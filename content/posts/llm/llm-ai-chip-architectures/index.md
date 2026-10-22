---
title: "AI 칩 아키텍처 6종 비교 - GPU, TPU, WSE, Trainium, LPU는 무엇에 베팅했나"
date: 2026-09-11T11:00:00+09:00
draft: true
tags: ["AI", "GPU", "TPU", "Trainium", "Cerebras", "Groq", "NVIDIA", "AMD", "Hardware"]
categories: ["LLM"]
featuredImage: images/banners/llm-ai-chip-architectures-f632a60f.png
---

2018년 Hennessy와 Patterson은 Turing Lecture에서 "컴퓨터 아키텍처의 새로운 황금기"를 선언했다. 1980년대 연 52%씩 자라던 단일 스레드 CPU 성능이 2018년에는 3%로 떨어졌고, 그 자리를 **domain-specific architecture(DSA)**가 메울 것이라는 예측이었다. 강연의 예시는 이미 양산 중이던 Google TPU v1이었다. 추론에서 CPU 대비 처리량 29배, 전력 효율 80배.

예측은 맞았다. 지금은 GPU, TPU, LPU, NPU, wafer-scale engine, reconfigurable dataflow, neuromorphic, photonic까지 수십 가지 아키텍처가 경쟁한다. 이 글은 그중 **실제 배포에서 자리를 잡은 6종**을 같은 틀로 비교한다.

> 이 글은 [AI Chip Architectures](https://www.google.com/search?q=AI+Chip+Architectures+blog) 원문을 읽고 정리한 것이다. 수치와 사실 관계는 원문을 따랐고, 비교 축과 구성은 새로 짰다. 원문의 Groq 절은 확보한 범위에서 끊겨 있어 해당 부분은 다른 칩보다 얕다.


&nbsp;

## 문제: 메모리 월

AI 연산은 행렬 곱이 지배한다. Transformer는 Q/K/V projection → attention → output projection → FFN으로 이어지는 matmul의 연속이고, 그 사이에 normalization·activation·residual 같은 element-wise 연산이 끼어든다. 프런티어 모델 학습 한 번에 약 10²⁵회의 multiply-accumulate가 돈다.

**중요한 것은 그 matmul의 모양이 워크로드마다 다르다는 점이다.**

| 단계 | 연산 모양 | 성격 |
| --- | --- | --- |
| Training | GEMM (행렬×행렬) | 수천 토큰이 같은 weight를 통과. arithmetic intensity 높음 → **compute-bound** |
| Prefill | GEMM | 프롬프트 전체를 한 번에 투사. 역시 compute-bound |
| Decode | GEMV (행렬×벡터) | 토큰 하나씩 자기회귀. 토큰 하나에 **전체 weight를 한 번 읽고** KV cache도 전부 읽음 → **memory-bound** |

추론 시스템은 배칭으로 GEMV를 다시 GEMM으로 승격시켜 intensity를 회복한다. continuous batching은 여러 사용자의 decode step을 쌓고, speculative decoding은 K개 초안 토큰을 한 번에 검증하며, multi-token prediction은 같은 수법을 모델 안으로 접어 넣는다.

다만 continuous batching에서도 **각 요청은 자기 KV cache를 따로 읽는다.** 그래서 long-context decode는 weight-bandwidth-bound에서 KV-bandwidth-bound로 성격이 바뀐다.

결국 아키텍처 문제는 하나로 수렴한다. **연산 유닛이 있는 곳까지 숫자를 충분히 빨리 나르는 것.** 연산은 지수적으로 늘었지만 메모리 대역폭은 그러지 못했고, 이 격차가 memory wall이다.

칩을 이해하는 일은 네 가지 질문으로 환원된다.

1. 데이터는 어디에 사는가
2. 연산 유닛까지 어떻게 옮기는가
3. 연산 유닛은 어떻게 생겼는가
4. 칩끼리는 어떻게 대화하는가


&nbsp;

## 한눈에 보는 6종

| | 철학 | 연산 유닛 | 온칩 메모리 | 스케줄링 | Scale-up |
| --- | --- | --- | --- | --- | --- |
| **NVIDIA GPU** | 프로그래머블 범용 병렬 | Tensor Core (warp 계층 안) | 캐시 + 스크래치패드 혼합 | 하드웨어 warp scheduler | NVLink/NVSwitch **코히런트** |
| **Google TPU** | matmul 전용기 | 256×256 systolic array | **캐시 없음**, 전부 스크래치패드 | **컴파일러(XLA)** | ICI **torus**, 메시지 패싱 |
| **AMD GPU** | 패키지에 재투자 | Matrix Core (wavefront 고정) | + 256MB Infinity Cache | 하드웨어 | Infinity Fabric → UALink |
| **Cerebras WSE** | 웨이퍼를 자르지 않음 | **matrix 유닛 없음**, 90만 dataflow core | **SRAM 44GB가 전부** | 데이터 도착이 트리거 | 리소그래피가 곧 도메인 |
| **AWS Trainium** | TPU 플레이북 차용 | 128×128 systolic array | 스크래치패드 (SBUF/PSUM) | 컴파일러(OpenXLA) | NeuronLink torus → switch |
| **Groq LPU** | **결정론** | functional slice 분해 | SRAM only | 컴파일러가 사이클 단위 배치 | 네트워크까지 스케줄 |

세로로 읽으면 공통 축이 보인다. **하드웨어가 런타임에 판단할 것인가, 컴파일러가 미리 정할 것인가.** NVIDIA와 AMD는 전자, TPU·Trainium·Groq는 후자, Cerebras는 제3의 답이다.


&nbsp;

## NVIDIA GPU — 프로그래머빌리티에 건다

철학은 일관된다. **워크로드는 움직이는 표적**이므로 모든 블록을 프로그래머블하게 두고 CUDA로 노출한다. 특수 유닛조차 고정 기능 블록이 아니라 같은 프로그래밍 모델 안에서 드러난다. 같은 칩이 transformer를 학습하고, 추론을 서빙하고, 그래픽을 렌더링하고, 과학 시뮬레이션을 돌린다.

### matmul이 warp에서 빠져나온 과정

가장 흥미로운 변화는 **행렬 명령이 스레드 계층에서 점점 분리돼 온 궤적**이다.

| 세대 | 명령 | 발행 주체 | 성격 |
| --- | --- | --- | --- |
| Volta | `mma.sync` | warp 32 스레드 | 동기. 완료까지 warp가 블록 |
| Hopper | `wgmma.mma_async` | warp-group 128 스레드 | 비동기. B는 shared memory descriptor |
| Blackwell | `tcgen05.mma` | **스레드 1개** | A·B 모두 descriptor, 누산기는 TMEM |

Blackwell에 오면 모든 피연산자가 레인 밖으로 나가서 조율할 per-thread 상태가 없다. **스레드 하나가 명령을 쏘고 즉시 반환**하며, 완료는 mbarrier로 알린다. 나머지 warp는 그동안 다른 일을 한다.

이 디커플링이 attention 커널의 효율을 만든다. matmul이 도는 동안 warp는 softmax를 돌리거나 마스크를 적용하거나 다음 타일을 미리 당겨올 수 있다. **FlashAttention-3/4의 구조가 통째로 이 성질에 의존한다.**

### 메모리도 같은 방향으로 갔다

타일을 나르는 일에서 warp를 빼내는 작업이 세대마다 반복됐다.

- **Ampere 이전** — 스레드마다 global load를 발행하고 warp가 대기. 주소 계산에 레인을 소모
- **Ampere `cp.async`** — 레지스터를 우회해 HBM→SMEM 비동기 복사
- **Hopper TMA** — 전용 DMA 엔진. 스레드 하나가 타일 descriptor를 제출하면 엔진이 주소 계산을 다 하고 mbarrier로 완료 통지
- **Blackwell** — TMA가 TMEM으로 직접 적재

여기서 나온 관용구가 **warp specialisation**이다. 블록 안에서 일부 warp는 TMA load를 연달아 쏘는 producer, 나머지는 도착한 타일에 wgmma를 쏘는 consumer가 된다. 동기화는 블록 단위 `__syncthreads()`가 아니라 warp 단위 mbarrier 핸드셰이크다.

### 다섯 가지 베팅

1. **프로그래머빌리티** — 워크로드가 변하니 개발자가 CUDA를 쓰게 둔다
2. **대규모 멀티스레딩으로 지연 은닉** — 정적 스케줄이 아니라 SM당 최대 64 warp 오버커밋으로 가린다
3. **warp로 감싼 matmul** — 행렬 유닛이 연산의 대부분이지만 고정 파이프가 아니라 warp 추상화 뒤에 둔다. 그래야 한 커널에서 matmul·softmax·element-wise를 융합한다
4. **비동기 메모리 계층** — 암묵적 캐시가 아니라 명시적 스크래치패드 + TMA/TMEM/mbarrier
5. **SIMT 세금 상각** — warp scheduler·레지스터 파일에 쓰는 트랜지스터는 MAC에 못 쓰는 트랜지스터다. 세금을 인정하되 Tensor Core를 키워 상각한다

### 스케일

**scale-up은 코히런트**다. NVLink가 GPU 간 캐시 코히런트 패브릭을 만들어 한 GPU의 load/store가 다른 GPU의 HBM을 직접 겨냥한다. NVSwitch 크로스바가 붙어 전 GPU가 동시에 full bandwidth로 통신한다.

NVL72는 72 GPU, 36 Grace CPU, HBM 13.5TB를 **하나의 평평한 주소 공간**으로 묶는다. 이 밀도를 지탱하는 것이 수동 구리다 — 5,184가닥이 backplane에 blind-mate로 물려 약 130 TB/s를 나르고, 광 대비 랙당 약 20kW를 아낀다.

랙 경계에서 구리가 유리로 바뀐다. 2m 남짓이 패시브 구리의 한계라 랙을 넘으면 광 트랜시버가 붙고, Rubin 세대에서는 그 광학층이 스위치 ASIC 안으로 들어간다(co-packaged optics).

### 해자는 CUDA가 아니다

CUDA 추상화는 18년째 거의 그대로다. 2007년 이후 쓰인 모든 CUDA 커널이 Blackwell에서 컴파일된다. **이 연속성이 해자이자 제약이다.** 너무 많은 코드가 의존하고 있어 SM을 근본적으로 갈아엎을 수 없고, 대신 CUDA에 대한 모든 투자가 세대를 넘어 복리로 쌓인다.

원문이 짚는 핵심은 이것이다. **해자는 CUDA 자체가 아니라 NVIDIA가 급여를 주지 않는 사람들이 20년간 쌓은 서드파티 커널·라이브러리·툴링, 그리고 그 API를 배운 수백만 개발자다.** 여기에 NVIDIA는 자사 엔지니어 수십 명을 프런티어 랩 안에 상주시킨다. 이탈 비용은 커널 재작성이 아니라 엔지니어링 조직 전체의 사고방식을 다시 훈련시키는 일이 된다.


&nbsp;

## Google TPU — 컴파일러가 곧 시스템

정반대 철학이다. 아무 병렬 워크로드나 돌리는 프로그래머블 칩이 아니라, **단일 primitive(대형 systolic array 위의 dense matmul)에 집중하고 XLA 컴파일러가 모든 사이클과 모든 바이트를 미리 계획한다.** 하드웨어 스케줄러도, 캐시도, 스레드/warp도 없다.

### systolic array와 weight-stationary

MXU는 256×256 systolic array다(세대별 128×128 ↔ 256×256 변동). `C = A × B`를 계산할 때 **B의 값을 셀마다 하나씩 미리 적재**하고(weight-stationary), activation이 왼쪽 모서리로 들어와 매 사이클 한 칼럼씩 전파하며 각 셀의 상주 weight와 곱해진다. 부분합은 아래로 흘러 누산 큐에 쌓인다.

**배열에 데이터가 들어간 뒤로는 메모리 접근이 없다.** weight는 지나가는 모든 activation에 재사용되고, activation은 행을 따라 128(또는 256)번 재사용된다. 데이터 재사용이 캐시의 중재가 아니라 **실리콘 배선에 새겨져 있다.**

연산의 지배적 비용은 곱셈 자체(수 피코줄)가 아니라 메모리 읽고 쓰기(100~1000배)인데, systolic array는 그 비용을 구조적으로 삭제한다. 대가는 **underfill**이다. 256×256 배열에서 128×128 matmul을 돌리면 실리콘의 75%가 논다. 그래서 XLA가 차원을 128(또는 256)의 배수로 타일링·패딩하고, 모델 코드도 그 양자를 의식하고 쓰인다.

### VLIW와 2D 벡터 머신

VPU는 조연처럼 보이지만 미세구조상 더 흥미롭다. **모든 TPU는 1D SIMD가 아니라 2D 벡터 머신이다.** 레지스터가 (8, 128) 같은 2D VREG 모양을 갖는다. lane 축이 systolic array 입력 폭과 맞고, sublane 축이 MXU로 타일을 스트리밍하게 해준다.

현대 TPU 프로그램 성능의 대부분은 **VPU/MXU 오버랩**에서 나온다. quantisation·layernorm·softmax·activation·bias-add가 MXU가 matmul을 도는 바로 그 사이클에 VPU에서 돈다.

전체를 지휘하는 것은 Scalar Unit이다. 가장 작지만 **명령 인출을 하는 유일한 블록**으로, 매 사이클 322비트 VLIW 번들을 당겨 자기 슬롯 2개를 실행하고 나머지 6개를 칩 전체에 분배한다. 블록 간 동기화는 명시적이다 — 하드웨어가 의존성을 추적하지 않고 컴파일러가 배리어 검사를 삽입한다.

### 캐시가 없다는 것의 의미

온칩 계층도 같은 발상이다. **캐시가 하나도 없고 모든 계층이 소프트웨어 관리다.** VMEM(벡터 스크래치패드), CMEM(HBM과 VMEM 사이 완충), SMEM(제어 상태)이 있고, 프로그램의 모든 텐서는 컴파일 시점에 어느 계층에 살지 확정된다.

**하드웨어는 prefetch도, eviction도, coherence도 하지 않는다.** 컴파일러가 맞히면 배열은 절대 멈추지 않고, 틀리면 폴백 경로가 없다.

### 다섯 가지 베팅

1. **systolic array** — matmul이 지배하니 실리콘을 거기 쓴다
2. **소프트웨어 스크래치패드** — 연산은 싸고 메모리는 비싸니 배선으로 재사용하고 캐시를 없앤다
3. **컴파일러 스케줄링** — 워크로드가 정적으로 예측 가능하니 스케줄링을 컴파일러로 옮긴다
4. **MAC만 남긴 실리콘** — 곱셈-누산을 하지 않는 트랜지스터는 전부 지운다(캐시 태그, 분기 예측기, reorder buffer)
5. **배열 밖 전용 엔진** — 배열이 잘못된 모양인 워크로드(embedding, collective)는 옆에 작은 전용 블록(SparseCore, CAE)을 판다

### torus와 광 회로 스위치

scale-up 이야기도 NVIDIA의 역이다. **ICI는 메시지 패싱**이라 remote-load 의미론도, 캐시 코히런스도, 크로스바도 없다. 모든 멀티칩 연산은 XLA가 컴파일한 명시적 collective다. 칩을 이웃과 직접 배선한 **torus**로 묶고 랙 경계는 광 회로 스위치로 꿰맨다.

NVIDIA에 대응물이 없는 부품이 **Palomar OCS**다. 3D-MEMS 광 회로 스위치로, 미세 거울이 물리적으로 회전해 임의의 입력 광섬유를 임의의 출력에 매핑한다. 재구성은 밀리초급이지만 회로 교환이라 상관없다 — **작업 시작 시 토폴로지를 고르고 일주일 돌린 뒤 다음 워크로드에 맞춰 재구성**한다.

이 하나로 세 문제가 동시에 풀린다. 워크로드별 토폴로지 재구성, 필요 시 sub-pod 분할, 그리고 장애 허용(칩이 죽으면 예비 큐브를 광학적으로 갈아 끼우고 작업이 계속된다).

superpod가 scale-up의 단위이고 NVL72와 같은 역할이되 **두 자릿수 더 크다.** Ironwood는 9,216칩을 하나의 코히런트 ICI 도메인으로 제시한다.

MoE 추론용 v8i가 torus를 버리고 계층적 high-radix 토폴로지로 간 것은 시사적이다. **3D torus는 collective가 최근접 이웃일 때 뛰어나지만 MoE expert routing은 정반대인 all-to-all**이고, 지연은 최장 홉 쌍에 좌우된다. 1,024칩 3D torus의 지름 16홉이 새 토폴로지에서는 7홉이 된다.

### 소프트웨어

GPU에서는 개발자가 커널을 쓰고 프레임워크가 커널을 엮으며 컴파일러의 역할은 대체로 국소적이다. TPU에서는 개발자가 JAX로 수치 프로그램을 쓰고 **그 아래 전부를 XLA가 책임진다** — 어떤 연산을 융합할지, 각 텐서가 어디 살지, 2D 벡터 레지스터에 어떻게 배치할지, DMA를 언제 발행할지, VLIW 번들을 어떻게 채울지, 수천 칩에 어떻게 샤딩할지.

**하드웨어 폴백이 없다.** 나쁜 스케줄을 덮어줄 warp scheduler도, 캐시도, out-of-order 엔진도 없다. 컴파일러가 곧 시스템이다.

탈출구는 **Pallas**다. GPU의 Triton에 해당하는 JAX의 커널 작성 언어로, XLA가 새로운 attention 변종이나 fused MoE dispatch의 최적해를 늘 합성해내지는 못하기 때문에 존재한다. **승부가 대수(algebra)가 아니라 스케줄에 있는 FlashAttention급 최적화**가 그 영역이다.

CUDA 생태계가 산발적이라면 TPU 생태계는 중앙집중적이다. XLA, JAX, Flax, Optax, Pallas, MaxText, Pathways가 전부 Google이 직접 오픈소스로 내고 실리콘과 보조를 맞춰 진화한다. **워크로드가 이상하게 생겼을 때 해자는 얕고, Gemini처럼 생겼을 때 깊다.**


&nbsp;

## AMD GPU — 코어는 보수적으로, 패키지에 재투자

NVIDIA와 다른 곳에 건다. NVIDIA가 세대마다 SM이 할 수 있는 일을 넓혀 온 반면 **AMD는 2012년 GCN 이래 Compute Unit을 보수적으로 유지하고 패키지에 재투자**했다.

행렬 명령의 궤적이 이를 압축해서 보여준다. NVIDIA의 Tensor Core가 스레드 계층을 타고 올라간 반면(warp → warp-group → 스레드 1개), **AMD의 Matrix Core는 제자리에 있다.** MI100(2020)부터 MI355X(2025)까지 모든 MFMA가 wavefront 스코프다. 명령은 빨라지고 포맷은 넓어졌지만 발행 주체와 스코프는 그대로다.

### Infinity Cache

메모리 계층은 NVIDIA보다 범용 계층이 적은 대신, **NVIDIA에 아예 없는 거대한 캐시가 하나 있다.** MI300X 기준 256MB의 Infinity Cache로, 측정 약 12 TB/s는 같은 칩의 HBM3 대역폭 5.3 TB/s의 두 배가 넘는다.

원래 좁은 GDDR 버스를 보상하려고 RDNA 게이밍 GPU에서 나온 IP인데, **attention의 KV 재사용과 weight 재사용이 대형 LLC에 유난히 잘 맞아** AI로 재활용됐다. NVIDIA는 더 큰 HBM 대역폭에, AMD는 캐시에 걸었다.

HBM 용량도 2021년 이후 매 세대 동시대 NVIDIA 플래그십과 같거나 넘는다. **추론이 점점 capacity-bound가 되고 있고 메모리가 더 많은 칩이 이긴다**는 베팅이다.

### 3D 스태킹을 먼저 했다

패키징이 AMD가 NVIDIA와 달라지는 지점이다. CDNA 3은 8개의 XCD를 TSMC SoIC 하이브리드 본딩으로 4개 I/O die 위에 **3D 적층**했다. NVIDIA는 H100까지 모놀리식이었고 B200에서야 2.5D CoWoS-L로 2개 다이를 붙였다. **AMD가 한 세대 먼저, 더 작은 다이 면적으로 갔다.**

MI300A APU는 여기서 더 밀어붙인다. XCD 8개 중 2개를 Zen 4 CCD 3개로 교체해 **CPU와 GPU가 HBM3 위 하나의 물리 주소 공간을 하드웨어 코히런스로 공유**한다. host-device 복사도, pinned memory도, 경로상의 PCIe도 없다. NVIDIA의 Grace-Hopper가 두 패키지를 NVLink-C2C로 잇는다면 MI300A는 하나다.

### 열려 있다는 것

AMD의 축은 **개방성**이다. CDNA 4의 FP4/FP6는 OCP MX 블록 스케일을 쓰는데, Blackwell의 MXFP4·TPU v8의 MXU와 같은 수치 포맷이되 **단일 벤더가 아니라 컨소시엄이 규정**한 것이다. scale-up은 UALink, scale-out은 Ultra Ethernet(UEC)으로 간다. 같은 수법이다 — **구현이 아니라 표준을 소유한다.**

대가는 수직 통합의 부재다. NVIDIA가 InfiniBand·Ethernet·NIC·DPU·CPO를 전부 자체 보유한 반면, AMD는 NIC/DPU 한 계층만 갖고 스위치 ASIC과 광학은 파트너 실리콘(Broadcom)이다.

### 소프트웨어 격차는 실재한다

ROCm은 CUDA의 오픈소스 대척점이다. HIP가 CUDA 호환 C++ 런타임이고 `hipify`가 소스를 자동 변환한다. **벌크 HPC 코드는 80~95%가 그대로 포팅되지만 현대 AI 커널은 훨씬 나쁘다** — TMA descriptor, `wgmma`, `tcgen05.mma` 같은 Hopper/Blackwell 전용 primitive에 손을 뻗는 코드는 깔끔한 ROCm 대응물이 없어 손으로 다시 써야 한다.

FlashAttention이 그 시금석이다. FA2는 MI300X에서 프로덕션이고, FA3는 부분 지원, **FA4(2026년 3월, Blackwell)는 ROCm 포팅이 아예 없다.** 원문의 관찰이 날카롭다 — 오픈소스 학술 커널이 AMD의 꼬리를 메우지만 그 시차는 **몇 년이 아니라 몇 달**이다.

독립 벤치마크는 ROCm 7.2가 동등 실리콘·동등 정밀도에서 CUDA 대비 10~25% 느리다고 본다. **기능 패리티에는 도달했지만 성능 패리티에는 아니다.**


&nbsp;

## Cerebras WSE — 웨이퍼를 자르지 않는다

가장 극단적인 답이다. 철학이 도발적이다. **메모리 월은 웨이퍼를 잘랐기 때문에 생긴 결과다.**

팹은 300mm 실리콘에 수십 개 다이를 찍고 톱으로 잘라낸다. 그러고 나면 업계가 가장 이국적인 엔지니어링(HBM, NVLink, CoWoS, 랙당 구리 5,184가닥)을 총동원해 **온다이 대역폭의 아주 일부로** 조각들을 도로 잇는다. Cerebras는 톱질을 건너뛴다.

### 수율 문제를 입도로 푼다

스테퍼는 한 번에 약 850mm²를 노광하고, 이것이 모든 칩의 천장이다(B200이 2다이가 된 이유). Cerebras는 같은 약 550mm² 다이를 12×7 격자로 84번 찍고, **원래 톱이 지나갈 1mm 미만의 scribe line 위에 상위 금속층을 얹는다.** 소프트웨어에 이음매는 존재하지 않는다.

웨이퍼 스케일은 1980년대에 이미 수율로 실패한 아이디어다. **Cerebras의 답은 입도다.** H100에서 결함 하나는 약 6mm²짜리 SM 전체를 죽이지만, WSE에서 같은 결함은 0.05mm² 코어 하나를 죽인다. 약 97만 코어를 만들어 90만 개를 출하하고, 약 7%의 예비 풀과 여분 패브릭 링크로 결함을 우회해 온전한 논리 메시를 복원한다.

### 행렬 유닛이 없다

다른 모든 칩이 FLOPs를 전용 matmul 엔진에 집중시키고 **그 엔진을 어떻게 먹이느냐로 갈리는 반면, Cerebras는 matmul을 패브릭으로 조립한다.**

GEMM은 웨이퍼 전체의 안무로 돈다. 도착한 weight를 activation을 쥔 코어들의 행을 따라 브로드캐스트하고, 각 코어가 자기 조각에 대해 곱셈-누산을 쏘고, 부분합이 메시를 가로질러 리듀스된다. **Tensor Core가 레지스터 타일에서, MXU가 배선에서 얻는 재사용을 WSE는 기하학에서 얻는다** — activation이 움직이지 않으니 이동하는 피연산자는 지금 곱해지는 것 하나뿐이다.

### 메모리 계층이 한 단이다

**SRAM 44GB가 코어 안에 48kB씩 나뉘어 있고 그 외에는 아무것도 없다.** HBM도, L2도, eviction 정책도 없다. 모든 바이트가 FMAC에서 한 사이클 거리다.

인용되는 21 PB/s는 90만 개 로컬 SRAM 포트의 합이지 point-to-point 링크가 아니므로 HBM 수치와 직접 비교할 수 없다. **정직한 비교 축은 FLOP당 바이트다.**

| | dense FP16 FLOP당 바이트 |
| --- | --- |
| Cerebras WSE | ~1.3 |
| NVIDIA B200 (HBM) | ~0.002 |

이 축에서 모든 GPU와 TPU는 굶고 있고 **WSE만 균형이 맞는다.** 토큰마다 weight를 전부 한 번 읽어야 하는 decode가 바로 웨이퍼가 맞게 생긴 국면이다.

반대편에는 절벽이 있다. 웨이퍼의 외부 연결은 12×100 GbE, 즉 1.2 Tb/s로 **Blackwell GPU 한 장에 붙는 ConnectX-8 하나보다 조금 큰 수준**이다. 온웨이퍼 SRAM과 오프웨이퍼 이더넷 사이에 다섯 자릿수의 격차가 있다. NVIDIA의 계층이 완만히 내려간다면 **WSE는 두 단 사이에 절벽이 있다.**

게다가 섬은 자라지 않는다. **선단 공정에서 SRAM 밀도가 사실상 스케일링을 멈췄다.** WSE-3는 풀 노드 축소와 트랜지스터 54% 증가에도 WSE-2 대비 SRAM이 10%만 늘었다. 이 아키텍처의 가장 희소한 자원이 하필 다음 공정이 더는 사주지 않는 것이다.

### weight streaming — 흐름을 뒤집는다

GPU와 TPU에서는 weight가 상주하고 activation이 흐른다. **WSE는 반대다.** activation이 SRAM에 고정되고 weight가 흘러 지나간다. 마스터 weight는 MemoryX라는 DRAM·플래시 어플라이언스에 살고, 레이어마다 웨이퍼를 가로질러 스트리밍되며 곱셈-누산을 트리거하고 떠난다.

**이것이 사주는 것은 프로그래밍 모델이다.** 웨이퍼 하나가 한 레이어의 activation을 통째로 쥐므로 tensor parallelism도, pipeline parallelism도, FSDP 샤딩도 없다. 70B 모델이 **단일 디바이스 프로그램으로** 작성되고 멀티 시스템 확장은 순수 data parallelism이다. GPU 학습을 지배하는 병렬화 전략 스프레드시트에 Cerebras 페이지는 존재하지 않는다.

### 대가는 정직하게 드러난다

원문이 이 대목에서 가장 냉정하다.

- 스펙시트는 2,048 CS-3를 말하지만 **공개된 최대 클러스터는 64대**다
- 플랫폼에서 처음부터 학습된 최대 모델은 **70B(Jais 2)**이고, CS-1 이후 7년간 그 위는 없다
- GPU 랩이 관례적으로 공개하는 MFU를 **Cerebras는 한 번도 공개한 적이 없다**
- 44GB/웨이퍼라 1.6T급 모델은 GPU 랙 몇 개에 들어갈 것을 **CS-3 약 24대**가 필요하다
- 토큰당 API 가격이 GPU 기반 제공자의 **3~5배**

그럼에도 니치는 진짜다. 배치 1 decode 속도는 독립 측정으로 검증됐고(Llama 70B 446 tok/s, Llama 4 Maverick 2,522 tok/s), **지연 시간을 비용보다 높게 값매기는 고객들이 값을 치른다.**

### 소프트웨어에는 탈출구가 없다

컴파일러는 TPU처럼 컴파일러 주도지만 훨씬 좁은 구멍이다. **일반 코드 생성기가 아니라 커널 매처**다. 서브그래프를 손으로 쓴 커널 라이브러리에 매칭하고, 매치가 없으면 느린 자동 생성 커널로 떨어진다. 정적 그래프만, 동적 shape 없음, 데이터 의존 제어 흐름 없음.

**그리고 사용자 커널 경로가 아예 없다.** CUDA의 답이 "커널을 써라", TPU의 답이 Pallas, ROCm의 답이 Triton이라면, Cerebras의 답은 **"Cerebras 엔지니어를 부른다"**이다.

여기에 기묘한 면역이 있다. FlashAttention은 메모리 계층을 타일링하는 기법인데 **WSE에는 타일링할 계층이 없다.** AMD가 몇 달의 포팅 지연을 치르는 최적화 부류가 여기서는 성립하지 않는다. 다만 면역과 빈곤은 같은 사실이다 — CUDA에서 복리로 쌓이는 서드파티 커널 생태계가 **붙을 표면이 없다.**


&nbsp;

## AWS Trainium — 빌려 쓰고, 네트워크에 투자한다

Nitro 카드와 Graviton을 만든 Annapurna Labs가 **fast-follower**로 설계했다. 연산 코어는 TPU의 검증된 플레이북(128×128 weight-stationary systolic array, 소프트웨어 관리 스크래치패드, 전체 프로그램 컴파일)을 **Google의 XLA 컴파일러를 통째로 공유하는 데까지** 가져왔다.

진짜 Amazon의 것은 좁고 의도적이다. **빌려온 코어에 볼트로 붙인 전용 collective 통신 실리콘**, 그리고 AWS 안에서만 NVIDIA를 이기면 되도록 값을 매기는 수직 통합.

### 네 개의 엔진

Tensor Engine이 matmul FLOPs를 갖고 나머지 셋이 그 외 전부를 맡는다. 128×128 격자(16,384 MAC)를 weight-stationary로 돌리되, **NVIDIA가 warp 계층으로 감싸고 Google이 VLIW 번들에서 발행하는 것을 Trainium은 명명된 스크래치패드에 대한 명시적 명령 쌍으로 노출한다.**

물리 배열은 3세대 내내 128×128로 고정이고, **바뀌는 것은 셀당 몇 개의 곱을 채우느냐**다. Trn2가 FP8을 double-pump해 실효 256×128을, Trn3가 microscaling으로 실효 512×128을 제시한다. 물리 MAC 셀 수는 움직이지 않고 데이터패스가 더 좁은 숫자를 먹일 뿐이다.

나머지 셋(Vector, Scalar, GPSIMD)이 배열을 바쁘게 유지한다. 잘 컴파일된 스텝은 넷을 겹친다. **대가는 가장자리에서 나온다** — 특화 엔진 어디에도 맞지 않는 연산자는 느린 GPSIMD로 떨어지고, 이것이 새로운 아키텍처에서 병목이 될 가능성이 가장 큰 부분이다.

### collective를 실리콘에 넣는다

GPU에 깔끔한 대응물이 없는 블록이다. 분산 학습·추론은 벽시계 시간의 큰 몫을 collective에 쓴다 — 매 gradient step이 all-reduce, 매 MoE 레이어가 all-to-all이다.

**GPU에서는 그 collective가 수학을 돌리는 바로 그 SM 위에서 NCCL 커널로 돈다.** 통신과 연산이 같은 실리콘을 놓고 경쟁하고, 오버랩은 소프트웨어로 따내야 한다. Trainium은 이 기능을 전용 하드웨어로 떼어낸다 — Trn2 칩당 20개의 CC-Core가 NeuronLink 포트에 직결돼, Tensor·Vector 엔진이 계속 도는 동안 all-reduce와 all-to-all을 실행한다.

**Google이 SparseCore로, Cerebras가 오프코어 제로 필터로 한 것과 같은 수법이다.** 메인 엔진이 잘못된 모양인 워크로드를 찾아, 코어에서 사이클을 훔치는 대신 옆에 작은 전용 블록을 판다.

### torus에서 스위치로

Trn2까지는 TPU와 똑같이 torus다(인스턴스 16칩 4×4 2D torus, UltraServer 64칩 4×4×4 3D torus). **Trn3는 torus를 버리고 NeuronSwitch로 간다.** 이유는 Google을 high-radix로 밀었던 것과 같다 — **expert routing은 all-to-all이고 torus의 최악 사례**이며, 스위치는 최장 홉 쌍을 한 번의 교차로 바꾼다.

원문의 정리가 인상적이다. **Trainium의 인터커넥트 로드맵은 업계의 압축 재방송이다** — 워크로드가 최근접 이웃일 때 torus를 채택하고, 아닐 때 크로스바로 간다.

scale-out은 아예 새로 만들지 않았다. **AWS가 이미 돌리는 그 패브릭**이다. EFA NIC에 SRD 전송을 Nitro 카드로 오프로드한다. SRD는 RoCE나 InfiniBand의 단일 정렬 흐름 대신 **메시지를 최대 64개 경로로 뿌리고 신뢰성 있게, 그러나 순서 없이 전달**해 head-of-line 블로킹을 피한다.

증거는 Project Rainier다. Anthropic을 위해 미국 여러 데이터센터에 걸쳐 Trainium2 약 50만 칩, 2026년 초에는 Claude가 100만 칩 이상에서 돌았다. **외부 랩이 비NVIDIA 학습 플랫폼에 한 최대 규모의 커밋**이다.

### 소프트웨어

빌려 씀이 노골적이다. Neuron SDK는 **TPU와 같은 OpenXLA 기반의 컴파일러 우선 스택**이고, Google의 OpenXLA 발표는 Trainium을 TPU와 나란히 일급 PJRT 디바이스로 올린다.

탈출구는 **NKI(Neuron Kernel Interface)** — 네 엔진과 SBUF/PSUM을 직접 노출하는 타일 수준 Python 커널 언어다. Trainium의 Pallas이자 Triton이다.

CUDA와의 격차는 설계가 아니라 **성숙도**다. 앵커 테넌트가 일하는 방식이 가장 분명한 신호다 — **Anthropic은 PyTorch로 Trainium을 겨냥하는 데 그치지 않고 Annapurna와 함께 붙어 자체 NKI 커널을 쓰고 수정을 Neuron 스택에 upstream한다.** 프런티어에서 Trainium은 production-viable이지만 turnkey가 아니라 co-engineered다.


&nbsp;

## Groq LPU — 결정론

> 확보한 원문이 이 절의 Architecture 중간에서 끊겨 다른 칩보다 얕다.

**결정론 기계다.** 다른 모든 칩은 불확실성을 견디는 데 실리콘을 쓴다 — 메모리 지연을 감추는 캐시, 스톨을 메우는 스케줄러, 예측 못 할 경합을 푸는 arbiter. **LPU는 그것을 전부 지운다.** 캐시도, 분기 예측기도, arbiter도, reorder buffer도, 온칩 크로스바조차 없다.

스케줄링 문제 전체를 컴파일러에 넘겨 **모든 명령과 모든 바이트를 정확한 사이클에 배치**한다. 남는 것은 **돌려보기 전에 지연 시간을 아는 칩**이다.

TPU가 스케줄링을 컴파일러로 옮기면서도 HBM과 동적 네트워크를 남겼다면, **Groq는 마지막 비결정성까지 제거한다** — 메모리는 전부 SRAM이고 네트워크도 스케줄되므로 수백 칩이 하나의 clock-exact 프로그램으로 돈다.

구조도 반대 방향이다. 다른 칩들이 코어 하나를 복제해 다이에 타일링한다면, **LPU는 전통적 코어 하나를 뜯어 펼친다.** 명령 제어, 벡터 ALU, 행렬 유닛, 메모리, 네트워크가 각각 **functional slice**라는 다이 전체 높이의 칼럼이 되어 나란히 선다. 슬라이스 안은 균질하고 칩을 가로지르면 이질적이다.

데이터는 레지스터 파일에 앉아 발행을 기다리지 않는다. **조립 라인의 부품처럼 슬라이스를 가로질러 수평으로 흐르고**(사이클당 레지스터 한 홉), VLIW 명령이 제어 슬라이스에서 북쪽으로 올라와 그 흐름과 만난다. 데이터패스의 어떤 것도 반응하지 않는다 — 컴파일러가 매 사이클 모든 피연산자의 위치를 알고, 하드웨어는 클럭만 돌린다.

이 설계는 Tensor Streaming Processor(TSP)로 출발해 2024년 LPU로 개명됐다. 2025년 NVIDIA가 비독점 라이선스를 받고 창업자 Jonathan Ross와 팀 상당수를 데려갔으며, 2026년 GTC에서 **Rubin NVL72 옆의 지연 시간 보조 프로세서**로 다시 등장했다.


&nbsp;

## 가로로 읽기 — 반복되는 네 가지 축

6종을 세로로 읽으면 스펙시트지만, 가로로 읽으면 같은 질문에 대한 다른 답이 보인다.

### 1. 누가 스케줄하는가

| 하드웨어가 런타임에 | 컴파일러가 사전에 |
| --- | --- |
| NVIDIA (warp scheduler, 64 warp 오버커밋) | TPU (VLIW, 캐시 없음) |
| AMD (동일 계열) | Trainium (OpenXLA 상속) |
| | Groq (사이클 단위, 네트워크까지) |

Cerebras는 제3의 답이다 — **데이터 도착 자체가 트리거**라 스케줄이라는 개념이 다르게 작동한다.

트레이드오프는 대칭적이다. 하드웨어 스케줄러는 나쁜 상황을 덮어주지만 그 트랜지스터는 MAC에 못 쓴다. 컴파일러 스케줄링은 이론 천장에 더 가까이 가지만 **폴백 경로가 없다.**

### 2. 캐시인가 스크래치패드인가

NVIDIA는 둘 다 쓴다(L2 유지 + SMEM/TMEM을 명명된 스크래치패드로 노출). TPU·Trainium·Groq·Cerebras는 **캐시를 아예 없앴다.** AMD는 반대로 가서 256MB Infinity Cache를 얹었다.

### 3. 코히런트인가 메시지 패싱인가

**NVIDIA만 scale-up이 코히런트다.** NVLink+NVSwitch로 다른 GPU의 HBM이 로컬 메모리처럼 보인다. TPU의 ICI, Trainium의 NeuronLink는 메시지 패싱이고, 모든 멀티칩 연산이 컴파일러가 낸 명시적 collective다.

### 4. 같은 수법이 세 번 반복된다

**메인 엔진이 잘못된 모양인 워크로드는 옆에 작은 전용 블록을 판다.**

| 칩 | 전용 블록 | 흡수하는 워크로드 |
| --- | --- | --- |
| TPU | SparseCore | embedding lookup (irregular, all-to-all) |
| TPU v8i | CAE | decode 중 collective reduction |
| Trainium | CC-Core ×20 | all-reduce, all-to-all |
| Cerebras | 오프코어 제로 필터 | unstructured sparsity |

그리고 **토폴로지도 같은 궤적을 그린다.** collective가 최근접 이웃이면 torus, all-to-all(MoE expert routing)이면 스위치. TPU v8i의 Boardfly, Trainium Trn3의 NeuronSwitch가 몇 달 사이 같은 결론에 도달했다.


&nbsp;

## 정리

원문이 던지는 가장 유용한 프레임은 **"베팅(bets)"**이다. 각 칩은 스펙시트가 아니라 **워크로드의 미래에 대한 서로 다른 내기**다.

- **NVIDIA** — 워크로드는 계속 변한다. 그러니 전부 프로그래머블하게 두고 생태계로 이긴다
- **TPU** — 워크로드는 정적으로 예측 가능하다. 그러니 스케줄링을 컴파일러로 옮기고 MAC이 아닌 트랜지스터를 전부 지운다
- **AMD** — 추론은 capacity-bound가 된다. 그러니 메모리와 패키징에 투자하고 표준을 소유한다
- **Cerebras** — 메모리 월은 패키징 선택의 결과다. 그러니 웨이퍼를 자르지 않고 지연 시간을 판다
- **Trainium** — 클라우드가 제품이고 칩은 부품이다. 그러니 연산 논리는 빌려오고 네트워크와 랙에 투자한다
- **Groq** — 불확실성을 견디는 실리콘이 낭비다. 그러니 전부 지우고 컴파일러가 사이클을 확정한다

베팅이 갈리는 지점도 분명하다. **decode는 순수한 대역폭 문제**라 Cerebras가 유리하고, **MoE의 all-to-all**은 torus를 벌하며 스위치를 부른다. **새로운 attention 변종**은 커널 탈출구가 있는 플랫폼에 유리하다 — 그래서 CUDA에는 커널이, TPU에는 Pallas가, Trainium에는 NKI가 있고, Cerebras에는 없다.

Hennessy와 Patterson은 Cambrian explosion을 약속했다. 지금 벌어지는 일이 그것이고, **어느 body plan이 살아남을지는 워크로드가 어느 쪽으로 움직이느냐에 달려 있다.**

> 관련 글: [vLLM + AWS Trainium 워크숍 실습 기록]({{< ref "/posts/llm/llm-vllm-trainium-workshop" >}}) — 이 글의 Trainium 절에서 설명한 systolic array, 소프트웨어 스크래치패드, NKI를 EKS 위에서 실제로 돌려본 기록
