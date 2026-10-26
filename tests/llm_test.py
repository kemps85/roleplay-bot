import asyncio, sys, json
sys.path.insert(0, r'C:\Users\ASUS\Documents\Discord\roleplay-bot')
import bot as B
B.MODELS[:] = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
script, seen = [], []
def ok(t, fr="stop"): return (200, {"choices": [{"message": {"content": t}, "finish_reason": fr}]})
class R:
    def __init__(s, st, body): s.status, s.body, s.headers = st, body, {}
    async def __aenter__(s): return s
    async def __aexit__(s, *e): pass
    async def json(s, content_type=None): return s.body
    async def text(s): return s.body if isinstance(s.body, str) else json.dumps(s.body)
class CS:
    async def __aenter__(s): return s
    async def __aexit__(s, *e): pass
    def post(s, url, headers, json, timeout):
        seen.append((json["model"], json.get("reasoning_effort"), json["max_tokens"]))
        return R(*script.pop(0))
B.aiohttp.ClientSession = CS
async def orig(_): pass
B.asyncio.sleep = lambda *_: orig(0)
async def run(steps, msgs=None):
    script[:] = steps; seen.clear(); B.bad_until.clear()
    return await B.llm(msgs or [{"role": "user", "content": "[An]: hi"}])
async def main():
    assert await run([ok("xin chào")]) == "xin chào" and seen == [("gemini-3.8-flash", "low", 1500)]
    # rỗng rồi ok: thử lại cùng model, không xuống lite
    assert await run([ok(""), ok("lần 2")]) == "lần 2" and [m for m, *_ in seen] == ["gemini-3.8-flash"] * 2
    # 500 hai lần -> phạt 60s, sang lite (lite không có reasoning_effort)
    assert await run([(500, "x"), (500, "x"), ok("lite")]) == "lite" and seen[-1] == ("gemini-3.5-flash-lite", None, 1500)
    assert 0 < B.bad_until["gemini-3.8-flash"] - B.time.monotonic() <= 60
    # Google chặn an toàn bằng 400 -> nhắc nhẹ, KHÔNG phạt model
    assert await run([(400, '[{"error":{"message":"Request blocked: PROHIBITED_CONTENT"}}]')]) == B.REMIND and not B.bad_until
    # 400 thường (sai tham số) -> phạt 300s, sang model sau
    assert await run([(400, "Invalid argument"), ok("b")]) == "b" and B.bad_until["gemini-3.8-flash"] - B.time.monotonic() > 200
    # content_filter -> nhắc nhẹ
    assert await run([ok("", "content_filter")]) == B.REMIND
    # chữ CJK: người dùng viết tiếng Việt -> bỏ; người dùng viết tiếng Nhật -> nhận
    assert await run([ok("こんにちは"), ok("chào")]) == "chào"
    assert await run([ok("こんにちは")], [{"role": "user", "content": "[An]: こんにちは"}]) == "こんにちは"
    # bị cụt -> cắt về câu hoàn chỉnh
    assert await run([ok("Câu một. Câu hai dở", "length")]) == "Câu một."
    # 429 hết hạn mức ngày -> nghỉ tới lần reset
    assert await run([(429, "GenerateRequestsPerDayPerProjectPerModel"), ok("c")]) == "c" and B.bad_until["gemini-3.8-flash"] - B.time.monotonic() > 60
    # choices rỗng (bị chặn ở prompt) -> không sập, sang model sau
    assert await run([(200, {"choices": []}), ok("d")]) == "d"
    # tất cả hỏng -> None (respond sẽ đăng FAIL hoặc câu cũ)
    assert await run([(503, "")] * 6) is None
    print("llm ok")
asyncio.run(main())
