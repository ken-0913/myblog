#!/usr/bin/env python3
"""LLM 시리즈 3~8편을 통합본 한 파일로 합친다.

    python3 scripts/build_all_in_one.py

`content/posts/llm/llm-series-all-in-one.md` 를 통째로 다시 만든다.
개별 글을 고쳤거나, 편집기가 통합본의 수식을 깨뜨렸을 때 이걸 다시 돌리면 된다.

하는 일
  - 각 편의 front matter를 떼고 heading을 한 단계 내린다(## → ###).
  - 각 편 끝의 `## 정리` 를 떼어 글 맨 뒤 `전체 정리` 로 모은다.
  - "앞 글에서" 같은 편 간 상호참조를 "1부에서" 식으로 바꾼다.

통합본을 직접 고치지 말 것. 여기서 다시 만들면 덮어써진다.
개별 글을 고치고 이 스크립트를 돌리거나, 통합본에만 필요한 내용이면
아래 HEADER / FOOTER 상수를 고친다.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "content", "posts", "llm")
OUT = os.path.join(SRC_DIR, "llm-series-all-in-one.md")

PARTS = [
    ("llm-03-gpt3-embeddings.md",              "1부. 임베딩과 위치 정보 (Token을 벡터로 바꾸기)"),
    ("llm-04-gpt3-self-attention.md",          "2부. Self-Attention — 단어들이 서로를 참고한다"),
    ("llm-05-gpt3-attention-output-concat.md", "3부. Multi-Head 마무리 — concat과 Wₒ"),
    ("llm-06-gpt3-mlp-feedforward.md",         "4부. MLP — 각 token을 따로 가공한다"),
    ("llm-07-gpt3-kv-cache-prefill-decode.md", "5부. prefill, decode, KV Cache"),
    ("llm-08-gpt3-output-layer-sampling.md",   "6부. 출력층과 sampling — 다시 글자로"),
]

HEADER = '''---
title: "LLM 서빙 스터디 통합본 — 임베딩부터 token 생성까지"
date: 2026-08-07T20:00:00+09:00
draft: false
tags: ["LLM", "GPT-3", "Transformer", "Self-Attention", "KV Cache", "Sampling", "선형대수"]
categories: ["프로그래밍"]
math:
  enable: true
featuredImage: images/banners/llm-series-all-in-one-85eb1b79.png
---
## 이 글의 구성

| | 다루는 것 |
| --- | --- |
| 1부 | 임베딩과 위치 정보 (Token을 벡터로 바꾸기) |
| 2부 | Q·K·V로 문맥을 섞는 self-attention |
| 3부 | 여러 head를 이어붙이고 되돌리는 concat과 \\(W_O\\) |
| 4부 | token 하나를 따로 가공하는 MLP, LayerNorm, residual |
| 5부 | 생성을 반복하는 구조와 KV Cache |
| 6부 | 벡터를 다시 글자로 되돌리는 출력층과 sampling |

'''

FOOTER = '''## 한 바퀴를 다시 보면

$$
\\text{텍스트} \\to \\underbrace{H_0}_{\\text{1부}} \\to \\underbrace{Z^i}_{\\text{2부}} \\to \\underbrace{\\text{Concat} \\cdot W_O}_{\\text{3부}} \\to \\underbrace{\\text{LN} \\to \\text{MLP} \\to +x}_{\\text{4부}} \\to \\underbrace{\\text{반복}}_{\\text{5부}} \\to \\underbrace{\\text{logits} \\to \\text{argmax}}_{\\text{6부}} \\to \\text{텍스트}
$$

GPT-3는 2부부터 4부까지를 **블록 하나**로 묶어 **96번 쌓고**, 그 위에서 5부의 반복을 돌린다.
차원이 3에서 12288로, 층이 1에서 96으로 커질 뿐 각 단계에서 하는 계산은 이 글에서 손으로 따라간 것과 똑같다.
'''

# 편 번호 → 부 번호. "3편" → "1부"
PART_OF = {3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6}

# 개별 글 기준으로 쓰인 표현을 통합본 어투로. (원문, 통합본)
REWRITES = [
    ("앞 글에서 문장은 \\(H_0\\) 라는 벡터 묶음(행렬)이 되어 Transformer 블록으로 들어갔다.",
     "1부에서 문장은 \\(H_0\\) 라는 벡터 묶음(행렬)이 되어 Transformer 블록으로 들어갔다."),
    ("이 글은 앞 글의 **3차원 결과 \\(H_0\\) 를 그대로 입력으로 이어받아**, attention을 손으로 따라가며 정리한다.",
     "여기서는 그 **3차원 결과 \\(H_0\\) 를 그대로 입력으로 이어받아**, attention을 손으로 따라간다."),
    ("### 예시 설정 — 앞 글의 H₀ 이어받기", "### 예시 설정 — 1부의 H₀ 이어받기"),
    ("입력은 앞 글에서 만든", "입력은 1부에서 만든"),
    ("지금은 뼈대만 보고, 살은 이 글 뒤쪽 multi-head 절에서 붙인다.",
     "지금은 뼈대만 보고, 살은 이 부 뒤쪽 multi-head 절에서 붙인다."),
    ("그 대가로 다음 글의 \\(W_O\\) 가 정방행렬이 아니게 되는데, 거기서 다시 짚는다.",
     "그 대가로 3부의 \\(W_O\\) 가 정방행렬이 아니게 되는데, 거기서 다시 짚는다."),
    ("다시 \\(3 \\times 3\\) 으로 되돌리는 과정이 다음 글의 주제다.",
     "다시 \\(3 \\times 3\\) 으로 되돌리는 과정이 다음 부의 주제다."),
    ("앞 글에서 head 2개가 각각 따로 attention을 계산해", "앞에서 head 2개가 각각 따로 attention을 계산해"),
    ("이 글은 그 조각들을 **이어붙여(concatenation) 다시 \\(3 \\times 3\\) 하나로 되돌리는** 과정을 정리한다.",
     "이제 그 조각들을 **이어붙여(concatenation) 다시 \\(3 \\times 3\\) 하나로 되돌린다.**"),
    ("앞 글에서 head 2개가 각각 \\(d_v = 2\\) 짜리", "앞에서 head 2개가 각각 \\(d_v = 2\\) 짜리"),
    ("앞 글에서 두 head에 각각 다른", "앞에서 두 head에 각각 다른"),
    ("앞 글에서 \\(d_{\\text{model}} = 3\\) 을 head 2개로", "2부에서 \\(d_{\\text{model}} = 3\\) 을 head 2개로"),
    ("두 장치 모두 다음 글에서 숫자와 함께 다룬다.", "두 장치 모두 다음 부에서 숫자와 함께 다룬다."),
    ("### LayerNorm — 앞 글들에서 미뤄 둔 것", "### LayerNorm — 앞에서 미뤄 둔 것"),
    ('MLP로 들어가기 전에, 지난 글들에서 계속 "다음 글에서 다룬다"고 미뤄 둔 LayerNorm을 짚는다.',
     'MLP로 들어가기 전에, 앞에서 계속 "뒤에서 다룬다"고 미뤄 둔 LayerNorm을 짚는다.'),
    ('앞 글의 multi-head 출력에서 "먹었다" 행은', '3부의 multi-head 출력에서 "먹었다" 행은'),
    ("숫자를 앞 글과 맞춰 두는 편이 읽기 쉽기 때문이다.", "숫자를 앞부분과 맞춰 두는 편이 읽기 쉽기 때문이다."),
    ("이 글은 그 반복 구조를 **prefill · decode** 로 나누고,",
     "이제 그 반복 구조를 **prefill · decode** 로 나누고,"),
    ("이 글은 **2부의 단순 설정으로 되돌아간다.**", "여기서는 **2부의 단순 설정으로 되돌아간다.**"),
    ("앞 글들과 같은 벡터를 쓴다", "앞과 같은 벡터를 쓴다"),
    ("출력층과 이 sampling 기법들은 **다음 글에서** 숫자와 함께 자세히 다룬다.",
     "출력층과 이 sampling 기법들은 **다음 부에서** 숫자와 함께 자세히 다룬다."),
    ("이 글은 그 벡터가 **다시 글자로 돌아오는 마지막 구간**을 다룬다.",
     "이제 그 벡터가 **다시 글자로 돌아오는 마지막 구간**을 본다."),
    ("이 글 내내 쓸 작은 예시를 정한다.", "글 내내 쓸 작은 예시를 정한다."),
    ("이 글은 GPT-3를 예로 임베딩이 **행렬 연산**으로 어떻게 이뤄지는지 정리한다.",
     "먼저 GPT-3를 예로 임베딩이 **행렬 연산**으로 어떻게 이뤄지는지 본다."),
    ("- 이 글의 \\(W = I\\) 설정은", "- 2부의 \\(W = I\\) 설정은"),
    # 6부가 본격적으로 다루므로 5부 정리에서는 뺀다
    ("- 벡터가 token이 되는 마지막 경로는 **final LayerNorm → 출력층 → logits → argmax** 다.\n", ""),
]


def strip_front_matter(src):
    return src.split("---", 2)[2].lstrip("\n") if src.startswith("---") else src


def demote_headings(body):
    """코드펜스 밖의 heading만 한 단계 내린다."""
    out, in_fence = [], False
    for line in body.split("\n"):
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
        if not in_fence and re.match(r"^#{2,5} ", line):
            line = "#" + line
        out.append(line)
    return "\n".join(out)


def split_summary(body, heading="## 정리"):
    """마지막 `## 정리` 절을 떼어낸다. → (본문, 정리)"""
    i = body.rfind("\n" + heading + "\n")
    if i == -1:
        return body, ""
    return body[:i].rstrip() + "\n", body[i + len(heading) + 2:].strip()


def rewrite_refs(text):
    for n, part in PART_OF.items():
        text = text.replace(f"{n}편", f"{part}부")
    for old, new in REWRITES:
        text = text.replace(old, new)
    return text


def main():
    chunks, summaries = [], []
    for fname, part_title in PARTS:
        with open(os.path.join(SRC_DIR, fname), encoding="utf-8") as f:
            body = strip_front_matter(f.read())
        body, summary = split_summary(body)
        chunks.append(f"## {part_title}\n\n{demote_headings(body).strip()}\n")
        summaries.append((part_title, summary))

    parts = [HEADER, rewrite_refs("\n".join(chunks)), "\n## 전체 정리\n\n"]
    for title, summary in summaries:
        parts.append(f"### {title}\n{rewrite_refs(summary)}\n\n")
    parts.append(FOOTER)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("".join(parts))

    rel = os.path.relpath(OUT, ROOT)
    print(f"{rel} — {len(''.join(parts).splitlines())}줄, {len(PARTS)}부")


if __name__ == "__main__":
    main()
