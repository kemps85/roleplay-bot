import asyncio, sys, types, json
sys.path.insert(0, r'C:\Users\ASUS\Documents\Discord\roleplay-bot')
import bot as B
B.save = lambda: None                      # không ghi đè sessions.json thật
B.bot._connection.user = types.SimpleNamespace(id=1)
HOOK = 9
def M(id, aid, wid, c, bot=False, name="An"):
    return types.SimpleNamespace(id=id, author=types.SimpleNamespace(id=aid, bot=bot, display_name=name), webhook_id=wid, content=c, embeds=[])
U = lambda i, t="u": M(i, 5, None, t)
C = lambda i, t="c": M(i, HOOK, HOOK, t, True)
class TH:
    def __init__(s, msgs): s.msgs, s.sent, s.deleted = msgs, [], []
    def history(s, limit):
        async def g():
            for m in list(reversed(s.msgs))[:limit]: yield m
        return g()
    def typing(s):
        class T:
            async def __aenter__(a): pass
            async def __aexit__(a, *e): pass
        return T()
    async def send(s, *a, **k): s.sent.append(a or k)
def S(**kw): return dict({"hook_ids": [HOOK], "char_name": "Hotaru", "system_prompt": "sys", "summary": "", "summarized_upto_message_id": 0, "ended": False}, **kw)
roles = lambda out: [m["role"] for m in out]
async def main():
    # 1. tin gửi lúc bot đang gõ: U1,U2,A1 (A1 trả lời U1) -> U1,A1,U2
    s = S(last_input_id=2); out, old = await B.build_messages(TH([C(1), U(2), U(3), C(4)]), s)
    assert roles(out) == ["system", "assistant", "user", "assistant", "user"] and out[-1]["content"].startswith("[An]: u") and old is None
    assert await B.build_messages(TH([C(1), U(2), U(3), C(4)]), s) is None, "dedupe"
    # 2. tin cuối của người dùng trùng FAIL -> không gửi prompt kết thúc bằng model
    assert await B.build_messages(TH([U(1), C(2), U(3, B.FAIL)]), S()) is None
    # 3. thread dài 100 tin: lượt này gửi đủ, phần cũ trả về để tóm tắt sau
    h = [C(i) if i % 2 else U(i) for i in range(1, 101)]
    s = S(); out, old = await B.build_messages(TH(h), s)
    assert len(out) == 101 and len(old) == 60 and old[-1][0].id == 60, (len(out), len(old))
    calls = []
    async def fake_llm(msgs, **kw): calls.append(kw); return "TÓM TẮT"
    B.llm = fake_llm
    await B.summarize(s, old)
    assert s["summary"] == "TÓM TẮT" and s["summarized_upto_message_id"] == 60 and calls[0]["temperature"] == 0.3
    h.append(U(101)); out, old = await B.build_messages(TH(h), s)
    assert old is None and len(out) == 42 and "TÓM TẮT" in out[0]["content"], len(out)
    # 4. tóm tắt lỗi / bị chặn: giữ tóm tắt cũ, 5 phút sau mới thử lại
    for bad in (None, B.REMIND):
        async def f(msgs, **kw): return bad
        B.llm = f
        s = S(summary="cũ"); _, old = await B.build_messages(TH(h[:100]), s)
        await B.summarize(s, old)
        assert s["summary"] == "cũ" and s["summarized_upto_message_id"] == 0 and s["sum_retry"] > B.time.time()
        s["last_input_id"] = 0; _, old2 = await B.build_messages(TH(h[:100]), s)
        assert old2 is None, "phải chờ sum_retry"
    # 5. clean_reply
    cr = B.clean_reply
    assert cr("[Hotaru]: *cười* chào", "Hotaru") == "*cười* chào"
    assert cr("Hotaru: chào", "Hotaru") == "chào"
    assert cr("*cười* chào cậu\n[An]: tớ cũng vậy", "Hotaru") == "*cười* chào cậu"
    assert cr("Chào [An] nha: hôm nay vui", "Hotaru") == "Chào [An] nha: hôm nay vui"
    assert cr("[An]: x", "Hotaru") == "[An]: x"     # không cắt thành rỗng
    # 6. respond: LLM hỏng khi viết lại -> đăng lại câu cũ; lỗi bất ngờ -> báo FAIL thay vì im lặng
    said = []
    async def fake_say(th, s, t): said.append(t)
    B.say = fake_say
    async def none(msgs, **kw): return None
    B.llm = none
    await B.respond(TH([C(1), U(2)]), S(), fallback="câu cũ"); assert said[-1] == "câu cũ"
    await B.respond(TH([C(1), U(3)]), S()); assert said[-1] == B.FAIL
    async def boom(msgs, **kw): raise PermissionError("sessions.json bị khoá")
    B.llm = boom; th = TH([C(1), U(2)])
    await B.respond(th, S()); assert th.sent, "phải báo FAIL"
    async def ok(msgs, **kw): return "[Hotaru]: xin chào\n[An]: hehe"
    B.llm = ok
    await B.respond(TH([C(1), U(2)]), S()); assert said[-1] == "xin chào"
    # 7. viết lại: U1,U2,A1,A2 (A1 trả lời U1, đăng sau U2), thả 🔄 vào A2 -> chỉ xoá A2, prompt U1,A1,U2
    msgs = [C(1), U(2, "u1"), U(3, "u2"), C(4, "a1"), C(5, "a2")]
    th = TH(msgs)
    for m in msgs:
        async def d(m=m): msgs.remove(m); th.deleted.append(m.id)
        m.delete = d
    s = S(turn_ids=[5], last_input_id=3)
    B.sessions["777"] = s; B.bot.get_channel = lambda cid: th
    got = []
    async def grab(th_, s_, fallback=None): got.append((await B.build_messages(th_, s_), fallback))
    real_respond, B.respond = B.respond, grab
    await B.on_raw_reaction_add(types.SimpleNamespace(emoji=B.REROLL, channel_id=777, user_id=5, member=None, message_id=5))
    assert th.deleted == [5], th.deleted
    (out, _), fb = got[0]
    assert [m["content"][:6] for m in out[1:]] == ["c", "[An]: ", "a1", "[An]: "] and out[-1]["content"].startswith("[An]: u2") and fb == "a2", out
    # 8. 🔄 vào lượt cũ / lời mở đầu: không làm gì
    got.clear()
    await B.on_raw_reaction_add(types.SimpleNamespace(emoji=B.REROLL, channel_id=777, user_id=5, member=None, message_id=1)); assert not got
    th2 = TH([M(1, 1, None, B.CTRL + "x", True), C(2, "intro")]); B.bot.get_channel = lambda cid: th2
    s.update(turn_ids=[2]); await B.on_raw_reaction_add(types.SimpleNamespace(emoji=B.REROLL, channel_id=777, user_id=5, member=None, message_id=2)); assert not got
    B.respond = real_respond
    # 9. hai tin đến cùng lúc: chỉ trả lời 1 lần (gộp), không trả lời trùng
    said.clear(); n = []
    async def slow(msgs, **kw): n.append(1); await asyncio.sleep(0.05); return "rep"
    B.llm = slow; th = TH([C(1), U(2), U(3)]); s = S(); B.sessions["888"] = s
    async def say2(th_, s_, t): th_.msgs.append(C(100 + len(n), t)); said.append(t)
    B.say = say2
    mk = lambda i: types.SimpleNamespace(author=types.SimpleNamespace(id=5, bot=False), channel=types.SimpleNamespace(id=888, **{k: getattr(th, k) for k in ("history", "typing", "send")}, msgs=th.msgs), content="u")
    await asyncio.gather(B.on_message(mk(2)), B.on_message(mk(3)))
    assert len(n) == 1 and len(said) == 1, (n, said)
    print("stress ok")
asyncio.run(main())
