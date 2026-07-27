---
title: "LLM 서빙 스터디 (2) LLM은 어떻게 답을 만드나 — token 생성, KV Cache, prefill·decode"
date: 2026-07-26T09:00:00+09:00
draft: false
tags: ["LLM", "Transformer", "KV Cache", "vLLM", "Inference"]
categories: ["프로그래밍"]
featuredImage: images/banners/llm-02-llm-serving-fundamentals-a28d8a4a.png
---

앞 글에서 Model Serving이 '배달의 문제'라는 것을 봤다.
이번에는 배달 대상 중 가장 까다로운 **LLM이 내부에서 어떻게 답을 만드는지**를 본다.
수학 없이 개념만으로, LLM 서빙의 핵심인 **token 생성·KV Cache·prefill/decode**를 정리한다.

## LLM은 한 번에 문장을 쓰지 않는다 — Autoregressive

LLM의 가장 중요한 특징은 **한 번에 token 하나씩** 만든다는 것이다.
여기서 **token**은 대략 단어 조각 하나라고 보면 된다(영어 기준 1 token ≈ 0.75 단어).
이렇게 **이전까지 만든 것을 보고 다음 하나를 예측**하는 방식을 **autoregressive(자기회귀)** 라 한다.

> "they generate text one token at a time, with each new token predicted based on all previously generated tokens."
> — *Hands-On LLM Serving*, Ch.2

예를 들어 "미국 수도를 소개해줘"라는 입력에 대해:

- 1단계: 입력을 받아 첫 token `Washington`을 생성한다.
- 2단계: `Washington`을 입력 뒤에 붙여 다시 넣고, 다음 token `D.C.`를 생성한다.
- 3단계: 이제 `Washington D.C.`까지 붙여 넣고 `is`를 생성한다.

이 과정을 **끝 신호(stop token)가 나오거나 최대 길이에 도달할 때까지** 반복한다.
즉 매 단계마다 지금까지의 결과 전체가 다시 입력이 된다.

## LLM 내부 구조 — 크게 세 덩어리

LLM(정확히는 decoder-only Transformer)은 세 부분으로 나눌 수 있다.

- **Tokenizer + Embedding**: 사람이 쓴 글을 token으로 쪼개고, 각 token을 **숫자 벡터(embedding)** 로 바꾼다. 모델은 글자가 아니라 숫자만 다룬다.
- **Transformer(decoder) blocks**: 실제 연산의 심장부. 이 블록이 여러 층(예: 24층) 쌓여, 문맥을 이해하고 다음 token 후보를 위한 표현을 만든다.
- **LM head**: 마지막 블록의 결과를 받아 **어휘 전체에 대한 확률**로 바꾸고, 가장 그럴듯한 token 하나를 고른다.

정리하면 **글 → 숫자(embedding) → 문맥 이해(blocks) → 다음 단어 확률(LM head) → token 선택**의 흐름이다.

## Transformer 블록 안 — Attention이 핵심

각 Transformer 블록은 두 부품으로 이뤄진다.

- **Self-attention layer**: 문장 안의 **다른 token들을 얼마나 참고할지** 정하는 부분. Transformer의 혁신이 바로 이것이다.
- **Feedforward network(FFN)**: attention이 모은 문맥을, 학습으로 익힌 지식과 결합해 **더 정교한 표현**으로 다듬는 부분.

**Attention**이 왜 필요한지는 예로 보면 쉽다.
"개가 다람쥐를 쫓았고, 그것이 나무 위로 올라갔다"에서 '그것'이 개인지 다람쥐인지는 **문맥**이 있어야 안다.
attention은 각 token이 앞의 어떤 token을 얼마나 봐야 하는지 **가중치**로 계산해, 이 모호함을 푼다.

서빙 관점에서 딱 하나만 기억하면 된다.
**attention은 연산이 무겁고, 입력이 길수록 비용이 급격히(제곱으로) 커진다.**
이 사실이 뒤에 나올 최적화의 출발점이다.

## 직접 돌려보면 보이는 문제 — 매번 다시 계산한다

token을 하나씩 만드는 과정을 직접 코드로 돌려보면, 흥미로운 현상이 보인다.
**뒤로 갈수록 token 하나 만드는 시간이 점점 늘어난다.**

이유는 단순하다.
새 token을 만들 때마다 그것을 입력 뒤에 붙여 **점점 길어진 전체 문장을 처음부터 다시 처리**하기 때문이다.
100번째 token을 만들 땐 앞의 99개에 대한 attention을 **매번 다시** 계산하는 셈이다.

여기서 자연스러운 질문이 나온다.
**이미 계산한 앞 token들의 결과를 저장해두고, 새 token만 계산하면 안 될까?**

## KV Cache — 이미 한 계산을 재사용한다

바로 그 아이디어가 **KV Cache**다.
attention 계산 과정에서 각 token은 **Key(K)와 Value(V)** 라는 중간 결과를 만드는데, 이걸 **저장(cache)해두고 재사용**한다.

> "this optimization stores the attention keys and values computed at each layer for previously generated tokens, allowing the model to skip redundant computations during decoding."
> — *Hands-On LLM Serving*, Ch.2

그러면 새 token을 만들 때 앞 token들의 K·V를 다시 계산할 필요 없이, **새로 추가된 token 하나만** 처리하면 된다.
**메모리를 조금 더 쓰는 대신 연산을 크게 아끼는** 맞바꿈이다.

효과는 극적이다.
캐시가 없으면 token 생성 시간이 계속 늘지만, KV Cache를 켜면 첫 token 이후로는 **시간이 거의 일정하게** 유지된다.
같은 100 token 생성이 캐시 하나로 몇 배 빨라진다.

```python
# 핵심만: 직전 스텝의 KV 캐시를 넘겨주고(use_cache=True),
# 새로 생성된 token 하나만 다음 입력으로 사용한다
outputs = model(input_ids=new_token, past_key_values=kv_cache, use_cache=True)
kv_cache = outputs.past_key_values   # 캐시 갱신
```

## Prefill과 Decode — 성격이 다른 두 단계

KV Cache를 이해하면, LLM 실행이 **두 단계**로 나뉜다는 게 보인다.

- **Prefill(프리필)**: 사용자가 넣은 **입력 프롬프트 전체를 한 번에** 처리하는 단계. 모든 token을 병렬로 계산하지만, 양이 많아 **연산 집약적(compute-intensive)** 이다. 첫 token이 나오기까지의 시간이 여기서 결정된다.
- **Decode(디코드)**: 그 뒤로 **token을 하나씩** 만들어내는 단계. 캐시 덕분에 스텝마다 가볍지만, 자주 반복되고 KV Cache가 계속 커져 **메모리 집약적(memory-intensive)** 이다.

> "The prefill phase is compute-intensive ...; the decoding phase is memory-intensive, primarily due to the frequent loading of model weights and the growing size of the KV cache."
> — *Hands-On LLM Serving*, Ch.2

이 구분이 실무에서 중요한 이유는 **병목 지점이 상황마다 다르기** 때문이다.

- 500쪽 PDF처럼 **입력이 매우 긴** 경우 → prefill이 비싸다.
- 짧게 묻고 길게 답하는 **챗봇·글쓰기** → decode가 병목이다.

어느 단계가 무거운지 알아야 올바른 최적화를 고를 수 있다.

## 서빙 프레임워크를 쓰는 이유 — vLLM

지금까지는 모델을 직접 불러와 token을 하나씩 만드는 방식이었다.
이해에는 좋지만 실제 서비스에는 **서빙 프레임워크**를 쓴다. 대표적으로 **vLLM**이다.

vLLM 같은 프레임워크는 단순 실행을 넘어 다음을 기본 제공한다.

- KV Cache 재사용을 통한 **효율적 디코딩**
- 요청 스케줄링과 **batching**
- **여러 사용자 동시 처리**
- token **streaming**과 요청 취소 처리

성능 차이도 크다.
같은 프롬프트·모델에서 vLLM이 Hugging Face 기본 방식보다 **10~20배 빠른** 처리량을 내는 벤치마크가 흔하다.

```python
from vllm import LLM, SamplingParams

llm = LLM(model="Qwen/Qwen2.5-0.5B", dtype="float16")
params = SamplingParams(temperature=0.8, top_p=0.95, max_tokens=128)
outputs = llm.generate(["미국 수도를 소개해줘"], params)
```

실무 팁은 **"간단하게 시작하고, 나중에 최적화하라"** 이다.
프로토타입은 Hugging Face로 빠르게 만들고, 운영 단계에서 vLLM으로 옮겨 지연·처리량·동시성을 튜닝한다.

## Streaming — 답을 기다리지 않고 흘려보낸다

기본 `generate()`는 **모든 token을 다 만든 뒤에야** 결과를 돌려준다.
챗봇이라면 사용자가 몇 초에서 수십 초를 **빈 화면으로 기다린다**는 뜻이다.

**Streaming(스트리밍)** 은 token이 만들어지는 대로 **즉시 조금씩 내보내는** 방식이다.
ChatGPT에서 글자가 좌르륵 흘러나오는 그 경험이 바로 이것이다.
vLLM에서는 `AsyncLLMEngine`을 써서 생성되는 token을 하나씩 받아 전달한다.

덤으로, 답이 엉뚱하게 흘러가면 **중간에 취소**할 수도 있어 사용자 경험과 비용 모두에 이롭다.

## Batching — 여러 요청을 한 번에 처리한다

프롬프트를 하나씩 처리하면 문서 10만 건 요약이나 동시 접속 2만 명 같은 상황을 감당할 수 없다.
**Batching(배칭)** 은 여러 입력을 **묶어서 한 번에** 모델에 통과시키는 기법이다.

Transformer 연산(행렬 곱, attention)은 병렬화가 잘 되고, GPU는 병렬 계산에 강하다.
그래서 여러 요청을 함께 처리해도 오버헤드가 작아 **처리량이 크게 오른다**.
간단한 실험에서도 4개를 묶으면 하나씩 처리할 때보다 약 2배 빨라진다.

더 나아가 **continuous batching**(끝난 요청 자리에 새 요청을 즉시 채우는 방식)은 처리량을 수십 배까지 끌어올린다.

## 정리

LLM은 **token을 하나씩 만드는 autoregressive 모델**이고, 그 심장은 **attention**이다.
attention이 무겁다는 사실에서 **KV Cache**(재계산 제거)와 **prefill/decode 구분**(병목 파악)이 나온다.
그리고 실제 서비스에서는 **vLLM 같은 프레임워크 + streaming + batching**으로 지연을 낮추고 처리량을 높인다.
이 개념들이 이후 최적화 기법 전부의 토대가 된다.

## 출처

이 글은 *Hands-On LLM Serving* (O'Reilly) Chapter 2의 내용을 바탕으로 정리했다.
인용문은 원문을 그대로 옮긴 것이며, 나머지는 이해를 돕기 위해 재구성한 것이다.
