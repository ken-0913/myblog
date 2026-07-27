---
title: "LLM 서빙 스터디 (1) Model Serving이란 무엇인가 — '학습'이 아니라 '배달'의 문제"
date: 2026-07-25T09:00:00+09:00
draft: false
tags: ["LLM", "Model Serving", "MLOps", "vLLM", "Inference"]
categories: ["프로그래밍"]
featuredImage: images/banners/llm-01-model-serving-introduction-a4a6addb.png
---

AI라고 하면 보통 **모델을 학습(training)** 시키는 이야기를 떠올린다.
하지만 학습이 끝난 모델을 실제 사용자에게 **빠르고 싸게 전달**하는 일은 완전히 다른 문제다.
이 과정을 **Model Serving(모델 서빙)** 이라 하며, 이 글은 서빙이 무엇이고 왜 중요한지 기초부터 정리한다.

## Model Serving을 한 문장으로

Model Serving은 **학습된 모델을 실제 환경에 올려, 새로운 입력에 대해 예측(prediction)을 내놓게 만드는 일**이다.

> "*model serving* refers to deploying an ML model in a production environment, where it can process new data and generate predictions."
> — *Hands-On LLM Serving*, Ch.1

여기서 "새 입력에 대해 답을 내는 것"을 **inference(추론)** 라고 부른다.
즉 서빙은 모델을 API·웹 서비스 형태로 만들어 **누구나 요청을 보내면 답을 받을 수 있게** 하는 작업이다.

비유하자면 서빙은 **공급망(supply chain)** 이다.
아무리 좋은 물건(모델)을 만들어도, 적절한 속도·비용·안정성으로 **배달**되지 않으면 가치가 없다.
Netflix의 추천, 은행의 실시간 이상거래 차단, 항공사 챗봇의 응답이 모두 서빙 시스템 위에서 돌아간다.

## 학습(Training)과 서빙(Serving)은 목표가 다르다

둘 다 "모델을 실행한다"는 점은 같지만, 목적이 정반대에 가깝다.

- **Training**: 정답을 맞히도록 **파라미터(weight)를 갱신**하는 과정. 오래 걸려도 되고, 대량의 데이터를 한 번에 처리한다.
- **Serving**: 이미 학습된 모델로 **빠르게 답만 낸다**. 파라미터 갱신이 없고, 요청 하나하나에 **낮은 지연(latency)** 이 중요하다.

그래서 학습용 도구(PyTorch, TensorFlow)를 그대로 서빙에 쓰면 비효율적이다.
서빙에는 **vLLM, NVIDIA Triton, SGLang** 같은 서빙 전용 프레임워크를 쓴다.

## 모델은 '데이터'가 아니라 '실행 프로그램'이다

많은 사람이 모델을 그냥 데이터 파일로 오해한다.
하지만 모델은 **실행 로직까지 포함한 프로그램**에 가깝다. 크게 세 부분으로 나뉜다.

- **Model data**: 학습으로 얻은 **weight와 bias**, 그리고 실행에 필요한 설정값(config).
- **Model architecture**: layer의 종류·개수·연결 방식 등 **모델의 구조**.
- **Model execution code**: 구조를 초기화하고 weight를 불러와 **실제로 예측을 돌리는 코드**.

이 셋이 합쳐져야 비로소 입력을 받아 출력을 내는 하나의 프로그램이 된다.

## 서빙은 어디서 이뤄지나 — 세 가지 위치

서빙은 요구사항에 따라 세 곳에서 일어난다.

- **On-device(기기 위)**: 스마트폰·로봇·카메라 등 사용자 기기에서 직접 실행. 네트워크 없이 즉시 동작하고, 데이터가 기기 밖으로 안 나가 **프라이버시**에 유리하다.
- **On-premises(사내 서버)**: 회사 자체 서버·클러스터에서 실행. 민감한 사내 데이터를 외부로 보내지 않아도 된다.
- **On-cloud(클라우드)**: AWS SageMaker, OpenAI 등 외부에 맡겨 실행. 하드웨어 관리 부담이 적고 빠르게 시작할 수 있다.

## 서빙에서 신경 쓰는 것들

서빙 엔지니어는 모델 내부 알고리즘보다 **운영 지표**에 집중한다.

- **Scalability(확장성)**: 요청이 수천에서 수백만으로 늘어도 감당할 수 있는가.
- **Latency(지연)**: 한 요청에 답하는 데 걸리는 시간. 실시간 서비스는 밀리초 단위가 중요하다.
- **Throughput(처리량)**: 단위 시간당 처리하는 예측 수.
- **Monitoring·Versioning·Security**: 성능 감시, 무중단 업데이트/롤백, 접근 통제.
- **Cost-to-serve(서빙 비용)**: 위 모든 것을 좌우하는 가장 결정적인 요소.

## 왜 직접 서빙을 이해해야 하나

"그냥 클라우드나 OpenAI를 쓰면 되지 않나?"라는 의문이 자연스럽다.
클라우드는 훌륭한 출발점이지만, 그것만으로 충분한 경우는 드물다.

- **비용**: 사용량이 커지면 관리형 서비스는 급격히 비싸진다. 오픈소스 LLM을 직접 서빙하면 크게 절감되는 경우가 많다.
- **데이터 보안**: 민감·기밀 데이터를 다루면 외부 전송 자체가 문제가 된다.
- **커스터마이징**: 직접 fine-tuning한 모델을 서빙하려면 자체 스택이 유리하거나 필수인 경우가 있다.

핵심은 **정답 아키텍처가 없다**는 점이다.
비즈니스 규모·보안 요건·기술 성숙도에 따라 외주와 자체 운영을 저울질해야 하고, 그러려면 서빙의 기본기를 알아야 한다.

## 최적화(Optimization) — 특히 LLM에서 필수

모델을 일단 띄우면 "끝난 것"처럼 보이지만, LLM은 그렇지 않다.
트래픽이 늘면 지연이 커지고, 처리량은 하드웨어 한계보다 훨씬 낮은 선에서 정체되며, 비용은 사용량에 비례해 치솟는다.

**Model Serving Optimization**은 지연을 줄이고 처리량을 늘리며 자원 사용을 효율화하는 작업이다.

> "*Model serving optimization* refers to the process of improving model serving performance, such as reducing serving latency, increasing throughput, and optimizing resource utilization."
> — *Hands-On LLM Serving*, Ch.1

LLM은 연산량이 워낙 커서, 최적화 없이는 운영 비용을 감당하기 어렵다.

실제로 vLLM 같은 서빙 프레임워크는 **PagedAttention·KV Cache** 같은 기법으로 기본 방식 대비 처리량을 수 배에서 수십 배까지 끌어올린다.
추가 하드웨어 없이 처리량을 몇 배로 높이는 것은, GPU가 비싼 현실에서 판을 뒤집는 차이다.

## 서빙 패러다임 — 규모에 따라 커지는 구조

서빙 구조는 요구가 커질수록 단계적으로 발전한다.

- **On-device serving**: 기기에서 직접. 저지연·오프라인·프라이버시가 강점이지만, 연산·전력·업데이트에 제약이 크다.
- **Single-model service**: 모델 하나(버전 하나)를 **독립된 웹 서비스**로 띄우는 가장 기본적이고 널리 쓰이는 방식. 격리성이 좋아 장애 전파가 없고 확장·디버깅이 쉽다.
- **Multi-model service**: 여러 모델을 **한 컨테이너에서 공유**하며, 요청이 올 때 올리고(load) 안 쓰면 내리는(unload) 방식. 모델이 아주 많을 때 비용 효율이 뛰어나다.
- **Model serving platform**: 위 방식들을 조합하고, 자원 그룹·워크플로 실행까지 관리하는 종합 플랫폼. 여러 모델이 협업하는 대규모 서비스에 쓴다.

각 방식은 지연·비용·확장성·복잡도 사이의 **트레이드오프**가 다르므로, 상황에 맞게 고른다.

## 정리

Model Serving은 학습이 아니라 **배달의 문제**다.
모델을 실제 사용자에게 낮은 지연·높은 처리량·감당 가능한 비용으로 전달하는 **시스템 엔지니어링** 영역이다.
다음 글에서는 그중에서도 까다로운 **LLM 서빙의 내부 동작**(token 생성, KV Cache, prefill·decode)을 코드와 함께 들여다본다.

## 출처

이 글은 *Hands-On LLM Serving* (O'Reilly) Chapter 1의 내용을 바탕으로 정리했다.
인용문은 원문을 그대로 옮긴 것이며, 나머지는 이해를 돕기 위해 재구성한 것이다.
