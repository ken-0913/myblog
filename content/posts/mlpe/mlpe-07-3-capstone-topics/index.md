---
title: "MLPE 스터디 4주차 - Ch7.2 ~ 7.3 도쿄 23구 중고 맨션 데이터로 따라 하는 KFP 데이터 준비 파이프라인"
date: 2026-11-13T10:00:00+09:00
draft: false
tags: ["MLOps", "MLPE", "Kubeflow", "Kubeflow Pipelines", "KFP", "Artifact", "Regression", "Geocoding", "Capstone"]
categories: ["MLOps"]
series: ["MLPE 4주차"]
featuredImage: images/banners/mlpe-07-3-capstone-topics-c1383d08.png
---
`Machine Learning Platform Engineering`의 7.2 ~ 7.3절 데이터 준비 파이프라인을 실제 **도쿄 23구 중고 맨션 매물 데이터**로 학습한 과정이다.

## 1. 한눈에 보기

### 1.1 배경: 호가가 적정한지 모른다

도쿄에서 중고 맨션 매물을 보면 가격표는 있지만, 그 가격이 **주변 시세에 비해 비싼지 싼지**는 알기 어렵다. 같은 역 근처라도 준공 연도(築年)와 면적, 층에 따라 가격이 몇 배씩 달라지고, 한 매물이 중개사마다 다른 가격으로 올라오기도 한다. 그래서 매물을 보는 사람은 결국 비슷한 조건의 매물을 여럿 찾아 머릿속으로 비교하게 된다.

이 비교를 모델이 대신하게 하는 것이 목표이다. **주소와 매물 조건**을 넣으면 **추정 가격과 80% 구간**을 돌려주고, 실제 호가가 그 구간의 어디에 있는지를 보여 준다.

### 1.2 풀려는 문제

**살고 싶은 주소와 원하는 맨션 조건**(면적, 준공 연도, 층, 방 구조(間取り))을 넣으면, 지금 그 자리에 매물이 올라와 있지 않아도 **그 조건이면 호가가 대략 얼마 선인지**를 알려 준다. 학습 데이터가 매도 호가이므로 실제 성약 가격은 아니고, 호가 수준의 추정값이다.

![입력과 출력. 입력은 주소(필수), 전용 면적·준공 연도·소재 층·방 구조(専有面積·築年·所在階·間取り, 필수), 총 층수·도보 분·방향(総階数·徒歩分·向き, 선택)이다. 주소는 지오코딩으로 위도·경도가 되어 회귀 모델에 들어간다. 모델의 타깃은 m²당 단가(만엔)이고 출력은 추정 가격(만엔)과 80% 구간이다.](problem-io.svg)

- **문제 유형**: 지도학습 회귀. 수집한 매물마다 주소·조건과 함께 가격이 적혀 있어 정답이 있는 **지도학습**이고, 맞힐 값이 가격이라는 연속값이라 **회귀**이다
- **타깃**: 가격이 아니라 **m²당 단가**. 위치가 결정하는 것은 단가에 가깝고, 가격은 단가에 면적을 곱하면 된다
- **위치가 가장 큰 변수**: 면적이나 준공 연도(築年)를 보지 않고 어느 구(区)인지만 알아도 단가 차이의 절반을 맞힐 수 있고, 동 이름(町名)까지 알면 3분의 2를 맞힐 수 있다.


| 아는 것       | 찍는 방법                                                        | 틀리는 정도   |
| ---------- | ------------------------------------------------------------ | -------- |
| 없음         | 모든 매물을 전체 중앙값 142만엔/m²로 찍는다                                  | 100 (기준) |
| 어느 구(区)인지  | 그 구의 중앙값으로 찍는다 (미나토구(港区) 267, 세타가야구(世田谷区) 127, 아다치구(足立区) 70) | 48       |
| 어느 동(町名)인지 | 그 동의 중앙값으로 찍는다 (미타(三田) 391, 코난(港南) 195, 타카나와(高輪) 272)        | 33       |

> **핸즈온ML 보강**: [문제 정의(지도 학습, 회귀, 배치 학습)](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#problem-framing) · [RMSE와 MAE](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#rmse-mae) · [타깃 변환](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#transforms)


### 1.3 데이터 현황

- **원본**
  -  SUUMO 의 도쿄 23구 중고 맨션 목록. (2026-11-13 에 한 번 수집한 스냅샷)
- **robots.txt 준수**
  -  수집 경로(`/ms/chuko/tokyo/` 아래 목록과 상세 페이지)는 `User-agent: *` 의 `Disallow` 목록에 없음 (2026-11-14 확인)
- **요청 간격**
  -  워커 2개, 요청마다 1.0 ~ 1.5초 대기. 초당 약 1.5회 이하
- **용도와 공개 범위**
  -  개인 학습 목적. 글에는 집계 통계만 싣는다. 아래 구조 설명용 한 건은 물건명, ID, URL 을 가렸다



#### 매물 한 건의 구조

한 행이 매물 하나이고 38열이다. 크롤러가 SUUMO 화면의 글자를 그대로 둔 **원문 열**과, 거기서 숫자만 뽑은 **파싱 열**이 짝을 이룬다. 모델에 들어가는 것은 파싱 열이다. 아래는 세타가야구(世田谷区)의 2LDK 매물 한 건이다.


| 원문 열                                                     | 값                            | 파싱 열                                              | 이 파이프라인에서의 쓰임                           |
| -------------------------------------------------------- | ---------------------------- | ------------------------------------------------- | --------------------------------------- |
| 가격(`価格`)                                                 | 7980万円                       | 가격\_만엔(`価格_万円`) = 7980                            | **타깃**. 면적으로 나눠 m²당 단가로 바꾼다             |
| 전용 면적(`専有面積`)                                            | 60.04m2（壁芯）                  | `専有面積_m2` = 60.04                                 | 필수 입력                                   |
| 방 구조(`間取り`)                                              | 2LDK                         | 그대로                                               | 필수 입력                                   |
| 준공 시기(`完成時期（築年月）`)                                       | 1985年2月                      | 준공 연도(`築年`) = 1985, 건물 연식(`築年数`) = 41             | 준공 연도는 필수 입력. 건물 연식은 수집 연도에 따라 변하므로 버린다 |
| 소재 층/구조·층수(`所在階/構造・階建`)                                  | 4階/RC5階建                     | 소재 층(`所在階_階`) = 4, 구조(`構造`) = RC, 총 층수(`総階数`) = 5 | 소재 층은 필수, 총 층수와 구조는 선택 입력               |
| 주소(`住所`)                                                 | 東京都世田谷区新町２                   | 없음                                                | 지오코딩 입력. 초메(丁目)까지만 적혀 있다                |
| 교통(`交通`)                                                 | 東急田園都市線「桜新町」歩9分, 「駒沢大学」歩13分  | 가장 가까운 역(`最寄駅`) = 桜新町, 최단 도보 분(`最短徒歩分`) = 9       | 선택 입력                                   |
| 방향(`向き`)                                                 | 東                            | 동(東). 남, 남동, 북서 같은 8방위                            | 선택 입력                                   |
| 물건명(`物件名`)                                               | (가림)                         | 없음                                                | 중복 제거 키. 모델에는 넣지 않는다                    |
| 총 호수(`総戸数`), 관리비(`管理費`), 수선적립금(`修繕積立金`), 캐치카피(`キャッチコピー`) | 19戸, 1万8850円／月, 2万3010円／月, … | 일부만                                               | 쓰지 않는다. 사용자가 입력할 수 없거나 호가 정보가 섞여 있다     |
| 물건 ID(`物件ID`), URL, 갱신 일시(`更新日時`)                        | (가림)                         | 없음                                                | 수집 관리용                                  |


이 매물의 단가는 7980 / 60.04 = 약 133만엔/m² 로, 세타가야구 중앙값 127만엔과 비슷한 수준이다.

#### 집계


| 항목                 | 값                                                                                                   |
| ------------------ | --------------------------------------------------------------------------------------------------- |
| 규모                 | 32,593행, 38열, CSV 20MB                                                                              |
| 타깃 가격\_만엔(`価格_万円`) | 결측 0, 650 \~ 216,800만엔, 중앙값 8,298                                                                   |
| 필수 피처의 빈 값         | 없음. 면적(面積), 준공 연도(築年), 구(区), 방 구조(間取り), 가장 가까운 역(最寄駅) 다섯 컬럼은 32,593건 모두 채워져 있다                      |
| 구(区)별 단가 차이        | m²당 중앙값이 가장 비싼 구는 미나토구(港区) 266.6만엔, 가장 싼 구는 아다치구(足立区) 70.1만엔. 약 3.8배 차이                             |
| 중복 매물              | 물건명, 주소, 가격, 면적, 층이 모두 같은 매물이 8,462건(26.0%). 같은 집을 여러 중개사가 따로 올린 것으로, 그대로 두면 학습과 평가에 같은 집이 양쪽에 들어간다 |
| 주소의 자세한 정도         | 번지(番地)까지 적힌 매물은 19%뿐이다. 75%는 초메(丁目, 동 아래 블록 번호)까지, 6%는 동 이름(町名)까지만 적혀 있어, 위치는 초메 단위로 다룬다            |


주의할 점은 두 가지이다. 같은 매물이 여러 번 올라온 **중복이 26%** 이고, 주소 해상도는 대부분 **초메(丁目)까지**이다. 앞의 것은 정제 단계에서, 뒤의 것은 지오코딩과 분할 단계에서 다룬다.

> **핸즈온ML 보강**: [데이터 구조 훑어보기](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#quick-look) · [상관관계와 이상한 수평선](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#correlation)

### 1.4 진행 단계

준비 하나와 본 단계 다섯 개로 나눈다. 책의 절 순서를 그대로 따르되, 예제 데이터만 매물 데이터로 바꾼다. 7.1절 Kubeflow 노트북은 [3주차 글](../mlpe-07-1-notebooks-data-passing/)에서 다뤘으므로 여기서는 7.2절부터 시작한다.

![7장 진행 단계. 준비 하나와 본 단계 다섯 개가 왼쪽에서 오른쪽으로 이어진다. 0 준비: 데이터 적재. A 단계: 값과 경로 전달. B 단계: 아티팩트 타입. C 단계: 아티팩트로 잇는 파이프라인. D 단계: 고정 경로로 잇는 파이프라인. E 단계: target_image.](ch7-lab-order.svg)


| 단계  | 데이터            | 하는 일                                                                                                        |
| --- | -------------- | ----------------------------------------------------------------------------------------------------------- |
| A   | 구 하나의 매물 CSV   | 컴포넌트 사이에 데이터를 넘기는 두 방법을 해 본다. 매물 건수 같은 작은 값은 반환값으로, CSV 같은 큰 데이터는 파일 경로로 넘긴다                                |
| B   | 매물 요약과 기준선     | KFP 가 결과물을 저장하는 종류(데이터셋, 모델, 지표, 리포트 등) 8가지를 하나씩 만들어 UI 에서 어떻게 보이는지 확인한다                                    |
| C   | 통합 CSV         | 다운로드 → 분할 → 확인 세 컴포넌트를, 앞의 출력 파일을 뒤가 받는 방식으로 잇는다. 웹 화면에서 올려 실행한다                                            |
| D   | 통합 CSV와 좌표 데이터 | 본 파이프라인. CSV 를 Parquet 으로 바꾸고, 주소에 좌표를 붙이고, 초메(丁目) 단위로 나눠 S3 호환 버킷의 정해진 폴더에 올린 뒤 검사한다. Python 코드로 등록하고 실행한다 |
| E   | D 단계와 같음       | D 와 같은 파이프라인을, 실행할 때마다 패키지를 설치하는 대신 미리 만든 컨테이너 이미지로 돌린다. 시작 시간과 결과를 비교한다                                    |




## 2. 준비: 데이터 적재

매물 수집이 끝났다면 데이터 파일을 S3 호환 버킷에 적재한다. AWS S3 대신 같은 방식으로 쓰는 저장소를 클러스터 안에 두었다. 매물 정보는 버킷에 올리고, 매물 정보에 없는 좌표 데이터는 국토교통성(国土交通省)이 공개 URL 로 제공하므로 파이프라인이 그 URL 에서 직접 내려받는다.

![S3 호환 버킷에 미리 올려 둘 것. 크롤러가 만든 통합 CSV 하나를 datasets 버킷의 suumo/raw/2026-11-13/tokyo_23ku_all.csv 로 올린다. A ~ E 모든 단계가 이 파일 하나를 읽는다. 좌표 데이터는 공개 URL 에서 파이프라인이 직접 받는다.](rustfs-staging.svg)

아래의 과정을 진행한다.

1. 버킷 `datasets` 를 만든다. 이미 있으면 그대로 쓴다.
2. 통합 CSV `tokyo_23ku_all.csv` 를 `suumo/raw/2026-11-13/` 아래에 올린다.
3. 실험 `ch07-suumo` 를 만든다.

1, 2 는 스크립트 `scripts/upload-raw.sh` 하나로 한다. 원본이 맥에만 있어서 클러스터 Job 이 아니라 맥에서 실행한다.

- 접속 키는 클러스터 Secret `rustfs-credentials` 에서 읽어 env 로만 쓴다. 화면에 찍지 않는다.
- 버킷이 있으면 건너뛰고, 같은 경로에 같은 크기의 파일이 있으면 건너뛴다. 여러 번 돌려도 결과가 같다.
- `--dry-run` 으로 할 일만 먼저 보고, `--snapshot` 으로 날짜를 바꿔 다시 수집한 데이터를 올린다.

먼저 `--dry-run` 으로 할 일을 확인했다.

```terminal {title="개발 PC: dry-run"}
$ ./scripts/upload-raw.sh --dry-run
==========================================================
📦 SUUMO 원본 업로드
   원본   : .../summo-crwal/data/csv/tokyo_23ku_all.csv (20419749 bytes, 헤더 제외 약 32593 줄)
   대상   : s3://datasets/suumo/raw/2026-11-13/tokyo_23ku_all.csv
   (dry-run: 버킷과 파일을 만들지 않는다)
==========================================================
✅ 접속 키 읽음 (Secret kubeflow/rustfs-credentials)
➡️  버킷 datasets 없음 → 만들 예정
➡️  s3://datasets/suumo/raw/2026-11-13/tokyo_23ku_all.csv 로 올릴 예정
```

그다음 실제로 올리고, 같은 명령을 한 번 더 실행해 건너뛰는 것까지 확인했다.

```terminal {title="개발 PC: 업로드"}
$ ./scripts/upload-raw.sh
✅ 접속 키 읽음 (Secret kubeflow/rustfs-credentials)
✅ 버킷 datasets 만듦
✅ 업로드 완료: s3://datasets/suumo/raw/2026-11-13/tokyo_23ku_all.csv (20419749 bytes)
2026-11-14 14:48:41   20419749 tokyo_23ku_all.csv

$ ./scripts/upload-raw.sh
✅ 접속 키 읽음 (Secret kubeflow/rustfs-credentials)
✅ 버킷 datasets 있음
✅ 같은 크기의 파일이 이미 있음 → 건너뜀 (덮어쓰려면 --force)
```


| 항목  | 결과                                                                        |
| --- | ------------------------------------------------------------------------- |
| 버킷  | `datasets` 생성 (기존 버킷 7개는 그대로)                                             |
| 객체  | `suumo/raw/2026-11-13/tokyo_23ku_all.csv`, 20,419,749 bytes, 로컬 파일과 크기 일치 |
| 재실행 | 버킷과 파일 모두 건너뜀                                                             |


실험 `ch07-suumo` 는 A 단계에서 첫 run 을 만들 때 `experiment_name` 으로 넘기면 자동으로 생긴다.

## 3. A 단계: 값과 경로 전달 (7.2.1 ~ 7.2.2)

컴포넌트 세 개로 통합 CSV 에서 구 하나의 매물을 꺼내고, 건수를 세고, 결과 문자열을 만든다.

![A 단계: 값과 경로 전달. export_ward(ward: str) 가 Output[Artifact] 디렉터리 경로로 CSV 를 넘기고, count_rows 가 int 값을 반환하고, output_result 가 str 값을 반환해 Rows: 3565 같은 결과가 나온다.](lab-a-flow.svg)


| 순서  | 컴포넌트                     | 하는 일                                                                                         | 다음으로 넘기는 것                                                      |
| --- | ------------------------ | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 1   | `export_ward(ward="港区")` | Pod 하나가 떠서 S3 호환 버킷에서 `tokyo_23ku_all.csv` 를 읽고, 구(区)가 미나토구(港区)인 행만 골라 `listings.csv` 로 저장한다 | **파일**. KFP 가 이 파일을 `mlpipeline` 버킷에 올리고, 다음 컴포넌트에는 그 경로만 알려 준다 |
| 2   | `count_rows(csv_dir)`    | 새 Pod 가 뜬다. KFP 가 앞의 파일을 내려받아 경로를 넘겨 주고, 컴포넌트는 그 파일의 행 수를 센다                                 | **값**. 정수 `3565` 를 반환하면 KFP 가 숫자 자체를 넘긴다                        |
| 3   | `output_result(count)`   | 또 새 Pod. `3565` 를 받아 `"Rows: 3565"` 문자열을 만든다                                                 | 끝                                                               |


확인할 것은 세 가지이다.

- `count_rows` 의 Input Artifacts 에 앞 컴포넌트의 출력 URI 가 보인다.
- 아티팩트는 `outputs["output_csv"]` 로, 반환값은 `.output` 으로 꺼낸다.
- KFP 는 경로만 넘겨 주므로 출력 디렉터리는 컴포넌트가 직접 만든다.

### 3.1 실행 결과

코드는 `MLOps-study` 저장소의 `k8s/kubeflow-pipelines/07-suumo/a_values_paths.py` 이다. 공통 설정 `common.py` 의 `with_s3()` 가 `export_ward` 에 Secret `rustfs-credentials` 를 env 로 넣고, 세 태스크 모두 amd64 노드에만 올린다. 맥에서 SDK 2.17.3 으로 컴파일해 KFP 에 실험 `ch07-suumo` 로 제출했다.

```terminal {title="개발 PC: A 단계 제출"}
$ python a_values_paths.py
$ KFP_HOST=http://192.168.0.242 python submit.py a_values_paths.yaml suumo-a-minato
run_id=85bca7b4-5ef5-4016-bbd8-449eac6def92 FINAL=SUCCEEDED took=91s
--- 로그 ([ch07] / Error 줄만) ---
[ch07] total=32593 ward=港区 rows=3565 -> /minio/mlpipeline/v2/artifacts/suumo-a-values-paths/<run_id>/export-ward/<uuid>/output_csv/listings.csv
[ch07] rows=3565
[ch07] Rows: 3565
```

| 컴포넌트 | 시간 | 결과 |
| --- | --- | --- |
| `export_ward` | 21초 | 32,593행 중 미나토구(港区) 3,565행을 `listings.csv` 로 썼다 |
| `count_rows` | 20초 | 그 파일을 받아 `3565` 를 반환했다 |
| `output_result` | 10초 | `3565` 를 받아 `"Rows: 3565"` 를 만들었다 |

Pod 7개(driver 4개, 실행 3개)는 모두 worker1-gpu 에 떴다.

`count_rows` 의 Input Artifacts 에는 앞 컴포넌트가 쓴 디렉터리의 URI 가 보이고, 반환한 `3565` 는 Output Parameters 에 값으로 보인다.

![KFP UI 2.17.3 의 run suumo-a-minato 에서 count-rows 태스크의 Input/Output 탭. Input Artifacts 의 csv_dir 은 minio://mlpipeline/v2/artifacts/suumo-a-values-paths/<run_id>/export-ward/<uuid>/output_csv 디렉터리 URI 이고, 1 file(s) 인 디렉터리 아티팩트로 표시된다. Output Parameters 의 Output 은 3565 이다.](run-a-count-rows.jpg)

`output_result` 는 그 숫자를 Input Parameters 의 `count` 로 받는다. 파일 경로가 아니라 값 그대로다.

![KFP UI 의 같은 run 에서 output-result 태스크의 Input/Output 탭. Input Parameters 의 count 는 3565, Output Parameters 의 Output 은 "Rows: 3565" 이다. Output Artifacts 에는 실행 로그 executor-logs 만 있다.](run-a-output-result.jpg)

버킷(`mlpipeline`)에 남은 것을 보면 두 방식의 차이가 그대로 드러난다.

| 파일 | 크기 | 의미 |
| --- | --- | --- |
| `export-ward/.../output_csv/listings.csv` | 2,294,487 bytes | 경로로 넘긴 파일. 다음 컴포넌트는 이 위치를 받았다 |
| 태스크별 `executor-logs-0` 3개 | 약 2 ~ 3KB | 실행 로그 |

`3565` 는 버킷에 파일로 남지 않는다. 값으로 넘긴 것은 파일이 아니라 숫자 자체로 전달된다.

## 4. B 단계: 아티팩트 타입 8종 (7.2.3)

KFP 는 컴포넌트가 만든 결과물을 데이터셋, 모델, 지표, 리포트 같은 종류(아티팩트 타입)로 나눠 저장하고, 종류마다 UI 에서 다르게 보여 준다. 컴포넌트 세 개로 통합 CSV 에서 여덟 종류를 모두 만들어 본다.

![B 단계: 타입별 출력. prepare_dataset 이 S3 호환 버킷의 통합 CSV 를 읽고, prepare_dataset 은 Dataset 과 Artifact(config.json)를 낸다. fit_baseline 이 Model 을, evaluate_baseline 이 Metrics(MAE, MAPE), ClassificationMetrics(가격대 혼동 행렬), SlicedClassificationMetrics(구별 가격대 지표), HTML(오차 분포 리포트), Markdown(데이터 카드)를 낸다.](lab-b-types.svg)


| 순서  | 컴포넌트                | 하는 일                                                      | 만드는 결과물 (타입)                                                                                                                                                  |
| --- | ------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `prepare_dataset`   | 통합 CSV 를 읽어 중복을 빼고 정리한 매물 표를 저장한다. 행 수와 컬럼 목록을 메타데이터로 붙인다 | 정리한 매물 표 (`Dataset`)<br>분할 비율과 컬럼 목록 파일 (`Artifact`)                                                                                                          |
| 2   | `fit_baseline`      | 구(区)별 중앙 단가 표를 만든다. "이 구면 m²당 얼마" 로 찍는 가장 단순한 예측기다        | 기준선 모델 (`Model`)                                                                                                                                              |
| 3   | `evaluate_baseline` | 기준선으로 가격을 찍어 보고 얼마나 틀리는지 잰다                               | 오차 수치 MAE, MAPE (`Metrics`)<br>가격대 혼동 행렬 (`ClassificationMetrics`)<br>구별 가격대 지표 (`SlicedClassificationMetrics`)<br>오차 분포 그래프 (`HTML`)<br>데이터 설명서 (`Markdown`) |


결과물 중 기준선 모델과 그 오차는 8장에서 학습한 모델이 "구별 중앙값으로 찍는 것보다 얼마나 나은지" 비교하는 기준이 된다. 혼동 행렬 두 개는 회귀 문제에는 필요 없지만, 그 타입이 UI 에서 어떻게 보이는지 확인하려고 가격을 4구간으로 나눠 만든다.

> **핸즈온ML 보강**: [RMSE와 MAE](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#rmse-mae) · [서브셋별 오차 분석](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#error-analysis)

확인할 것은 두 가지이다.

- UI 의 Visualization 탭에서 타입마다 보이는 방식(표, 그래프, 문서)이 다르다.
- `Metrics` 계열은 파일 없이 MLMD 에만 남는다. S3 호환 버킷에 해당 파일이 없는 것으로 확인한다.

### 4.1 실행 결과

코드는 `07-suumo/b_artifact_types.py` 이다. A 단계와 같은 방식으로 컴파일해 실험 `ch07-suumo` 에 제출했다.

```terminal {title="개발 PC: B 단계 제출"}
$ python b_artifact_types.py
$ KFP_HOST=http://192.168.0.242 python submit.py b_artifact_types.yaml suumo-b-types
run_id=860190a3-d8a6-40a7-a981-552cec48bec7 FINAL=SUCCEEDED took=101s
--- 로그 ([ch07] / Error 줄만) ---
[ch07] raw=32593 dedup=24131
[ch07] wards=23
[ch07] MAE=3885.5 MAPE=32.29%
```

| 컴포넌트 | 시간 | 결과 |
| --- | --- | --- |
| `prepare_dataset` | 20초 | 32,593행에서 중복을 빼 24,131행. `Dataset` 메타데이터에 행 수와 컬럼 목록을 붙였다 |
| `fit_baseline` | 20초 | 23개 구(区)의 m²당 중앙 단가 표 |
| `evaluate_baseline` | 20초 | 기준선 MAE 3,886만엔, MAPE 32.3%, 오차 중앙값 25.2% |

그래프에는 컴포넌트 3개와 아티팩트 9개가 이어진다. `prepare_dataset` 의 `dataset` 은 두 컴포넌트가 함께 받는다.

![KFP UI 의 run suumo-b-types 그래프. prepare-dataset 에서 config 와 dataset 이 나오고, dataset 은 fit-baseline 과 evaluate-baseline 으로 함께 들어간다. fit-baseline 에서 model 이 나와 evaluate-baseline 으로 들어가고, evaluate-baseline 에서 cls_metrics, data_card, error_report, metrics, sliced_metrics 가 나온다. 세 태스크 모두 성공 표시다.](run-b-graph.jpg)

타입마다 Visualization 탭이 다르게 그린다.

| 타입 | 아티팩트 | UI 에 보이는 모습 |
| --- | --- | --- |
| `Metrics` | `metrics` | 이름과 값의 표 (Scalar Metrics) |
| `ClassificationMetrics` | `cls_metrics` | 색으로 칠한 혼동 행렬 |
| `Markdown` | `data_card` | 렌더링된 문서 |
| `HTML` | `error_report` | 페이지를 그대로 띄운 화면 |
| `SlicedClassificationMetrics` | `sliced_metrics` | 그리지 않는다. "There is no metrics artifact available in this step" |
| `Dataset`, `Model`, `Artifact` | `dataset`, `model`, `config` | 그리지 않고 URI 와 정보만 보인다 |

![KFP UI 에서 metrics 아티팩트의 Visualization 탭. Scalar Metrics 표에 mae_man_yen 3885.5, mape_pct 32.29, median_ape_pct 25.21, rows 24131 이 있다.](run-b-metrics.jpg)

![KFP UI 에서 cls_metrics 아티팩트의 Visualization 탭. 가격 4분위 Q1 ~ Q4 의 4 × 4 혼동 행렬이 파란 색조로 칠해져 있다. 대각선 값은 Q1 3425, Q2 3205, Q3 3470, Q4 3789 이다.](run-b-confusion.jpg)

![KFP UI 에서 data_card 아티팩트의 Visualization 탭. Static Markdown 으로 SUUMO 도쿄 23구 중고 맨션 데이터 카드가 렌더링돼 있다. 행 수 24,131, 구 수 23, 가격 중앙값 8,580 만엔, 단가 중앙값 147.5 만엔/m², 수집일 2026-11-13 과 기준선 MAE, MAPE 표가 보인다.](run-b-data-card.jpg)

![KFP UI 에서 error_report 아티팩트의 Visualization 탭. Static HTML 로 기준선 오차 분포 페이지가 보인다. 절대 백분율 오차 구간별 건수와, 구별 오차 중앙값을 막대로 그린 표가 있다. 주오구(中央区) 16.9% 가 가장 작다.](run-b-html.jpg)

`SlicedClassificationMetrics` 는 구마다 `ClassificationMetrics` 로 혼동 행렬을 만들어 슬라이스 23개로 채웠다. UI 는 이 타입을 그리지 않지만, MLMD 에는 `evaluationSlices` 속성(14,297 bytes)으로 저장돼 있다.

S3 호환 버킷(`mlpipeline`)에 남은 파일은 이렇다.

| 아티팩트 | 크기 | 버킷에 파일이 있나 |
| --- | --- | --- |
| `dataset` (Parquet) | 1,025,393 bytes | 있다 |
| `config` | 516 bytes | 있다 |
| `model` | 622 bytes | 있다 |
| `error_report` | 3,009 bytes | 있다 |
| `data_card` | 306 bytes | 있다 |
| `metrics`, `cls_metrics`, `sliced_metrics` | | **없다**. 값은 MLMD 에만 있다 |

기준선 오차는 학습에 쓴 같은 데이터로 잰 값이라 실제 성능보다 낙관적이다. 초메(丁目) 단위로 나눈 데이터로 다시 재는 것은 8장에서 한다.

> **핸즈온ML 보강**: [데이터 스누핑 편향](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#data-snooping) · [k-폴드 교차 검증](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#cross-validation) · [테스트 세트로 평가](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#test-evaluation)

## 5. C 단계: 아티팩트로 잇는 파이프라인 (7.3.1)

통합 CSV 를 받아 train / validation / test 로 나누고, 검증 분할의 내용을 확인한다. 세 컴포넌트는 앞의 출력 파일을 뒤가 받는 방식(`Output[Dataset]`)으로 이어진다.

### 5.1 파이프라인 만들기

![C 단계: suumo-artifact-passing. download_dataset 이 Output[Dataset] 으로 CSV 를 넘기고, split_dataset(random_state=42)이 train_dataset, validation_dataset, test_dataset 세 개를 낸다. validation_dataset 만 output_file_contents 로 가서 파일 트리와 행 수를 로그로 남긴다. train 과 test 는 이후 학습과 평가에서 쓴다.](lab-c-pipeline.svg)


| 순서  | 컴포넌트                   | 하는 일                                                                   | 다음으로 넘기는 것                                                                          |
| --- | ---------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1   | `download_dataset`     | S3 호환 버킷에서 통합 CSV 를 내려받아 저장한다                                          | **파일**. 매물 CSV 의 경로                                                                 |
| 2   | `split_dataset`        | 행 단위로 75 / 15 / 10 무작위 분할한다(`train_test_split` 두 번, `random_state=42`) | **파일 세 개**. train, validation, test CSV 의 경로. **값**. train 과 test 에 함께 들어간 초메(丁目) 수 |
| 3   | `output_file_contents` | 검증 분할의 파일 목록, 행 수, 구(区)별 건수를 로그로 남긴다                                   | -                                                                                   |


컴포넌트는 처음부터 쓰지 않고, 평범한 스크립트에서 시작해 한 단계씩 옮긴다. 첫 컴포넌트인 `download_dataset` 을 예로 든다.

**1. 스크립트.** 

터미널에서 그냥 돌려 보는 코드다. S3 호환 버킷에서 CSV 를 내려받는다. 접속 키는 Secret 에서 env 로 주입되므로 코드에 적지 않는다.

```python
import boto3

s3 = boto3.client("s3", endpoint_url="http://rustfs.mlflow.svc:9000")
s3.download_file("datasets", "suumo/raw/2026-11-13/tokyo_23ku_all.csv", "listings.csv")
```

**2. 함수.**

 같은 코드를 함수 안으로 옮긴다. import 도 함수 안에 둔다. KFP 는 이 함수 본문만 잘라서 Pod 로 보내므로, 파일 맨 위의 import 는 따라가지 않는다.

```python
def download_dataset(output_path: str):
    import boto3

    s3 = boto3.client("s3", endpoint_url="http://rustfs.mlflow.svc:9000")
    s3.download_file("datasets", "suumo/raw/2026-11-13/tokyo_23ku_all.csv", output_path)
```

**3. 컴포넌트.**

 `@dsl.component` 를 붙이고, 출력 위치는 KFP 가 정해 주는 `Output[Dataset]` 으로 바꾼다. 이제 이 함수는 Pod 하나로 실행되고, `boto3` 는 Pod 가 뜰 때 설치된다.

```python
from kfp import dsl
from kfp.dsl import Dataset, Output


@dsl.component(base_image="python:3.11", packages_to_install=["boto3"])
def download_dataset(output_dataset: Output[Dataset]):
    import boto3

    s3 = boto3.client("s3", endpoint_url="http://rustfs.mlflow.svc:9000")
    s3.download_file("datasets", "suumo/raw/2026-11-13/tokyo_23ku_all.csv", output_dataset.path)
```

**4. 컴포넌트 하나짜리 파이프라인.** 

컴포넌트가 준비되면 이것 하나만 넣은 파이프라인을 먼저 컴파일한다.

```python
from kfp import compiler


@dsl.pipeline(name="suumo-download-only")
def pipeline():
    download_dataset()


compiler.Compiler().compile(pipeline, "download_only.yaml")
```

클러스터의 KFP 와 같은 SDK 2.17.3 으로 컴파일하면 59줄짜리 YAML 이 나온다. 컴포넌트가 Pod 에서 어떻게 실행되는지는 `deploymentSpec` 에 다 들어 있다(일부 줄임).

```yaml {title="download_only.yaml"}
deploymentSpec:
  executors:
    exec-download-dataset:
      container:
        command:
        - sh
        - -c
        - "... python3 -m pip install --quiet --no-warn-script-location 'boto3' && \
           python3 -m pip install --quiet --no-warn-script-location 'kfp==2.17.3' ..."
        - sh
        - -ec
        - 'program_path=$(mktemp -d)
          printf "%s" "$0" > "$program_path/ephemeral_component.py"
          _KFP_RUNTIME=true python3 -m kfp.dsl.executor_main ...'
        - "\nimport kfp\nfrom kfp import dsl\nfrom kfp.dsl import *\nfrom typing import *\n\n
           def download_dataset(output_dataset: Output[Dataset]):\n    import boto3\n ..."
        image: python:3.11
```

- `image: python:3.11` 위에서 Pod 가 뜬다.
- 첫 번째 명령이 `packages_to_install` 의 `boto3` 와 `kfp` 를 **실행할 때마다** 설치한다.
- 함수 본문이 **문자열로 통째로** 들어가 있고, Pod 는 이것을 임시 파일 `ephemeral_component.py` 로 써서 실행한다. 맨 앞에 붙는 import 는 `kfp` 관련뿐이라, `boto3` 를 함수 안에서 import 해야 하는 이유가 여기서 보인다.

**5. 전체 파이프라인.**

 분할과 확인 컴포넌트를 붙인다. 앞 컴포넌트의 출력을 뒤 컴포넌트의 입력으로 넘기면 KFP 가 실행 순서를 알아서 정한다.

```python
@dsl.pipeline(name="suumo-artifact-passing")
def pipeline(random_state: int = 42):
    download_op = download_dataset()
    split_op = split_dataset(
        random_state=random_state,
        input_dataset=download_op.outputs["output_dataset"],
    )
    output_file_contents(dataset=split_op.outputs["validation_dataset"])
```

`split_dataset` 이 분할하면서 **train 과 test 에 함께 들어간 초메(丁目) 수**를 세어 반환한다. 이 숫자가 D 단계에서 분할 방식을 바꾸는 근거가 된다. 분할된 파일은 경로로, 이 숫자는 값으로 넘어간다.

```python
@dsl.component(base_image="python:3.11", packages_to_install=["pandas", "scikit-learn"])
def split_dataset(
    random_state: int,
    input_dataset: Input[Dataset],
    train_dataset: Output[Dataset],
    validation_dataset: Output[Dataset],
    test_dataset: Output[Dataset],
) -> int:
    ...
    # 주소에서 번지를 떼어 초메(丁目)까지를 키로 쓴다
    key = lambda df: set(df["住所"].str.replace(r"-.*$", "", regex=True))
    overlap = len(key(train) & key(test))
    print(f"train 과 test 에 함께 들어간 초메: {overlap}")
    return overlap
```

키는 매물 하나를 가리키는 ID 가 아니라 같은 초메(丁目)의 매물을 한 묶음으로 보는 그룹 키이다. 미리 재 보니 키는 2,694종이고 키 하나에 매물이 중앙값 6건 있다. 무작위로 나누면 test 매물의 97.9% 가 같은 초메의 이웃 매물을 train 에서 이미 본 상태로 평가받는다.

### 5.2 UI 로 올리고 실행하기

이 단계는 웹 UI 로 실행한다. Upload pipeline 으로 YAML 을 올리고, Experiment 를 고르고, Run 을 만든다.

- 파이프라인 함수의 인자 `random_state=42` 가 Run 생성 화면에 채워져 있는지 확인한다.
- 그래프에서 컴포넌트 사이의 연결선이 데이터 의존성과 일치하는지 본다.
- 실행 중 로그 탭에서 컴포넌트가 출력한 진행 상황을 본다.

### 5.3 실행 결과

코드는 `07-suumo/c_artifact_passing.py` 이다. 맥에서 컴파일한 `c_artifact_passing.yaml` 을 Pipelines 화면의 Upload pipeline 으로 올려 파이프라인 `suumo-artifact-passing` 을 등록했다.

![KFP UI 의 New Pipeline 화면. Create a new pipeline 이 선택돼 있고, Pipeline Name 은 suumo-artifact-passing, Pipeline Description 은 "C 단계: 다운로드 → 분할 → 확인을 Output[Dataset] 으로 잇는다", Upload a file 에 c_artifact_passing.yaml 이 들어가 있다.](run-c-upload.jpg)

등록한 파이프라인의 Create run 에서 실험 `ch07-suumo` 를 골랐다. 파이프라인 함수의 인자 `random_state` 는 기본값 `42` 로 이미 채워져 있다.

![KFP UI 의 Start a new run 화면. Pipeline 과 Pipeline Version 은 suumo-artifact-passing, Run name 은 suumo-c-ui, Experiment 는 ch07-suumo, Run Type 은 One-off 이고, Run parameters 의 random_state - integer 칸에 42 가 채워져 있다.](run-c-create-run.jpg)

Start 를 누르면 run 이 시작되고, 그래프의 노드가 차례로 성공으로 바뀐다. 연결선은 코드에서 출력을 입력으로 넘긴 관계 그대로다.

![KFP UI 의 run suumo-c-ui 그래프. download-dataset 에서 output_dataset 이 나와 split-dataset 으로 들어가고, split-dataset 에서 test_dataset, train_dataset, validation_dataset 이 나온다. validation_dataset 은 output-file-contents 로 이어진다. download-dataset 과 split-dataset 에 성공 표시가 있다.](run-c-graph.jpg)

| 컴포넌트 | 시간 | 결과 |
| --- | --- | --- |
| `download_dataset` | 20초 | 버킷의 CSV 를 `output_dataset` 경로로 내려받았다 |
| `split_dataset` | 31초 | 32,593행을 train 24,444 / validation 4,889 / test 3,260 으로 나눴다. 반환값 `1327` |
| `output_file_contents` | 20초 | 검증 분할 4,889행. 구(区)별로는 미나토구(港区) 555, 고토구(江東区) 364, 주오구(中央区) 346 순 |

run 전체는 112초가 걸렸고, Pod 7개는 모두 worker1-gpu 에 떴다.

`split_dataset` 의 Input/Output 탭에서 A 단계의 두 전달 방식이 한 화면에 함께 보인다. 입력 `random_state` 는 값, 입력 `input_dataset` 은 앞 컴포넌트의 경로, 출력 `Output` 은 값이다.

![KFP UI 에서 split-dataset 태스크의 Input/Output 탭. Input Parameters 의 random_state 는 42, Input Artifacts 의 input_dataset 은 download-dataset 의 output_dataset URI 이고 미리보기에 区コード,区名,物件ID 로 시작하는 CSV 헤더가 보인다. Output Parameters 의 Output 은 1327 이다.](run-c-split.jpg)

```terminal {title="split-dataset 로그"}
[ch07] rows total=32593 train=24444 val=4889 test=3260
[ch07] train 과 test 에 함께 들어간 초메: 1327 / test 초메 1378, test 매물 중 같은 초메가 train 에 있는 비율 98.3%
```

test 에 나온 초메(丁目) 1,378개 중 1,327개가 train 에도 있다. test 매물로 따지면 **98.3%** 가 같은 동네의 이웃 매물을 train 에서 이미 본 상태로 평가받는다. 무작위 분할로는 처음 보는 주소에 대한 성능을 잴 수 없다는 뜻이고, D 단계에서 초메 단위로 나누는 근거가 이 숫자다.

> **핸즈온ML 보강**: [테스트 세트 만들기](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#test-set) · [시드와 해시 기반 분할](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#hash-split) · [계층적 샘플링](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#stratified)

## 6. D 단계: 고정 경로로 잇는 파이프라인 (7.3.2)

본 파이프라인 구조 

- 매물 CSV 와 좌표 데이터를 Parquet으로 변경 및 정제
- 주소에 좌표를 추가
- 초메(丁目) 단위로 나누어서 S3 호환 버킷에 적재
- 다시 S3 호환 버킷에서 읽어서 검사

### 6.1 파이프라인

컴포넌트는 아홉 종류이고, `csv_to_parquet` 과 `put_to_minio` 는 입력만 바꿔 두 번 쓴다.

![D 단계: suumo-data-prep. 왼쪽 열: download_raw(버킷의 통합 CSV) → csv_to_parquet(utf-8-sig) → clean_dedup → geocode → split_dataset(丁目 그룹 75/15/10) → put_to_minio u2(train/val/test) → qa_data. 오른쪽 열: download_geo(位置参照情報 zip) → unzip_data → csv_to_parquet-2(cp932) → put_to_minio u1(chome.parquet). csv_to_parquet-2 의 출력은 geocode 에도 들어간다. split_dataset 은 eda_report 로도 간다. qa_data 는 u1, u2 가 모두 끝난 뒤 .after(u1, u2) 로 실행되며 고정 경로에서 읽는다.](lab-d-pipeline.svg)


| 순서  | 컴포넌트                | 하는 일                                                                                                     |
| --- | ------------------- | -------------------------------------------------------------------------------------------------------- |
| 1   | `download_raw`      | S3 호환 버킷의 통합 CSV 를 내려받는다                                                                                |
| 2   | `csv_to_parquet`    | 매물 CSV 를 Parquet 으로 바꾼다                                                                                  |
| 3   | `download_geo`      | 위치참조정보(位置参照情報) zip 을 공개 URL 에서 내려받는다                                                                     |
| 4   | `unzip_data`        | zip 에서 좌표 CSV 하나를 꺼낸다                                                                                    |
| 5   | `csv_to_parquet-2`  | 좌표 CSV 를 Parquet 으로 바꾼다. Shift\_JIS 라 `encoding` 인자를 준다                                                  |
| 6   | `put_to_minio` (u1) | 좌표 Parquet 을 고정 경로에 올린다                                                                                  |
| 7   | `clean_dedup`       | 중복과 이상값을 걸러낸다                                                                                            |
| 8   | `geocode`           | 주소에 위도, 경도, 초메(丁目) 키를 붙인다                                                                                |
| 9   | `split_dataset`     | 초메(丁目) 단위로 train / validation / test 를 나눈다                                                               |
| 10  | `put_to_minio` (u2) | 세 분할을 고정 경로에 올린다. 접속 키는 Secret 에서 받는다                                                                    |
| 11  | `qa_data`           | 버킷에 올라간 파일을 다시 읽어 8장에서 쓸 수 있는지 7가지를 검사한다. 하나라도 틀리면 파이프라인을 실패시키고, 결과는 검사표(`Markdown`)와 숫자(`Metrics`)로 남긴다 |
| 12  | `eda_report`        | train 분할로 구(区)별 단가 분포를 `HTML` 로 낸다                                                                       |


모든 태스크에 `set_caching_options(False)` 를 두어 매번 새로 실행한다. `qa_data` 는 아티팩트를 입력으로 받지 않고 고정 경로에서 읽으므로 KFP 가 순서를 알 수 없다. 그래서 `.after(u1, u2)` 로 두 업로드가 모두 끝난 뒤에 실행되도록 직접 지정한다.

> **핸즈온ML 보강**: [컴포넌트와 데이터 파이프라인](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#data-pipeline) · [사이킷런 Pipeline과 KFP 파이프라인](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#sklearn-pipeline)

### 6.2 Parquet 변환

표 데이터는 CSV 대신 Parquet 으로 저장한다. 열 단위로 저장해 필요한 열만 읽을 수 있고, 압축되어 파일이 작고, 열 타입이 함께 저장된다. 변환 전후의 파일 크기와 읽기 시간을 재서 비교한다. 엔진은 `pyarrow` 하나로 고정하고 `index=False` 로 쓴다.

### 6.3 정제와 중복 제거

![clean_dedup 처리 순서. 원본 32,593행 → 사용할 컬럼 15개만 남김 → 같은 매물 중복 제거(物件名, 住所, 価格, 面積, 所在階 기준) → 약 24,131행 → 준공 2027년 이후 매물 제외 → 構造 57종을 RC/SRC/S/기타로 정리 → 築年数 제거, 築年만 유지 → unit_price 추가(価格_万円 / 専有面積_m2) → 같은 구 중앙 단가의 10배를 넘는 가격 오류 제외 → 24,117행.](clean-dedup-steps.svg)

38열 중 남기는 것은 15열이다.


| 역할        | 컬럼                                                                 | 쓰임                                     |
| --------- | ------------------------------------------------------------------ | -------------------------------------- |
| **타깃**    | 가격\_만엔(`価格_万円`)                                                    | 맞힐 값. 면적으로 나눠 m²당 단가로 바꾼다              |
| **필수 입력** | 전용 면적(`専有面積_m2`), 방 구조(`間取り`), 준공 연도(`築年`), 소재 층(`所在階_階`)          | 사용자가 꼭 넣는 조건                           |
| **위치**    | 주소(`住所`), 구(`区名`)                                                  | 주소는 지오코딩으로 좌표가 되고, 구는 좌표를 못 찾았을 때와 분석용 |
| **선택 입력** | 총 층수(`総階数`), 구조(`構造`), 가장 가까운 역(`最寄駅`), 최단 도보 분(`最短徒歩分`), 방향(`向き`) | 사용자가 몰라도 되는 조건. 비어 있어도 학습한다            |
| **보조**    | 준공 월(`築月`)                                                         | 준공 연도와 함께 건물 나이를 월 단위로 계산할 때           |
| **관리용**   | 물건 ID(`物件ID`), 물건명(`物件名`)                                          | 모델에는 넣지 않는다. ID 는 행 추적, 물건명은 중복 제거 키   |


버리는 23열은 숫자로 바꾼 파싱 열이 따로 있는 원문 열(`価格`, `専有面積` 등), 사용자가 모르는 값(관리비, 수선적립금, 총 호수), 수집 관리용 열(URL, 갱신 일시)이다.

건물 연식(`築年数`)는 수집 연도에 따라 달라지는 파생값이므로 버리고 준공 연도(`築年`)만 둔다. 층, 구조, 방향이 빈 행은 지우지 않는다. 서빙 때도 선택 입력이므로 결측 그대로 학습시킨다.

가격 입력 오류도 여기서 걸러낸다. 같은 구(区)의 m²당 중앙 단가보다 **10배를 넘게 비싼 매물**은 사이트에 가격이 잘못 올라온 것으로 보고 제외한다. 6.6 의 검사에서 찾은 2건이 이 기준에 걸리고, 도심 신축 고급 맨션(중앙 단가의 5 ~ 6배)은 남는다.

> **핸즈온ML 보강**: [결측치 처리(SimpleImputer)](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#imputer) · [범주형 특성 인코딩](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#categorical) · [특성 조합](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#feature-combo)

### 6.4 주소 정규화와 지오코딩

좌표 데이터의 동과 초메 이름(町丁目名)은 소토칸다 3초메(`外神田三丁目`)처럼 한자 숫자를 쓰고, 매물 주소는 소토칸다 3(`外神田３`)처럼 전각 숫자를 쓴다. 그래서 양쪽 표기를 맞춘 뒤 조인한다.

매물 주소에 적용하는 정규화는 세 가지이다.


| 규칙          | 하는 일                                                                    | 예                      |
| ----------- | ----------------------------------------------------------------------- | ---------------------- |
| NFKC 정규화    | 유니코드 표준 정규화로, 모양만 다른 같은 글자를 하나로 맞춘다. 전각 숫자와 영문은 반각으로, 반각 가타카나는 전각으로 바뀐다 | `外神田３` → `外神田3`        |
| `ヶ` 를 `ケ` 로 | 작은 `ヶ` 와 큰 `ケ` 를 섞어 쓰는 지명을 한쪽으로 맞춘다. 좌표 데이터 쪽에도 같은 규칙을 적용한다             | `千駄ヶ谷` → `千駄ケ谷`        |
| 구분자 통일      | 번지 사이의 `‐`, `ー`, `−`, `.` 와 `7番13号` 같은 표기를 `-` 하나로 맞춘다                  | `明石町7番13号` → `明石町7-13` |


정규화한 주소를 구(区), 동(町名), 초메 번호로 나누고, 초메 번호는 한자 숫자로 바꿔(`3` → `三丁目`) 좌표 데이터와 조인한다.

![geocode 처리 흐름. 도쿄도 치요다구 소토칸다 3(東京都千代田区外神田３) → NFKC 정규화(ヶ를 ケ로, 구분자 통일) → 구/동/초메(区/町名/丁目) 분해(치요다구/소토칸다/3(千代田区/外神田/3)) → 초메(丁目) 일치? 예(93.2%)면 초메(丁目) 좌표, 아니오면 동 이름(町名) 일치? 예(6.8%)면 동(町) 좌표, 아니오면 제외하고 건수를 Metrics 에 기록. 좌표가 붙으면 lat, lon, chome_key, geo_level 컬럼을 추가한다.](geocode-flow.svg)

정규화 규칙 세 가지를 적용하면 32,593건 중 32,592건이 매칭된다. `ヶ` 표기 통일이 없으면 시부야구(渋谷区)의 센다가야(千駄ヶ谷), 토미가야(富ヶ谷), 하타가야(幡ヶ谷) 253건이 빠진다.

동(町名)까지도 맞지 않으면 구(区) 좌표로 대신하지 않고 버린다. 구 하나가 넓어 엉뚱한 이웃과 묶이기 때문이다. 이렇게 버려지는 행은 1건이다. 동까지만 맞은 6.8% 는 버리지 않고 동의 좌표를 쓰되, `geo_level` 컬럼에 초메인지 동인지 남겨 둔다.

> **핸즈온ML 보강**: [지리적 산점도](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#geo-scatter) · [군집 유사도 변환기(ClusterSimilarity)](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#custom-transformer)

### 6.5 초메(丁目) 그룹 분할

C 단계의 무작위 분할은 같은 초메(丁目)의 이웃 매물을 train 과 test 에 함께 넣는다. 처음 보는 주소에 대한 성능을 재려면 초메(丁目) 단위로 묶어서 나눠야 한다.

![무작위 분할과 초메(丁目) 그룹 분할. C 단계의 무작위 분할은 소토칸다 3(外神田3) 의 매물 A 를 train, 매물 B 를 test 에 넣어 같은 초메(丁目) 가 양쪽에 들어간다. D 단계의 초메(丁目) 그룹 분할은 소토칸다 3(外神田3) 의 매물 A 와 B 를 모두 train 에, 타카나와 3(高輪3) 의 매물 C 를 test 에 넣는다.](split-random-vs-group.svg)

`chome_key` 를 그룹으로 `GroupShuffleSplit` 을 두 번 적용한다. 출력은 **폴더 하나에 Parquet 세 개**를 담는다. 그룹 단위로 나누면 행 비율이 정확히 떨어지지 않으므로 QA 기준에 ±2%p 여유를 둔다.

> **핸즈온ML 보강**: [계층적 샘플링](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#stratified) · [해시 기반 분할](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#hash-split)

### 6.6 업로드와 QA

**업로드 (`put_to_minio`)**

- 앞 단계가 만든 파일을 S3 호환 버킷의 고정 경로(`datasets/suumo/prepared/2026-11-13/`)에 올린다.
- 두 번 쓴다. u1 은 좌표 파일 하나를, u2 는 train / val / test 세 파일이 든 폴더를 올린다.
- 입력이 폴더이면 안의 파일을 모두 올리고, 파일 하나이면 `upload_file_name` 으로 정한 이름으로 올린다.
- 이름을 따로 받는 이유는 KFP 가 아티팩트 파일 이름을 `output_path` 같은 값으로 자동으로 붙이기 때문이다.

![qa_data 가 읽는 고정 경로와 검사. datasets/suumo/prepared/2026-11-13/ 의 train.parquet, val.parquet, test.parquet, chome.parquet 를 pyarrow fs.S3FileSystem 으로 읽어 검사 7개를 한다: 파일 4개 존재, 분할 간 chome_key 중복 0, 분할 간 물건 ID(物件ID) 중복 0, 행 비율 75/15/10 ±2%p, 좌표 결측 0, 같은 구 중앙 단가의 10배 이하, 23구가 모든 분할에 존재. 모두 통과하면 Markdown 리포트와 Metrics 를 기록하고, 아니면 태스크가 실패한다.](qa-gate.svg)

**검사 (`qa_data`)**

- 업로드가 끝난 뒤 고정 경로에서 파일 네 개를 다시 읽는다. 8장이 읽을 바로 그 파일이다.
- 일곱 가지를 검사한다. 파일 존재, 분할 간 초메(丁目) 중복 0, 분할 간 매물 중복 0, 비율 75 / 15 / 10 ±2%p, 좌표 결측 0, 같은 구 중앙 단가의 10배를 넘는 매물이 남아 있지 않은지, 23개 구(区)가 모든 분할에 있는지.
- 하나라도 틀리면 태스크가 실패해 파이프라인 전체가 실패로 표시된다.
- 결과는 검사표(`Markdown`)와 행 수, 매칭률 같은 숫자(`Metrics`)로 남긴다.

**검사로 잡은 데이터 오류.** 이 검사를 노트북에서 먼저 돌려 보다가, 매물 사이트에 **가격이 실제의 10배로 올라온 매물 2건**을 찾았다.

| 매물 | 표시 가격 | 단가 | 같은 구(区) 보통 단가 대비 |
| --- | --- | --- | --- |
| 고토구(江東区), 2007년 준공, 76m² | 14억 9,800만엔 | 1,961만엔/m² | 약 14배 |
| 시나가와구(品川区), 2003년 준공, 58m² | 13억 7,000만엔 | 2,358만엔/m² | 약 13배 |

- 크롤러가 잘못 읽은 것이 아니라 사이트의 가격 칸 자체가 이 값이었다.
- 고토구 건은 다른 부동산 사이트의 같은 건물 시세(단가 146 ~ 479만엔/m², 현재 매물 1억 ~ 2억엔대)와 비교해 오류를 확인했다. 0 을 하나 빼면 1억 4,980만엔, 단가 196만엔/m² 로 시세 범위 안에 들어온다.
- 처음 정한 검사 기준(단가 10 ~ 2,000만엔/m²)으로는 시나가와구 건만 걸리고 고토구 건은 통과했다. 그래서 고정 범위 대신 **같은 구 보통 단가의 10배를 넘으면 오류로 보고 제외**하는 규칙으로 바꿨다. 이 기준이면 두 건만 빠지고, 도심 신축 고급 맨션(보통 단가의 5 ~ 6배)은 남는다.

같은 기준을 정제 규칙(6.3)에도 넣어, 정제에서 지우고 검사에서 남아 있지 않은지 다시 확인한다.

노트북에서 이 기준을 넣고 다시 돌린 결과는 이렇다.

| 단계 | 행 수 |
| --- | --- |
| 원본 | 32,593 |
| 중복 제거 | 24,131 |
| 준공 2027년 이후 제외 | 24,119 |
| 가격 오류 제외 (구 중앙 단가 10배 초과) | **24,117** (위 2건, 각각 14.1배와 13.1배) |
| 지오코딩 매칭 | 24,116 (초메 22,496, 동 1,620) |
| 초메 그룹 분할 | train 17,803 (73.8%) / val 3,878 (16.1%) / test 2,435 (10.1%) |

검사 7개가 모두 통과했고, 남은 매물의 단가는 18.5 ~ 1,487.2만엔/m² 이다.

**탐색 리포트 (`eda_report`)**

- train 분할만 읽는다. validation, test 를 보고 판단을 바꾸면 평가가 낙관적이 되기 때문이다.
- 구(区)별 단가 분포와 준공 연도(築年)에 따른 단가 변화를 그래프로 그려 `HTML` 로 남긴다.
- 검사와 달리 통과·실패가 없는 참고용 결과물이다.

> **핸즈온ML 보강**: [데이터 스누핑 편향](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#data-snooping) · [탐색과 시각화](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#explore) · [특성 조합](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#feature-combo)

### 6.7 SDK 로 등록하고 실행하기

이 단계는 UI 대신 Python SDK 로 올린다. KFP 2.17.3 에서 `upload_pipeline(..., pipeline_name=...)` 으로 등록하고, 등록된 버전으로 run 을 만든다.

- 등록한 파이프라인이 Pipelines 메뉴에 보이는지 확인한다.
- `create_run_from_pipeline_package` 로 만든 일회성 run 은 Pipelines 메뉴에 남지 않는 것과 비교한다.
- 3주차에 띄운 Kubeflow 노트북에서 `kfp.Client()` 를 인자 없이 불러 같은 작업을 해 본다.

### 6.8 실행 결과

코드는 `07-suumo/d_data_prep.py`, 등록과 실행은 `run_registered.py` 이다. 컴포넌트 로직은 노트북에서 숫자를 맞춘 코드를 그대로 옮겼다. 원본 CSV 는 `dsl.importer` 대신 `download_raw` 컴포넌트가 Secret 을 env 로 받아 내려받는다. importer 는 파이프라인 루트가 아닌 버킷의 접속 정보를 다음 컴포넌트에 넘겨 주지 않기 때문이다.

```terminal {title="개발 PC: D 단계 등록과 실행"}
$ python d_data_prep.py
$ KFP_HOST=http://192.168.0.242 python run_registered.py d_data_prep.yaml suumo-data-prep suumo-d-registered
pipeline_id=d16c9093-... version_id=fc96ca84-... experiment_id=9d1ac70c-...
run_id=14046c7a-6957-4e2d-8e21-478a86093dd6 FINAL=SUCCEEDED took=232s
```

`upload_pipeline` 으로 등록한 `suumo-data-prep` 은 C 단계의 `suumo-artifact-passing` 과 함께 Pipelines 목록에 남는다. A, B 처럼 `create_run_from_pipeline_package` 로 만든 일회성 run 은 이 목록에 없다.

![KFP UI 의 Pipelines 목록. suumo-data-prep 과 suumo-artifact-passing 두 파이프라인이 2026-11-14 에 올라와 있고, 그 아래 기본 튜토리얼 파이프라인 두 개가 있다.](run-d-pipelines.jpg)

그래프에는 컴포넌트 12개가 두 줄기로 나뉘었다가 `geocode` 에서 합쳐진다. `qa_data` 는 두 `put_to_minio` 가 모두 끝난 뒤에 실행된다.

![KFP UI 의 run suumo-d-registered 그래프. 왼쪽 줄기는 download-geo, unzip-data, csv-to-parquet-2 이고 put-to-minio 로 갈라진다. 오른쪽 줄기는 download-raw, csv-to-parquet, clean-dedup 이다. 두 줄기가 geocode 에서 합쳐지고, split-dataset 뒤에 put-to-minio-2 와 eda-report 가 이어지며, 맨 아래 qa-data 에서 report 와 metrics 가 나온다. 모든 태스크에 성공 표시가 있다.](run-d-graph.jpg)

| 컴포넌트 | 시간 | 결과 |
| --- | --- | --- |
| `download_raw` | 21초 | 원본 CSV 20,419,749 bytes |
| `download_geo`, `unzip_data` | 10초, 10초 | 위치참조정보(位置参照情報) zip 83KB 에서 좌표 CSV 하나 |
| `csv_to_parquet` ×2 | 20초씩 | 매물 32,593행, 좌표 5,390행 |
| `clean_dedup` | 20초 | 32,593 → 24,131 → 24,119 → **24,117** |
| `geocode` | 20초 | 24,116 매칭, 1건 제외 (초메 22,496, 동 1,620) |
| `split_dataset` | 31초 | train 17,803 / val 3,878 / test 2,435 |
| `put_to_minio` ×2 | 20초씩 | `chome.parquet` 와 `train / val / test.parquet` |
| `qa_data` | 20초 | 검사 7개 **모두 PASS** |
| `eda_report` | 20초 | train 분할만 읽은 구별·준공 연대별 단가 |

run 전체는 232초가 걸렸고, Pod 25개(driver 포함)는 모두 worker1-gpu 에 떴다.

정제 단계는 줄어드는 행 수를 `Metrics` 로 남긴다. 단계마다 몇 건이 빠졌는지 UI 에서 바로 보인다.

![KFP UI 에서 clean-dedup 의 metrics 아티팩트 Visualization. Scalar Metrics 표에 raw 32593, dedup 24131, year_filtered 24119, price_filtered 24117 이 있다.](run-d-clean-metrics.jpg)

`qa_data` 의 검사표는 `Markdown` 으로 남는다.

![KFP UI 에서 qa-data 의 report 아티팩트 Visualization. QA 결과: PASSED 아래에 대상 s3://datasets/suumo/prepared/2026-11-13/ 와 검사 일곱 개(파일 4개 존재, 분할 간 chome_key 중복 0, 분할 간 物件ID 중복 0, 행 비율 73.8% / 16.1% / 10.1%, 좌표 결측 0, 구 중앙 단가 10배 초과 0, 23구가 모든 분할에 23 / 23 / 23)가 모두 PASS 로 표시된다. 아래 표에 train 17,803행 1,824 초메, val 3,878행 364 초메, test 2,435행 244 초메가 있다.](run-d-qa.jpg)

`eda_report` 는 train 분할만 읽어 단가 분포를 `HTML` 로 낸다.

![KFP UI 에서 eda-report 의 report 아티팩트 Visualization. train 분할 탐색 17,803행 제목 아래 구별 m²당 중앙 단가 막대가 미나토구(港区) 291.7, 지요다구(千代田区) 261.0, 시부야구(渋谷区) 227.6, 주오구(中央区) 204.2, 시나가와구(品川区) 183.4 순으로 이어진다.](run-d-eda.jpg)

고정 경로에는 8장이 읽을 파일 네 개가 남았다.

```terminal {title="개발 PC: 고정 경로 확인"}
$ aws --endpoint-url $S3 s3 ls s3://datasets/suumo/prepared/2026-11-13/
2026-11-14 16:31:54     161991 chome.parquet
2026-11-14 16:33:25     136113 test.parquet
2026-11-14 16:33:25     886953 train.parquet
2026-11-14 16:33:25     202588 val.parquet
```

**노트북에서 같은 run 만들기**

같은 run 을 3주차 방식대로 클러스터 안의 Kubeflow 노트북(`suumo-nb`)에서도 만들었다. 노트북 Pod 에는 PodDefault `add-ml-env` 가 `KF_PIPELINES_ENDPOINT` 를 넣어 두므로 `kfp.Client()` 를 주소 없이 부른다. 노트북의 SDK 는 2.16.1 이라 다시 컴파일하지 않고, 개발 PC 에서 등록한 `suumo-data-prep` 의 최신 버전으로 run 만 만든다.

```python {title="notebooks/d_submit_from_nb.ipynb"}
import kfp

c = kfp.Client()   # 주소 인자 없음
pid = c.get_pipeline_id("suumo-data-prep")
vid = c.list_pipeline_versions(pid, sort_by="created_at desc").pipeline_versions[0].pipeline_version_id
exp = c.create_experiment("ch07-suumo")   # 있으면 그대로 돌려준다
r = c.run_pipeline(experiment_id=exp.experiment_id, job_name="suumo-d-from-notebook",
                   pipeline_id=pid, version_id=vid, enable_caching=False)
run = c.wait_for_run_completion(r.run_id, timeout=1800)
```

SDK 가 읽은 주소는 클러스터 내부 서비스 `http://ml-pipeline.kubeflow.svc.cluster.local:8888` 이다. 실험 목록과 등록된 파이프라인 버전이 개발 PC 에서 본 것과 같다.

![JupyterLab 의 d_submit_from_nb.ipynb. 첫 셀 출력은 kfp 2.16.1 과 KF_PIPELINES_ENDPOINT = http://ml-pipeline.kubeflow.svc.cluster.local:8888 이다. 두 번째 셀에서 kfp.Client() 를 인자 없이 불러 실험 목록 Default, smoke, income-classifier, ch07-data-passing, ch07-suumo 를 얻는다. 세 번째 셀은 suumo-data-prep 의 pipeline_id 와 최신 버전 suumo-data-prep-20261114-163014 를 출력하고, 네 번째 셀이 run_pipeline 으로 run 을 만든다.](run-d-nb-client.jpg)

run 은 개발 PC 에서 만든 것과 똑같이 232초 만에 끝났고, 태스크 12개가 모두 성공했다.

![JupyterLab 에서 wait_for_run_completion 셀의 출력. SUCCEEDED 232s 아래에 download-geo, download-raw, unzip-data, csv-to-parquet, csv-to-parquet-2, clean-dedup, put-to-minio, geocode, split-dataset, put-to-minio-2, eda-report, qa-data 가 모두 SUCCEEDED 로 10 ~ 30초씩 걸렸다.](run-d-nb-run.jpg)

KFP UI 의 실험 `ch07-suumo` 에는 두 run 이 같은 파이프라인 버전, 같은 소요 시간(3분 52초)으로 나란히 남는다. 어디서 제출했는지는 계산에 영향을 주지 않는다.

![KFP UI 의 실험 ch07-suumo Runs 목록. 맨 위 suumo-d-from-notebook 과 그 아래 suumo-d-registered 가 둘 다 성공, 0:03:52, 파이프라인 버전 suumo-data-prep-20261114... 이다. 그 아래로 suumo-c-ui, suumo-b-types, suumo-a-minato 가 있다.](run-d-nb-runs.jpg)

## 7. E 단계: 컨테이너화된 파이썬 컴포넌트 (7.3.2)

D 와 똑같은 파이프라인을 실행 방식만 바꿔 한 번 더 돌리고, 무엇이 달라지는지 비교한다. D 는 Pod 가 뜰 때마다 패키지를 pip 로 설치하고, E 는 패키지와 코드를 미리 넣어 둔 이미지로 실행한다.

![컴포넌트를 만드는 세 가지 방식. 경량 파이썬 컴포넌트(dsl.component, 실행할 때 pip install) → 컨테이너화된 파이썬 컴포넌트(dsl.component 와 target_image, 빌드할 때 설치) → 컨테이너 컴포넌트(dsl.container_component, 이미지와 명령을 직접 지정).](component-kinds.svg)

**경량과 컨테이너화의 차이**

한 줄로 줄이면 패키지와 코드를 Pod 가 뜰 때 가져오느냐, 미리 넣어 둔 이미지로 가져오느냐의 차이다. 코드는 `target_image` 한 줄만 다르다.

```python
# 경량 파이썬 컴포넌트
@dsl.component(base_image="python:3.11", packages_to_install=["pandas", "pyarrow"])
def clean_dedup(...):
    ...

# 컨테이너화된 파이썬 컴포넌트: target_image 한 줄이 늘어난다
@dsl.component(base_image="python:3.11", packages_to_install=["pandas", "pyarrow"],
               target_image="레지스트리/suumo-prep:1.0.0")
def clean_dedup(...):
    ...
```

Pod 가 뜰 때 일어나는 일은 이렇게 다르다.


|                | 경량                                  | 컨테이너화                       |
| -------------- | ----------------------------------- | --------------------------- |
| Pod 이미지        | 깨끗한 `python:3.11`                   | 미리 빌드한 `suumo-prep:1.0.0`   |
| 패키지            | Pod 가 뜰 때마다 pip 로 설치                | 이미지에 이미 들어 있음               |
| 함수 코드          | YAML 에 문자열로 들어 있다가 Pod 에서 파일로 써서 실행 | 이미지 안에 파일로 들어 있음            |
| 함수 밖 파일 import | 안 된다. 함수 본문만 옮겨지므로                  | 된다. 프로젝트 폴더가 통째로 이미지에 들어가므로 |


비유하면 경량은 요리할 때마다 장 보러 가는 것이고, 컨테이너화는 재료를 다 채운 냉장고를 들고 가는 것이다.


|         | 경량                                    | 컨테이너화                                 |
| ------- | ------------------------------------- | ------------------------------------- |
| 준비      | 없다. 코드만 고쳐서 바로 컴파일                    | 이미지를 빌드하고 레지스트리에 올려야 한다(도커 필요)        |
| 실행할 때   | 매번 pip 설치 시간이 든다. 인터넷이나 PyPI 가 막히면 실패 | 바로 시작한다                               |
| 코드 고칠 때 | 다시 컴파일만 하면 반영                         | 이미지를 다시 빌드하고 태그도 올려야 반영               |
| 맞는 경우   | 패키지가 가볍고 자주 고치는 실험 단계                 | 패키지가 무겁거나(torch 등) 여러 컴포넌트가 코드를 공유할 때 |


이 글의 패키지(pandas, pyarrow)는 가벼워서 경량으로 충분하다. E 단계는 이 방식도 실제로 돌려 보고 무엇이 달라지는지 재는 비교 실험이다. 8장에서 torch 나 LightGBM 처럼 무거운 패키지를 쓰게 되면 컨테이너화의 이점이 커진다.

**하는 일**

![E 단계 진행 순서. 컴포넌트에 target_image 지정 → kfp component build 로 이미지 1개 빌드 → 레지스트리에 push → 컴파일 → run 실행 → D 단계와 비교.](lab-e-order.svg)

- D 단계 컴포넌트 코드에 `target_image="레지스트리/suumo-prep:1.0.0"` 를 한 줄씩 붙인다.
- `kfp component build` 로 패키지(pandas, pyarrow, boto3 등)와 컴포넌트 코드가 미리 설치된 이미지 하나를 만든다.
- 이 이미지를 클러스터가 받을 수 있는 레지스트리에 올린다.
- 파이프라인을 다시 컴파일해 실행한다. 이제 각 Pod 는 `python:3.11` 대신 이 이미지로 뜬다.

**D 단계와 비교할 것**

- **컴파일된 YAML**: D 의 YAML 에 있던 pip 설치 명령과 함수 본문 문자열(5.1)이 사라졌는지 본다. 사라졌다면 코드가 YAML 이 아니라 이미지 안에 있다는 뜻이다.
- **컴포넌트별 실행 시간**: pip 설치가 없어진 만큼 Pod 하나당 얼마나 빨라지는지 KFP UI 의 시간으로 비교한다.
- **결과 파일(Parquet)**: 이미지 하나에 모든 컴포넌트의 패키지가 함께 들어가므로, 라이브러리 조합이 달라져 결과 파일 모양이 바뀌지 않는지 D 의 결과와 비교한다.
- **이미지 크기와 태그**: 이미지가 몇 GB 인지 본다. 코드를 고친 뒤 태그(`1.0.0`)를 그대로 두면 노드가 예전 이미지를 계속 쓰므로, 태그를 올려야 반영되는 것을 확인한다.

**모듈 분리**

- D 처럼 이미지 없이 돌리면 함수 본문만 Pod 로 옮겨지므로(5.1), 함수 밖의 다른 파일을 import 할 수 없다. 주소 정규화 코드를 `geocode` 와 `qa_data` 양쪽에 복사해 넣어야 한다.
- E 처럼 이미지를 빌드하면 프로젝트 폴더가 이미지에 들어가므로, 정규화 함수를 `address.py` 하나로 빼고 두 컴포넌트가 `from address import normalize` 로 같은 코드를 공유할 수 있다.
- 이것이 이미지 방식의 실질적인 이점이라 직접 바꿔 본다.

> **핸즈온ML 보강**: [모델 저장과 사용자 정의 코드 import](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#model-serving)

### 7.1 실행 결과

코드는 `07-suumo/e_components/`(이미지에 들어가는 폴더)와 `e_data_prep.py`(파이프라인 정의)이다. 컴포넌트 10개는 D 의 코드에 `target_image` 만 붙였고, 주소 정규화는 `address.py` 로 뺐다. 결과는 D 를 덮어쓰지 않도록 `suumo/prepared/2026-11-13-e/` 에 쓴다.

```python {title="e_components/components.py (geocode 부분)"}
@dsl.component(base_image=BASE, target_image=IMAGE, packages_to_install=["pandas", "pyarrow"])
def geocode(listings: Input[Dataset], geo: Input[Dataset], geocoded: Output[Dataset], metrics: Output[Metrics]):
    import pandas as pd
    from address import make_locator   # 이미지 안의 address.py (D 에서는 이 함수 안에 있던 코드)

    df = pd.read_parquet(listings.path)
    locate = make_locator(pd.read_parquet(geo.path))
    loc = df["住所"].map(locate)
    ...
```

`qa_data` 도 같은 모듈의 `ward_town` 으로 "chome_key 가 그 매물 주소의 구+동으로 시작하는가" 를 검사한다. 검사는 D 의 7개에서 8개가 된다.

**이미지 빌드와 push**

개발 PC 는 arm64 이고 클러스터 노드는 amd64 라서 `--platform linux/amd64` 로 빌드한다. `kfp component build` 가 `Dockerfile` 과 `runtime-requirements.txt` 를 만들고, 컴포넌트 10개의 `packages_to_install` 을 합쳐 한 번에 설치한다.

```terminal {title="개발 PC: E 단계 빌드, push, 실행"}
$ kfp component build e_components --component-filepattern components.py --platform linux/amd64 --no-push-image
Successfully tagged hyeonjae0913/suumo-prep:1.0.0
$ cat e_components/runtime-requirements.txt
boto3
pandas
pyarrow
requests
scikit-learn
$ docker push docker.io/hyeonjae0913/suumo-prep:1.0.0
$ python e_data_prep.py
$ KFP_HOST=http://192.168.0.242 python run_registered.py e_data_prep.yaml suumo-data-prep-e suumo-e-image
run_id=aaad630a-fb5b-4bf1-a4bd-76eab0efc766 FINAL=SUCCEEDED took=171s
```

생성된 `Dockerfile` 은 `python:3.11` 위에 requirements 와 `kfp==2.17.3` 을 설치하고, 마지막 `COPY . .` 로 폴더 전체(`components.py`, `address.py`)를 `/usr/local/src/kfp/components` 에 넣는다. 맥에서 amd64 를 에뮬레이션해 빌드하므로 약 6분이 걸렸다.

**컴파일된 YAML 비교**

| | D (`d_data_prep.yaml`) | E (`e_data_prep.yaml`) |
| --- | --- | --- |
| 파일 크기 | 45,479 bytes | 22,297 bytes |
| 컴포넌트 이미지 | `python:3.11` ×12 | `docker.io/hyeonjae0913/suumo-prep:1.0.0` ×12 |
| 함수 본문 문자열 | 있음 | 없음 |
| `kfp==2.17.3` 설치 | 12곳 | 없음 |
| 실행 명령 | 임시 파일에 본문을 써서 실행 | `python3 -m kfp.dsl.executor_main` 이 이미지 안의 `components.py` 를 읽음 |

함수 본문이 빠져 YAML 이 절반으로 줄었다. `packages_to_install` 의 `pip install 'pandas' 'pyarrow'` 줄은 E 에도 남지만, 패키지가 이미 이미지에 있어 아무것도 내려받지 않고 넘어간다. 실제로 E 의 Pod 로그에는 `Collecting`, `Downloading` 줄이 하나도 없다.

**실행 시간**

| | D | E |
| --- | --- | --- |
| run 전체 | 232초 (3분 52초) | **171초 (2분 51초)** |
| 컴포넌트 하나 | 대부분 20초 | 대부분 10초 |
| 이미지 받기 | `python:3.11` 은 노드에 이미 있음 | 첫 Pod 에서 압축 618MB 를 15초에 받음, 이후 Pod 는 재사용 |

pip 설치가 빠진 만큼 컴포넌트마다 약 10초씩 줄었다. 맨 앞의 `download_raw`, `download_geo` 는 이미지를 받는 시간이 더해져 30초였다. 노드가 한 번 받은 이미지는 다음 Pod 부터 그대로 쓴다.

![KFP UI 의 실험 ch07-suumo Runs 목록. 맨 위 suumo-e-image 가 성공, 0:02:51, 파이프라인 버전 suumo-data-prep-e 이다. 그 아래 suumo-d-from-notebook 과 suumo-d-registered 가 각각 0:03:52 이다.](run-e-runs.jpg)

**결과 파일 비교**

E 가 만든 Parquet 4개를 D 의 파일과 노트북에서 비교했다.

| 파일 | 크기 (D = E) | 행 수 | 스키마 | 내용 | 바이트 |
| --- | ---: | ---: | --- | --- | --- |
| `train.parquet` | 886,953 | 17,803 | 같음 | 같음 | 같음 |
| `val.parquet` | 202,588 | 3,878 | 같음 | 같음 | 같음 |
| `test.parquet` | 136,113 | 2,435 | 같음 | 같음 | 같음 |
| `chome.parquet` | 161,991 | 5,390 | 같음 | 같음 | 같음 |

두 run 모두 pandas 3.1.1, pyarrow 26.0.1 로 실행되어 파일이 바이트까지 같다. 다만 D 는 Pod 가 뜰 때마다 최신 버전을 받으므로 시간이 지나면 버전이 달라질 수 있다. E 는 이미지에 버전이 고정되어 같은 태그라면 항상 같은 라이브러리로 돈다.

**이미지 크기**

| 이미지 | 크기 (압축 해제) | 레지스트리에서 받는 크기 |
| --- | ---: | ---: |
| `python:3.11` | 1.6GB | |
| `suumo-prep:1.0.0` | 2.48GB | 618MB |

pandas, pyarrow, scikit-learn, kfp 가 기본 이미지에 약 0.9GB 를 더했다.

**태그를 그대로 두고 코드를 고치면**

`clean_dedup` 의 로그 줄에 `price_removed=` 를 덧붙이고 두 가지로 다시 돌렸다. 먼저 같은 태그 `1.0.0` 으로 다시 빌드해 push 했고, 그다음 태그를 `1.0.1` 로 올렸다.

| run | 태그 | 레지스트리의 digest | Pod 가 실제로 쓴 digest | `clean_dedup` 로그 |
| --- | --- | --- | --- | --- |
| `suumo-e-image` | `1.0.0` | `1bf7f84…` | `1bf7f84…` | `… price=24117` |
| `suumo-e-same-tag` | `1.0.0` (다시 push) | `0817106…` | **`1bf7f84…`** | `… price=24117` (고친 줄 없음) |
| `suumo-e-tag-1.0.1` | `1.0.1` | `9ca15c1…` | `9ca15c1…` | `… price=24117 price_removed=2` |

KFP 가 만든 Pod 의 `imagePullPolicy` 는 `IfNotPresent` 다. 그래서 노드에 같은 이름의 이미지가 있으면 레지스트리가 바뀌어도 다시 받지 않는다. 태그를 올리자 노드가 새 이미지를 받았고, 바뀐 마지막 층(`COPY . .`)만 받아 3.9초가 걸렸다.

```terminal {title="개발 PC: 태그 올리기"}
$ sed -i '' 's/suumo-prep:1.0.0/suumo-prep:1.0.1/' e_components/components.py
$ kfp component build e_components --component-filepattern components.py --platform linux/amd64 --no-push-image
$ docker push docker.io/hyeonjae0913/suumo-prep:1.0.1
$ python e_data_prep.py
$ KFP_HOST=http://192.168.0.242 python run_registered.py e_data_prep.yaml suumo-data-prep-e suumo-e-tag-1.0.1
run_id=b49b8e5b-79f2-44af-8e69-6f15e5a03ea8 FINAL=SUCCEEDED took=161s
```

코드만 바뀐 두 번째 빌드부터는 pip 층을 캐시로 재사용해 25초 만에 끝났다. 코드를 고칠 때마다 태그를 올리는 것을 규칙으로 둔다.

> **핸즈온ML 보강**: [재현 가능하게 남기기](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#reproducibility) · [모니터링과 재학습](../../hands-on-machine/hands-on-ml-02-2-split-to-launch/#monitoring)

**QA 결과**

`address.py` 를 쓰는 8번째 검사까지 모두 통과했다.

![KFP UI 에서 run suumo-e-image 의 qa-data report 아티팩트 Visualization. QA 결과: PASSED 아래에 대상 s3://datasets/suumo/prepared/2026-11-13-e/ 와 검사 여덟 개가 있다. D 와 같은 일곱 개에 chome_key 와 주소 불일치 0 이 더해졌고 모두 PASS 이다. 아래 표에 train 17,803행 73.8% 1,824 초메, val 3,878행 16.1% 364 초메가 보인다.](run-e-qa.jpg)
