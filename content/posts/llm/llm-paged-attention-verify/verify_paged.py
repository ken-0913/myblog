"""PagedAttention 검증 1 — 블록 단위 할당과 prefix 공유

vLLM 엔진을 같은 프로세스 안에서 띄우고, 스케줄러가 들고 있는
블록 테이블(req_to_blocks)을 직접 꺼내 본다.
"""
import os

# 엔진을 별도 프로세스가 아니라 이 프로세스 안에서 돌린다. 내부를 보려면 필수.
os.environ["VLLM_ENABLE_V1_MULTIPROCESSING"] = "0"
# nvcc 가 없는 환경에서 FlashInfer 샘플러가 JIT 컴파일하다 죽는 것을 피한다.
os.environ["VLLM_USE_FLASHINFER_SAMPLER"] = "0"
os.environ["TORCHDYNAMO_DISABLE"] = "1"

import math
import torch
from vllm import LLM, SamplingParams

BLK = 16                      # 블록 하나가 담는 토큰 수
MAX_LEN = 512                 # 최대 컨텍스트 길이
BAR = "=" * 74

llm = LLM(model="HuggingFaceTB/SmolLM-135M",
          max_model_len=MAX_LEN,
          block_size=BLK,
          enable_prefix_caching=True,
          gpu_memory_utilization=0.35,
          enforce_eager=True)

engine = llm.llm_engine
scheduler = engine.engine_core.engine_core.scheduler
manager = scheduler.kv_cache_manager.coordinator.single_type_managers[0]
tokenizer = engine.get_tokenizer()
cache_config = engine.vllm_config.cache_config


def blocks_of(tag):
    """요청이 들고 있는 물리 블록 번호 목록.

    엔진이 request_id 뒤에 접미사를 붙이므로("R1" -> "R1-bf6e0edb")
    정확히 일치시키지 말고 접두사로 찾는다.
    """
    for request_id, blocks in manager.req_to_blocks.items():
        if request_id == tag or request_id.startswith(tag + "-"):
            return [b.block_id for b in blocks]
    return None


def add(tag, prompt, max_tokens=4):
    engine.add_request(tag, prompt,
                       SamplingParams(temperature=0, max_tokens=max_tokens))


def drain():
    """남은 요청을 모두 끝낸다."""
    while engine.has_unfinished_requests():
        engine.step()


# ─────────────────────────────────────────────────────────────
print("\n" + BAR)
print("[1] KV 캐시 풀은 기동 시 고정 크기로 선할당된다")
print(BAR)
print(f"  block_size     : {cache_config.block_size} 토큰")
print(f"  num_gpu_blocks : {cache_config.num_gpu_blocks:,} 개")
print(f"  총 수용량      : {cache_config.num_gpu_blocks * cache_config.block_size:,} 토큰")
before = torch.cuda.memory_allocated()
print(f"  GPU 할당량     : {before / 1024**2:,.1f} MiB  (이후 변하지 않는다)")

# ─────────────────────────────────────────────────────────────
print("\n" + BAR)
print("[2] 요청은 max_model_len 이 아니라 '쓴 만큼'만 블록을 잡는다")
print(BAR)
print(f"  {'토큰':>5} {'블록':>5} {'ceil(n/16)':>11} {'낭비':>7}  연속할당이면")

prompts = [
    "안녕",
    "오늘 날씨는 어떤가요? 서울 기준으로 알려줘.",
    "긴 프롬프트를 만들기 위해 같은 문장을 반복한다. " * 6,
]
for i, prompt in enumerate(prompts):
    tag = f"L{i}"
    n = len(tokenizer.encode(prompt))
    add(tag, prompt)
    engine.step()                       # prefill 이 돌면서 블록이 배정된다
    got = blocks_of(tag) or []
    print(f"  {n:5d} {len(got):5d} {math.ceil(n / BLK):11d} {len(got) * BLK - n:6d}칸"
          f"  {MAX_LEN // BLK}블록 고정")
    drain()

# ─────────────────────────────────────────────────────────────
print("\n" + BAR)
print("[3] prefix 가 같으면 같은 물리 블록을 공유한다")
print(BAR)

shared = "You are a helpful assistant. " * 10      # 두 요청이 공유할 앞부분

add("PA", shared + "질문 A 입니다.")
engine.step()
blocks_a = blocks_of("PA")
drain()

add("PB", shared + "완전히 다른 질문 B 입니다.")
engine.step()
blocks_b = blocks_of("PB")
drain()

print(f"  공유 prefix : {len(tokenizer.encode(shared))} 토큰")
print(f"  A 블록 : {blocks_a}")
print(f"  B 블록 : {blocks_b}")
if blocks_a and blocks_b:
    same = [x for x, y in zip(blocks_a, blocks_b) if x == y]
    print(f"  앞에서부터 일치 : {same}"
          f"  ({len(same)}개 = {len(same) * BLK} 토큰 재계산 생략)")

# ─────────────────────────────────────────────────────────────
print("\n" + BAR)
print("[4] 그동안 GPU 메모리 총량은 변하지 않았다")
print(BAR)
after = torch.cuda.memory_allocated()
print(f"  검증 전 {before / 1024**2:,.1f} MiB"
      f" -> 검증 후 {after / 1024**2:,.1f} MiB"
      f"  (차이 {(after - before) / 1024**2:+.1f} MiB)")
print("  -> 풀은 고정, 그 안에서 블록 소유권만 오간다")
