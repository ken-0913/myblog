"""PagedAttention 검증 2 — 흩어진 빈칸을 주워 담는가

일부러 '구멍'을 만든다.
요청 셋을 나란히 띄우고, 가운데 것만 먼저 끝내면 그 자리가 빈다.
그 뒤 구멍보다 큰 요청을 넣어 어디서 블록을 받아 오는지 본다.
"""
import os

os.environ["VLLM_ENABLE_V1_MULTIPROCESSING"] = "0"
os.environ["VLLM_USE_FLASHINFER_SAMPLER"] = "0"
os.environ["TORCHDYNAMO_DISABLE"] = "1"

from vllm import LLM, SamplingParams

BLK = 16
POOL = 80            # 풀을 좁혀야 구멍을 재사용할 수밖에 없다
BAR = "=" * 74

llm = LLM(model="HuggingFaceTB/SmolLM-135M",
          max_model_len=512,
          block_size=BLK,
          num_gpu_blocks_override=POOL,     # 기본 4,361개는 너무 넉넉하다
          enable_prefix_caching=False,      # 공유를 꺼야 파편화만 보인다
          gpu_memory_utilization=0.35,
          enforce_eager=True)

engine = llm.llm_engine
scheduler = engine.engine_core.engine_core.scheduler
manager = scheduler.kv_cache_manager.coordinator.single_type_managers[0]


def blocks_of(tag):
    for request_id, blocks in manager.req_to_blocks.items():
        if request_id == tag or request_id.startswith(tag + "-"):
            return [b.block_id for b in blocks]
    return None


def add(tag, prompt, max_tokens):
    engine.add_request(tag, prompt,
                       SamplingParams(temperature=0, max_tokens=max_tokens))


def contiguous(xs):
    s = sorted(xs)
    return s == list(range(s[0], s[-1] + 1))


print("\n" + BAR)
print(f"[1] 요청 셋을 띄운다 — 풀 {POOL}블록, prefix 공유 끔")
print(BAR)

body = "요청 %s 의 본문입니다. 블록을 여러 개 차지하도록 길게 씁니다. "
add("R0", (body % "A") * 5, max_tokens=400)   # 오래 남는다
add("R1", (body % "B") * 5, max_tokens=2)     # 먼저 끝난다 -> 구멍이 된다
add("R2", (body % "C") * 5, max_tokens=400)   # 오래 남는다
for _ in range(2):
    engine.step()

occupied = {i: blocks_of(f"R{i}") for i in range(3)}
for i in range(3):
    print(f"  R{i} : {occupied[i]}")

hole = list(occupied[1])
used = sum(len(v) for v in occupied.values() if v)
print(f"\n  사용 {used} / 전체 {POOL}  ->  아직 안 쓴 블록 {POOL - used}개")

print("\n" + BAR)
print("[2] 가운데 R1 이 끝나면서 구멍이 생긴다")
print(BAR)
for _ in range(20):
    engine.step()
    if blocks_of("R1") is None:          # 블록 테이블에서 사라지면 반환된 것
        break
print(f"  구멍 {len(hole)}블록 반환 : {hole}")
print(f"  가용 = 구멍 {len(hole)} + 미사용 {POOL - used} = {len(hole) + POOL - used}블록")
print(f"  다만 가장 긴 '연속' 구간은 {max(len(hole), POOL - used)}블록뿐이다")

print("\n" + BAR)
print("[3] 구멍보다 큰 요청을 넣는다")
print(BAR)
need = "새 요청. 흩어진 빈칸을 모두 써야 들어갈 만큼 길게 만든 프롬프트입니다. " * 5
add("NEW", need, max_tokens=4)

got = []
for _ in range(15):
    engine.step()
    got = blocks_of("NEW") or []
    if got:
        break

print(f"  NEW 가 받은 블록 ({len(got)}개) :")
print(f"    {got}")
if got:
    reused = sorted(set(got) & set(hole))
    fresh = sorted(set(got) - set(hole))
    print(f"\n  구멍에서 재사용 : {len(reused)}개 {reused}")
    print(f"  미사용분에서    : {len(fresh)}개 {fresh}")
    print(f"  연속인가? {'예' if contiguous(got) else '아니오 — 흩어진 블록을 이어 붙였다'}")
    if reused and fresh:
        print("\n  -> 연속 할당이었다면 이만한 연속 공간이 없어 거절됐을 것이다")
