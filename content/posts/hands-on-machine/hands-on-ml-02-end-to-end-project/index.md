---
title: "핸즈온 머신러닝 2주차 - 머신러닝 프로젝트 처음부터 끝까지"
date: 2026-11-07T20:00:00+09:00
draft: false
tags: ["Machine Learning", "핸즈온 머신러닝", "Scikit-Learn", "pandas", "RMSE", "독서기록"]
categories: ["Machine Learning"]
series: ["핸즈온ML 2주차"]
featuredImage: images/banners/hands-on-ml-02-end-to-end-project-d46203ea.png
---
`핸즈온 머신러닝 with 사이킷런, 파이토치` 2장을 읽고 정리한 글이다. 이번에는 2.5.3절 **특성 스케일과 변환**을 다룬다. 글 중간의 그림은 직접 눌러 볼 수 있고, 분포는 모양을 보여 주기 위해 만든 예시 값이다.

## 1. 특성 스케일과 변환 (2.5.3절)

### 1.1 왜 스케일링하는가

대부분의 머신러닝 알고리즘은 입력 특성들의 숫자 범위가 크게 다르면 제대로 학습하지 못한다. 주택 가격 데이터에서 전체 방 개수는 6 ~ 39,320인데 중간 소득은 0 ~ 15다. 그대로 두면 모델은 숫자가 큰 방 개수에 끌려가고 중간 소득을 거의 무시한다.

{{< scaling-demo range >}}

트리 기반 알고리즘(5장, 6장)은 예외다. 특성 하나의 값을 기준으로 나누기만 하므로 범위가 달라도 영향을 받지 않는다.

모든 특성의 범위를 맞추는 방법은 두 가지가 널리 쓰인다.

| 방법 | 계산 | 결과 범위 | 이상치 영향 |
| --- | --- | --- | --- |
| min-max 스케일링 (정규화, normalization) | (값 - 최솟값) / (최댓값 - 최솟값) | 0 ~ 1 (변경 가능) | 크다 |
| 표준화 (standardization) | (값 - 평균) / 표준 편차 | 제한 없음 | 작다 |

### 1.2 min-max 스케일링

최솟값을 빼고 범위로 나눠 0 ~ 1 사이로 옮긴다. scikit-learn의 `MinMaxScaler` 가 이 일을 하고, `feature_range` 로 범위를 바꿀 수 있다. 신경망은 평균이 0인 입력에서 잘 동작해서 -1 ~ 1 범위를 자주 쓴다.

```python
from sklearn.preprocessing import MinMaxScaler

min_max_scaler = MinMaxScaler(feature_range=(-1, 1))
housing_num_min_max_scaled = min_max_scaler.fit_transform(housing_num)
```

"정규화"라는 말은 여러 뜻으로 쓰인다. scikit-learn의 `Normalizer` 는 각 **행**의 ℓ2 노름을 1로 맞추는 전처리라서 min-max 스케일링과 전혀 다른 결과를 낸다.

### 1.3 표준화

평균을 빼고 표준 편차로 나눈다. 결과는 평균 0, 표준 편차 1이 되고 값의 범위는 제한되지 않는다.

```python
from sklearn.preprocessing import StandardScaler

std_scaler = StandardScaler()
housing_num_std_scaled = std_scaler.fit_transform(housing_num)
```

표준화의 장점은 이상치에 덜 흔들린다는 점이다. 어떤 구역의 중간 소득이 100으로 잘못 입력됐다고 하자. min-max 스케일링은 이 값을 1에 놓고 나머지를 전부 0 ~ 0.15로 밀어 넣지만, 표준화는 평균과 표준 편차가 조금 바뀔 뿐이다.

{{< scaling-demo outlier >}}

희소 행렬은 평균을 빼면 0이 아닌 값이 대량으로 생겨 희소성이 깨진다. `StandardScaler(with_mean=False)` 로 두면 평균을 빼지 않고 표준 편차로만 나눈다.

### 1.4 스케일러는 훈련 세트로만 fit 한다

스케일러도 추정기다. `fit()` 이나 `fit_transform()` 은 **훈련 세트에만** 쓰고, 검증 세트, 테스트 세트, 새 데이터에는 `transform()` 만 쓴다.

훈련 세트는 항상 정해진 범위로 변환되지만 새 데이터는 그렇지 않다. 훈련 범위를 벗어난 값은 0 ~ 1 밖으로 나간다. 이를 막으려면 `MinMaxScaler(clip=True)` 를 쓴다.

{{< scaling-demo clip >}}

### 1.5 두꺼운 꼬리는 먼저 변환한다

분포의 꼬리가 두꺼우면(평균에서 먼 값이 드물지 않으면) min-max 스케일링과 표준화 모두 대부분의 값을 좁은 구간에 몰아넣는다. 모델은 이런 입력을 잘 다루지 못하므로, 스케일링하기 **전에** 분포를 대칭에 가깝게 바꾼다.

| 분포 모양 | 변환 |
| --- | --- |
| 오른쪽 꼬리가 두꺼운 양수 특성 | 제곱근 (또는 0 ~ 1 사이의 거듭제곱) |
| 꼬리가 아주 길고 두꺼운 특성 (멱법칙 분포) | 로그 |

`population` 이 멱법칙에 가깝다. 주민 1만 명인 구역은 1천 명인 구역보다 지수적으로 드문 것이 아니라 10배쯤 드물 뿐이다. 로그를 취하면 종 모양에 가까워진다.

{{< scaling-demo log >}}

### 1.6 버킷타이징

두꺼운 꼬리를 다루는 다른 방법은 **버킷타이징(bucketizing)** 이다. 분포를 거의 같은 개수씩 담는 구간으로 자르고, 값을 구간 번호로 바꾼다. 백분위수로 바꾸는 것이 한 예다.

{{< scaling-demo bucket >}}

구간마다 개수가 같으므로 결과는 거의 균등 분포다. 추가 스케일링이 필요 없고, 버킷 개수로 나누면 0 ~ 1 범위가 된다.

`housing_median_age` 처럼 정점(모드)이 여러 개인 **멀티모달 분포**에도 쓸 수 있다. 이때는 버킷 번호를 수치가 아니라 **카테고리**로 다루고 `OneHotEncoder` 로 인코딩한다. 버킷이 너무 많으면 특성이 늘어나므로 적당히 잡는다. 이렇게 하면 회귀 모델이 연식 구간마다 다른 규칙을 배울 수 있다.

### 1.7 가우스 RBF로 유사도 특성 만들기

멀티모달 분포를 다루는 또 다른 방법은 **특정 모드와의 유사도**를 새 특성으로 추가하는 것이다. 유사도는 보통 입력값과 고정 지점 사이의 거리에만 의존하는 **방사 기저 함수(radial basis function, RBF)** 로 잰다.

가장 널리 쓰는 가우스 RBF는 고정 지점에서 멀어질수록 값이 지수적으로 줄어든다. 주택 연식 x와 35 사이의 유사도는 exp(-γ(x - 35)²)이고, 하이퍼파라미터 γ(gamma)가 감소 속도를 정한다.

```python
from sklearn.metrics.pairwise import rbf_kernel

age_simil_35 = rbf_kernel(housing[["housing_median_age"]], [[35]], gamma=0.1)
```

{{< scaling-demo rbf >}}

새 특성은 연식 35에서 1로 가장 높다. 이 연식대의 주택이 낮은 가격과 관련이 있다면 모델에 도움이 된다.

### 1.8 타깃값의 변환과 역변환

입력 특성뿐 아니라 타깃도 변환할 수 있다. 타깃 분포의 꼬리가 두꺼우면 로그를 취하는 식이다. 다만 그러면 모델이 예측하는 것은 주택 가격이 아니라 **주택 가격의 로그**이므로, 예측값에 지수 함수를 적용해 되돌려야 한다.

scikit-learn 변환기는 대부분 역변환용 `inverse_transform()` 을 제공한다. 아래는 레이블을 `StandardScaler` 로 스케일링해 학습하고, 예측을 원래 단위로 되돌리는 코드다.

```python
from sklearn.linear_model import LinearRegression

target_scaler = StandardScaler()
scaled_labels = target_scaler.fit_transform(housing_labels.to_frame())

model = LinearRegression()
model.fit(housing[["median_income"]], scaled_labels)
some_new_data = housing[["median_income"]].iloc[:5]

scaled_predictions = model.predict(some_new_data)
predictions = target_scaler.inverse_transform(scaled_predictions)
```

`StandardScaler` 는 2차원 입력을 받으므로 `to_frame()` 으로 Series를 DataFrame으로 바꿨다.

{{< scaling-demo inverse >}}

같은 일을 `TransformedTargetRegressor` 가 한 번에 한다. 회귀 모델과 레이블 변환기를 넘기고 **원본 레이블**로 학습하면, 내부에서 레이블을 변환해 학습하고 예측할 때 자동으로 역변환한다. 스케일링과 역변환을 따로 챙기지 않아도 되어 실수가 줄어든다.

```python
from sklearn.compose import TransformedTargetRegressor

model = TransformedTargetRegressor(LinearRegression(),
                                   transformer=StandardScaler())
model.fit(housing[["median_income"]], housing_labels)
predictions = model.predict(some_new_data)
```

### 1.9 정리

| 상황 | 선택 |
| --- | --- |
| 특성마다 숫자 범위가 다르다 | min-max 스케일링 또는 표준화 |
| 이상치가 있다 | 표준화 |
| 신경망 입력 | `MinMaxScaler(feature_range=(-1, 1))` |
| 희소 행렬 | `StandardScaler(with_mean=False)` |
| 새 데이터가 훈련 범위를 벗어날 수 있다 | `MinMaxScaler(clip=True)` |
| 오른쪽 꼬리가 두껍다 | 스케일링 전에 제곱근이나 로그 |
| 꼬리가 두껍거나 멀티모달이다 | 버킷타이징 (멀티모달이면 원-핫 인코딩) |
| 특정 값 근처가 중요하다 | 가우스 RBF 유사도 특성 |
| 타깃을 변환했다 | `inverse_transform()` 또는 `TransformedTargetRegressor` |

순서도 중요하다. 스케일러는 훈련 세트로만 fit 하고, 꼬리가 두꺼운 특성은 변환을 먼저 한 뒤 스케일링한다.
