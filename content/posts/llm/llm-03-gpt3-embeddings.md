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

GPT-3의 임베딩 벡터는 길이가 \(d_{\text{model}} = 12288\) 이다.
즉 token 하나가 **12288개의 숫자**로 표현된다.

$$
\mathbf{e}_{\text{cat}} = \big[\, e_1,\; e_2,\; \dots,\; e_{12288} \,\big] \in \mathbb{R}^{12288}
$$

## 임베딩 행렬

이 벡터들은 어디서 오는가? **임베딩 행렬(embedding matrix)** 이라는 거대한 표에서 꺼내온다.
사전의 각 token마다 벡터 하나씩을 행(row)으로 쌓아둔 것이다.

GPT-3의 사전 크기는 \(V = 50257\) 이므로, 임베딩 행렬 \(W_E\) 는 다음 크기의 행렬이다.

$$
W_E \in \mathbb{R}^{V \times d_{\text{model}}} = \mathbb{R}^{50257 \times 12288}
$$

$$
W_E =
\begin{bmatrix}
\text{— } \mathbf{e}_{\text{(token 0)}} \text{ —} \\
\text{— } \mathbf{e}_{\text{(token 1)}} \text{ —} \\
\vdots \\
\text{— } \mathbf{e}_{\text{(token 50256)}} \text{ —}
\end{bmatrix}
$$

이 표 하나가 담는 숫자만 \(50257 \times 12288 \approx 6.17 \times 10^{8}\), 약 **6억 개**다.
이 값들은 사람이 정하는 게 아니라, **학습을 통해 얻어지는 파라미터**다.

## 임베딩 조회 = one-hot 벡터 × 행렬

"token ID로 행렬의 해당 행을 꺼낸다"는 조회(lookup)를, 행렬 곱으로 정확히 표현할 수 있다.
핵심 도구는 **one-hot 벡터**다.

token ID가 \(i\) 일 때, one-hot 벡터 \(\mathbf{o}_i \in \mathbb{R}^{V}\) 는 **\(i\)번째 성분만 1, 나머지는 0** 인 벡터다.

$$
\mathbf{o}_i = \big[\,0,\; \dots,\; 0,\; \underbrace{1}_{i\text{번째}},\; 0,\; \dots,\; 0\,\big]
$$

이 one-hot 벡터를 임베딩 행렬에 곱하면, 정확히 \(i\)번째 행만 뽑혀 나온다.

$$
\mathbf{e}_i = \mathbf{o}_i^{\top} \, W_E
$$

곱셈이 "행 하나 선택"이 되는 이유는, 0인 성분은 해당 행을 0으로 지우고 1인 성분만 그 행을 살리기 때문이다.
즉 **임베딩 조회는 곧 one-hot 벡터와 임베딩 행렬의 곱**이다.

## 문장 전체를 한 번에 — 행렬 대 행렬

실제로는 token 하나가 아니라 **문장(token 여러 개)** 을 한꺼번에 처리한다.
길이 \(n\) 인 token 시퀀스의 one-hot 벡터들을 세로로 쌓으면 행렬 \(O \in \mathbb{R}^{n \times V}\) 가 된다.

여기에 임베딩 행렬을 곱하면, 문장의 모든 token 임베딩이 한 번의 행렬 곱으로 나온다.

$$
X = O \, W_E \in \mathbb{R}^{n \times d_{\text{model}}}
$$

$$
\underbrace{O}_{n \times V} \cdot \underbrace{W_E}_{V \times d}
\;=\; \underbrace{X}_{n \times d} \;=\;
\begin{bmatrix}
\text{— } \mathbf{e}_{t_1} \text{ —} \\
\text{— } \mathbf{e}_{t_2} \text{ —} \\
\vdots \\
\text{— } \mathbf{e}_{t_n} \text{ —}
\end{bmatrix}
$$

이제 \(X\) 의 각 행이 문장 속 token 하나의 임베딩이다.
행렬 크기가 \((n \times V) \cdot (V \times d) = (n \times d)\) 로 맞아떨어지는 것을 확인하면 감이 잡힌다.

## 위치 정보 더하기 — positional embedding

여기엔 빠진 게 하나 있다. 지금까지의 \(X\) 는 **token의 순서**를 전혀 모른다.
`"개가 사람을 물었다"` 와 `"사람이 개를 물었다"` 가 구분되지 않는다.

그래서 GPT-3는 **위치마다 다른 벡터**(learned positional embedding)를 하나 더 준비한다.
위치용 행렬 \(W_P\) 는 문맥 최대 길이 \(n_{\text{ctx}} = 2048\) 에 대해 다음 크기다.

$$
W_P \in \mathbb{R}^{n_{\text{ctx}} \times d_{\text{model}}} = \mathbb{R}^{2048 \times 12288}
$$

문장 길이 \(n\) 에 맞춰 앞의 \(n\) 개 위치 벡터를 잘라 \(P \in \mathbb{R}^{n \times d}\) 를 만들고, **token 임베딩에 그냥 더한다**.

$$
H_0 = X + P =
\begin{bmatrix}
\mathbf{e}_{t_1} + \mathbf{p}_1 \\
\mathbf{e}_{t_2} + \mathbf{p}_2 \\
\vdots \\
\mathbf{e}_{t_n} + \mathbf{p}_n
\end{bmatrix}
\in \mathbb{R}^{n \times d}
$$

이 \(H_0\) 가 **Transformer 블록에 들어가는 첫 입력**이다.
즉 "무슨 단어인가(token embedding) + 몇 번째인가(positional embedding)"를 합친 벡터에서 모든 계산이 시작된다.

## 예시로 보기 — "나는 밥을 먹었다"를 3차원으로

지금까지의 과정을 작은 숫자로 직접 따라가 본다.
실제 GPT-3는 \(d_{\text{model}} = 12288\) 이지만, 여기서는 눈으로 볼 수 있게 **\(d_{\text{model}} = 3\)** 으로 낮춘다.
사전 크기도 실제 50257 대신, 예시용으로 **\(V = 6\)** 이라 하자.

**1) token으로 쪼개고 ID를 붙인다.**

문장 `"나는 밥을 먹었다"` 는 token 3개(\(n = 3\))로 나뉜다.

| token | ID  |
| ----- | --- |
| 나는    | 0   |
| 밥을    | 1   |
| 먹었다   | 2   |

**2) 임베딩 행렬 \(W_E\) 에서 각 token의 행을 꺼낸다.**

여기서는 \(6 \times 3\) 크기의 작은 행렬을 예로 든다(값은 학습으로 얻어진 것이라 가정).

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
\leftarrow \text{나는 (0)} \\
\leftarrow \text{밥을 (1)} \\
\leftarrow \text{먹었다 (2)} \\
\\ \\ \\
\end{matrix}
$$

**3) one-hot 벡터로 행을 선택한다.**

`"나는"`(ID 0)의 one-hot은 \([1,0,0,0,0,0]\) 이고, 이를 \(W_E\) 에 곱하면 정확히 0번째 행이 나온다.

$$
\mathbf{e}_{\text{나는}} = [\,1,0,0,0,0,0\,] \, W_E = [\,0.2,\; 0.9,\; 0.1\,]
$$

**4) 문장 전체를 한 번의 행렬 곱으로.**

세 token의 one-hot을 세로로 쌓은 \(O \in \mathbb{R}^{3 \times 6}\) 에 \(W_E\) 를 곱하면, 문장의 임베딩 \(X\) 가 한 번에 나온다.

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

**5) 위치 임베딩을 더해 첫 입력 \(H_0\) 를 만든다.**

각 위치(0, 1, 2번째)에 해당하는 위치 벡터 \(P\) 를 더한다.

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

이 \(3 \times 3\) 행렬 \(H_0\) 가, 실제 GPT-3에서는 \(3 \times 12288\) 크기가 되어 Transformer 블록으로 들어간다.
차원만 커질 뿐, 흐름은 이 예시와 똑같다.

## 왜 벡터인가

임베딩의 진짜 힘은, **비슷한 의미의 token이 벡터 공간에서 가깝게** 학습된다는 데 있다.
두 벡터가 얼마나 같은 방향을 보는지는 **cosine similarity(코사인 유사도)** 로 잰다.

$$
\cos(\mathbf{a}, \mathbf{b}) = \frac{\mathbf{a} \cdot \mathbf{b}}{\lVert \mathbf{a} \rVert \, \lVert \mathbf{b} \rVert}
$$

값이 1에 가까우면 방향이 거의 같고(의미가 비슷), 0이면 무관, -1이면 반대다.
그래서 `king`과 `queen`, `cat`과 `dog` 같은 token들이 서로 가까운 벡터로 자리 잡는다.

아래에서 두 벡터의 끝점을 **드래그**해 보면, 방향이 일치할 때 cos가 1, 수직이면 0, 정반대면 -1이 되는 것을 직접 확인할 수 있다.

{{< cosine-demo >}}

정수 ID로는 표현할 수 없던 **"의미의 가까움"** 을 벡터의 방향과 거리로 담아내는 것이 임베딩의 목적이다.

## GPT-3 숫자 요약

| 기호 | 의미 | GPT-3 값 |
| --- | --- | --- |
| \(V\) | 사전 크기(token 종류 수) | 50257 |
| \(d_{\text{model}}\) | 임베딩 벡터 길이 | 12288 |
| \(n_{\text{ctx}}\) | 최대 문맥 길이 | 2048 |
| \(W_E\) | token 임베딩 행렬 | \(50257 \times 12288\) (약 6.2억) |
| \(W_P\) | 위치 임베딩 행렬 | \(2048 \times 12288\) (약 2500만) |

## 정리

- 임베딩은 **정수 token을 \(d_{\text{model}}\) 차원 실수 벡터로 바꾸는 것**이다.
- 조회는 곧 행렬 곱이다: \(\mathbf{e}_i = \mathbf{o}_i^\top W_E\), 문장 전체는 \(X = O\,W_E\).
- 여기에 **위치 임베딩을 더해** \(H_0 = X + P\) 를 만들면, 그게 Transformer의 첫 입력이다.
- 벡터로 바꾸는 이유는, **의미의 유사함을 방향·거리(cosine similarity)로 표현**하기 위해서다.
