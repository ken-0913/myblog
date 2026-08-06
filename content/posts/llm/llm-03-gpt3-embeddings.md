---
title: "LLM 서빙 스터디 (3) GPT-3의 임베딩"
date: 2026-07-27T21:00:00+09:00
draft: false
tags: ["LLM", "GPT-3", "Embedding", "Transformer", "선형대수"]
categories: ["프로그래밍"]
math:
  enable: true
featuredImage: images/banners/llm-03-gpt3-embeddings-1d92e886.png
---
LLM은 글자를 직접 다루지 못한다. 오직 **숫자(벡터)** 만 계산할 수 있다.
그래서 첫 단계는 단어(정확히는 token)를 벡터로 바꾸는 것인데, 이를 **embedding(임베딩)** 이라 한다.
이 글은 GPT-3를 예로, 임베딩이 **행렬 연산**으로 어떻게 이뤄지는지 정리한다.

## token은 정수, 임베딩은 벡터

먼저 tokenizer가 문장을 **token** 단위로 쪼개고, 각 token에 **정수 ID**를 부여한다.
예를 들어 `"cat"` → `2543` 처럼, 모든 token은 사전(vocabulary)에서 번호 하나를 갖는다.

문제는 이 정수 자체엔 **의미가 없다**는 것이다. `2543`과 `2544`가 가깝다고 뜻이 비슷하지 않다.
그래서 각 token을 **여러 개의 실수로 이뤄진 벡터**로 바꾼다. 이 벡터가 임베딩이다.

GPT 계열이 쓰는 BPE tokenizer로 직접 확인하면 이렇다.

```python
import tiktoken

tokenizer = tiktoken.get_encoding("gpt2")
ids = tokenizer.encode("cat sat")
print(ids)                       # [9246, 3332]
print([tokenizer.decode([i]) for i in ids])   # ['cat', ' sat']
```

GPT-3의 임베딩 벡터는 길이가 \(d_{\text{model}} = 12288\) 이다.
즉 token 하나가 **12288개의 숫자**로 표현된다.

$$
\mathbf{e}_{\text{cat}} = \big[\, e_1,\; e_2,\; \dots,\; e_{12288} \,\big] \in \mathbb{R}^{12288}
$$

## 왜 벡터인가 — 의미가 거리로 표현된다

정수 ID로 못 하던 일을 벡터는 할 수 있다. **의미의 가까움을 거리로 담는 것**이다.
두 벡터가 얼마나 같은 방향을 보는지는 **cosine similarity(코사인 유사도)** 로 잰다.

$$
\cos(\mathbf{a}, \mathbf{b}) = \frac{\mathbf{a} \cdot \mathbf{b}}{\lVert \mathbf{a} \rVert \, \lVert \mathbf{b} \rVert}
$$

값이 1에 가까우면 방향이 거의 같고(의미가 비슷), 0이면 무관, -1이면 반대다.

```python
import torch
import torch.nn.functional as F

cat = torch.tensor([0.2, 0.9, 0.1])
dog = torch.tensor([0.3, 0.8, 0.2])
car = torch.tensor([0.9, 0.1, 0.4])

print(F.cosine_similarity(cat, dog, dim=0))   # tensor(0.9831) — 가깝다
print(F.cosine_similarity(cat, car, dim=0))   # tensor(0.3377) — 멀다
```

`cat`과 `dog`는 0.98로 붙어 있고, `cat`과 `car`는 0.34로 떨어져 있다.
정수 ID `2543`과 `2544`로는 절대 만들 수 없던 관계다.

아래에서 두 벡터의 끝점을 **드래그**해 보면, 방향이 일치할 때 cos가 1, 수직이면 0, 정반대면 -1이 되는 것을 직접 확인할 수 있다.

{{< cosine-demo >}}

### 이 벡터는 어디서 오나 — Word2Vec과의 차이

"비슷한 문맥에 등장하는 단어는 비슷한 의미를 갖는다."
**Word2Vec**은 이 전제로 단어와 문맥을 서로 예측하게 학습시켜 벡터를 얻는다. 즉 **미리 따로 학습해두고 가져다 쓴다**.

반면 **LLM은 임베딩을 입력층의 일부로 두고, 모델 전체와 함께 학습한다**.
별도 사전학습 대신 **해당 task와 데이터에 맞게 최적화된다**는 것이 이점이다.
아래에서 다룰 \(W_E\) 가 바로 그 "함께 학습되는" 표다.

## 실제로는 subword — BPE와 V = 50257

한 가지 짚고 갈 전제가 있다. GPT는 token을 **단어 단위로 쪼개지 않는다.**

단어 단위 사전은 학습에 없던 단어를 만나면 무너진다.
그래서 GPT-2·GPT-3는 **BPE(byte pair encoding)** 를 쓴다.
자주 함께 나오는 문자 조합을 반복 병합해 사전을 만들고, 모르는 단어는 **subword나 개별 문자로 쪼개** 처리한다.

```python
ids = tokenizer.encode("someunknownPlace")
print([tokenizer.decode([i]) for i in ids])
# ['some', 'unknown', 'Place'] — 모르는 단어도 쪼개서 처리한다
```

덕분에 `<|unk|>` 같은 대체 token 없이 **어떤 문자열이든** 표현할 수 있다.
이렇게 만들어진 GPT-2/GPT-3의 사전 크기가 바로 **\(V = 50257\)** 이다.

> 아래 예시는 이해를 위해 `나는 / 밥을 / 먹었다` 를 token 하나씩으로 다룬다.
> 실제 BPE라면 더 잘게 쪼개지지만, 행렬 연산의 구조는 동일하다.

## 임베딩 행렬

이 벡터들은 어디서 오는가? **임베딩 행렬(embedding matrix)** 이라는 거대한 표에서 꺼내온다.
사전의 각 token마다 벡터 하나씩을 행(row)으로 쌓아둔 것이다.

GPT-3의 사전 크기는 \(V = 50257\) 이므로, 임베딩 행렬 \(W_E\) 는 다음 크기의 행렬이다.

$$
W_E \in \mathbb{R}^{V \times d_{\text{model}}} = \mathbb{R}^{50257 \times 12288}
$$

이 표 하나가 담는 숫자만 \(50257 \times 12288 \approx 6.17 \times 10^{8}\), 약 **6억 개**다.
이 값들은 사람이 정하는 게 아니라, **학습을 통해 얻어지는 파라미터**다.

```python
V, d_model = 50257, 12288
embedding = torch.nn.Embedding(V, d_model)

print(embedding.weight.shape)      # torch.Size([50257, 12288])
print(embedding.weight.numel())    # 617558016  (약 6.2억)
print(embedding.weight.requires_grad)   # True — 학습되는 파라미터다
```

### 예시 — 6 × 3 으로 줄여 보기

실제 크기로는 눈에 안 들어오니, 이 글 내내 쓸 작은 예시를 정한다.
사전 크기 **\(V = 6\)**, 임베딩 차원 **\(d_{\text{model}} = 3\)** 이다.

문장 `"나는 밥을 먹었다"` 의 token에 ID를 붙이고, \(6 \times 3\) 짜리 \(W_E\) 를 둔다(값은 학습으로 얻어진 것이라 가정).

$$
W_E =
\begin{bmatrix}
0.2 & 0.9 & 0.1 \\
0.8 & 0.1 & 0.3 \\
0.4 & 0.3 & 0.9 \\
0.5 & 0.5 & 0.2 \\
0.1 & 0.7 & 0.6 \\
0.9 & 0.2 & 0.4
\end{bmatrix}
\begin{matrix}
\leftarrow \text{나는 (ID 0)} \\
\leftarrow \text{밥을 (ID 1)} \\
\leftarrow \text{먹었다 (ID 2)} \\
\\ \\ \\
\end{matrix}
$$

## 임베딩 조회 = one-hot 벡터 × 행렬

"token ID로 행렬의 해당 행을 꺼낸다"는 조회(lookup)를, 행렬 곱으로 정확히 표현할 수 있다.
핵심 도구는 **one-hot 벡터**다.

token ID가 \(i\) 일 때, one-hot 벡터 \(\mathbf{o}_i \in \mathbb{R}^{V}\) 는 **\(i\)번째 성분만 1, 나머지는 0** 인 벡터다.

$$
\mathbf{o}_i = \big[\,0,\; \dots,\; 0,\; \underbrace{1}_{i\text{번째}},\; 0,\; \dots,\; 0\,\big]
$$

이 one-hot 벡터를 임베딩 행렬에 곱하면, 정확히 \(i\)번째 행만 뽑혀 나온다.
`"나는"`(ID 0)으로 확인하면 이렇다.

$$
\mathbf{e}_{\text{나는}} = [\,1,0,0,0,0,0\,] \, W_E = [\,0.2,\; 0.9,\; 0.1\,]
$$

곱셈이 "행 하나 선택"이 되는 이유는, 0인 성분은 해당 행을 0으로 지우고 1인 성분만 그 행을 살리기 때문이다.
즉 **임베딩 조회는 곧 one-hot 벡터와 임베딩 행렬의 곱**이다.

```python
V, d = 6, 3
embedding = torch.nn.Embedding(V, d)
token_id = torch.tensor([0])

lookup = embedding(token_id)                       # 방식 1: 조회
onehot = F.one_hot(token_id, num_classes=V).float()
matmul = onehot @ embedding.weight                 # 방식 2: one-hot × 행렬

print(torch.allclose(lookup, matmul))   # True — 수학적으로 동치
```

### 단, 실제로는 one-hot을 만들지 않는다

여기서 오해하기 쉽다. one-hot은 **"조회가 왜 행렬 곱인가"를 설명하는 개념 도구**일 뿐이다.
실제 구현은 one-hot 행렬을 만들지 않고, **그냥 해당 행을 꺼낸다**.

이유는 크기를 보면 분명하다.
GPT-3 기준 one-hot 벡터 하나는 길이 50257인데, 그중 **99.998%가 0**이다.
token 하나를 고르려고 0을 5만 번 곱하는 셈이다.

`nn.Embedding`은 결과가 수학적으로 동일하면서 이 낭비를 없앤 **더 효율적인 구현**이다.
그래서 앞으로 나올 행렬 곱 수식은 **개념을 설명하는 표현**이지, 실제 연산 방식이 아니다.

## 문장 전체를 한 번에 — 행렬 대 행렬

실제로는 token 하나가 아니라 **문장(token 여러 개)** 을 한꺼번에 처리한다.
길이 \(n\) 인 token 시퀀스의 one-hot 벡터들을 세로로 쌓으면 행렬 \(O \in \mathbb{R}^{n \times V}\) 가 된다.

여기에 임베딩 행렬을 곱하면, 문장의 모든 token 임베딩이 한 번의 행렬 곱으로 나온다.

$$
X = O \, W_E \in \mathbb{R}^{n \times d_{\text{model}}}
$$

예시 문장 `"나는 밥을 먹었다"` 로 확인해 보자. token 3개이므로 \(n = 3\) 이다.

$$
\underbrace{
\begin{bmatrix}
1 & 0 & 0 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 & 0 & 0
\end{bmatrix}}_{O\;(3 \times 6)}
\;
W_E
\;=\;
\underbrace{
\begin{bmatrix}
0.2 & 0.9 & 0.1 \\
0.8 & 0.1 & 0.3 \\
0.4 & 0.3 & 0.9
\end{bmatrix}}_{X\;(3 \times 3)}
\begin{matrix}
\leftarrow \text{나는} \\
\leftarrow \text{밥을} \\
\leftarrow \text{먹었다}
\end{matrix}
$$

이제 \(X\) 의 각 행이 문장 속 token 하나의 임베딩이다.
행렬 크기가 \((n \times V) \cdot (V \times d) = (n \times d)\) 로 맞아떨어지는 것을 확인하면 감이 잡힌다.

실제로는 배치까지 함께 처리하므로 차원이 하나 더 붙는다.

```python
V, d = 50257, 256
embedding = torch.nn.Embedding(V, d)

# [batch=8, seq_len=4] 형태의 token ID 묶음
token_ids = torch.randint(0, V, (8, 4))

X = embedding(token_ids)
print(X.shape)      # torch.Size([8, 4, 256])  → [batch, seq_len, d_model]
```

즉 token ID 텐서 뒤에 \(d_{\text{model}}\) 축이 하나 추가되는 것이 임베딩 층의 전부다.

## 위치 정보 더하기 — positional embedding

여기엔 빠진 게 하나 있다. 지금까지의 \(X\) 는 **token의 순서**를 전혀 모른다.
같은 token ID는 문장 어디에 있든 **항상 같은 벡터**로 매핑되기 때문이다.
그래서 `"개가 사람을 물었다"` 와 `"사람이 개를 물었다"` 가 구분되지 않는다.

그래서 GPT-3는 **위치마다 다른 벡터**를 하나 더 준비한다.
위치용 행렬 \(W_P\) 는 문맥 최대 길이 \(n_{\text{ctx}} = 2048\) 에 대해 다음 크기다.

$$
W_P \in \mathbb{R}^{n_{\text{ctx}} \times d_{\text{model}}} = \mathbb{R}^{2048 \times 12288}
$$

문장 길이 \(n\) 에 맞춰 앞의 \(n\) 개 위치 벡터를 잘라 \(P \in \mathbb{R}^{n \times d}\) 를 만들고, **token 임베딩에 그냥 더한다**.

$$
H_0 = X + P
$$

예시로 이어가면, 각 위치(0, 1, 2번째)의 벡터 \(P\) 를 더해 \(H_0\) 가 완성된다.

$$
P =
\begin{bmatrix}
0.0 & 0.1 & 0.0 \\
0.1 & 0.0 & 0.1 \\
0.2 & 0.1 & 0.0
\end{bmatrix}
\quad\Rightarrow\quad
H_0 = X + P =
\begin{bmatrix}
0.2 & 1.0 & 0.1 \\
0.9 & 0.1 & 0.4 \\
0.6 & 0.4 & 0.9
\end{bmatrix}
$$

이 \(H_0\) 가 **Transformer 블록에 들어가는 첫 입력**이다.
즉 "무슨 단어인가(token embedding) + 몇 번째인가(positional embedding)"를 합친 벡터에서 모든 계산이 시작된다.
실제 GPT-3에서는 \(3 \times 12288\) 크기가 될 뿐, 흐름은 이 예시와 똑같다.

### absolute와 relative, 그리고 길이 제한

위치를 주입하는 방식은 두 갈래다.

- **absolute** — 위치마다 고유한 벡터를 둔다(0번째 자리, 1번째 자리, …).
- **relative** — token 사이의 **거리**를 표현한다("몇 칸 떨어져 있는가").

**GPT는 absolute를 쓰되, 고정값이 아니라 학습으로 최적화한다.**
원래 Transformer 논문의 고정된 사인파 방식과 다른 지점이다.

여기서 제약이 하나 따라온다. \(W_P\) 의 행이 2048개뿐이므로 **그보다 긴 입력은 위치 벡터가 없다.**
그래서 문맥 길이를 넘는 입력은 **잘라내야(truncate)** 한다.

### 전체를 코드로

지금까지의 예시를 그대로 코드로 옮기면 아래와 같다.
임베딩 값을 직접 지정했으므로 **출력이 위 손계산과 정확히 일치**한다.

```python
import torch

V, d = 6, 3

# 위에서 쓴 임베딩 행렬을 그대로 넣는다 (보통은 학습으로 얻어진다)
W_E = torch.tensor([
    [0.2, 0.9, 0.1],   # 나는 (0)
    [0.8, 0.1, 0.3],   # 밥을 (1)
    [0.4, 0.3, 0.9],   # 먹었다 (2)
    [0.5, 0.5, 0.2],
    [0.1, 0.7, 0.6],
    [0.9, 0.2, 0.4],
])
embedding = torch.nn.Embedding(V, d)
embedding.weight.data = W_E

# "나는 밥을 먹었다" → token ID → 임베딩 조회
token_ids = torch.tensor([0, 1, 2])
X = embedding(token_ids)
print(X)
# tensor([[0.2000, 0.9000, 0.1000],
#         [0.8000, 0.1000, 0.3000],
#         [0.4000, 0.3000, 0.9000]])

# 위치 임베딩을 더해 H0 완성
P = torch.tensor([
    [0.0, 0.1, 0.0],
    [0.1, 0.0, 0.1],
    [0.2, 0.1, 0.0],
])
H0 = X + P
print(H0)
# tensor([[0.2000, 1.0000, 0.1000],
#         [0.9000, 0.1000, 0.4000],
#         [0.6000, 0.4000, 0.9000]])
```

임베딩은 학습되는 파라미터이므로 실제 출력에는 `grad_fn=...` 이 함께 찍힌다(위에서는 생략했다).

참고로 이 예시의 \(W_E\) 는 설명을 위해 지어낸 값이라, 여기에 cosine similarity를 재도 **의미 있는 결과가 나오지 않는다**.
`cos(나는, 밥을) = 0.35` 같은 수치는 우연일 뿐이다.
의미가 담기는 것은 어디까지나 **실제 데이터로 학습된** 임베딩이다.

## GPT-3 숫자 요약

| 기호 | 의미 | GPT-3 값 |
| --- | --- | --- |
| \(V\) | 사전 크기(BPE token 종류 수) | 50257 |
| \(d_{\text{model}}\) | 임베딩 벡터 길이 | 12288 |
| \(n_{\text{ctx}}\) | 최대 문맥 길이 | 2048 |
| \(W_E\) | token 임베딩 행렬 | \(50257 \times 12288\) (약 6.2억) |
| \(W_P\) | 위치 임베딩 행렬 | \(2048 \times 12288\) (약 2500만) |

## 정리

- 정수 ID엔 의미가 없지만, **벡터는 의미의 가까움을 방향·거리로 표현**할 수 있다(cosine similarity).
- LLM의 임베딩은 Word2Vec처럼 따로 학습하지 않고, **모델과 함께 학습되는 입력층**이다.
- GPT는 BPE로 **subword**를 쪼개며, 그 결과 사전 크기가 \(V = 50257\) 이다.
- 조회는 개념적으로 행렬 곱이다: \(\mathbf{e}_i = \mathbf{o}_i^\top W_E\), 문장 전체는 \(X = O\,W_E\).
  다만 **실제 구현은 one-hot을 만들지 않고 해당 행을 바로 꺼낸다**.
- 여기에 **위치 임베딩을 더해** \(H_0 = X + P\) 를 만들면, 그게 Transformer의 첫 입력이다.
