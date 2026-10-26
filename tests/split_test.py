import asyncio, sys, types
sys.path.insert(0, r'C:\Users\ASUS\Documents\Discord\roleplay-bot')
import bot as B
B.save = lambda: None
B.bot._connection.user = types.SimpleNamespace(id=1)
P = B.paragraphs
assert P("*a*\n\nb\n\n*c*\n\nd") == ["*a*", "b", "*c*", "d"]
assert P("*a\n\nvẫn nghiêng*\n\nb") == ["*a\n\nvẫn nghiêng*", "b"], "không tách giữa *...*"
assert P("một đoạn") == ["một đoạn"] and P("a\n   \nb") == ["a", "b"]
assert all(len(x) <= 4096 for x in P("x " * 5000))
# say: 4 đoạn -> 4 tin, turn_ids đủ 4, 🔄 ở tin cuối
sent, reacts = [], []
class Hook:
    id = 9
    async def send(self, **kw): sent.append(kw["embed"].description); return types.SimpleNamespace(id=100 + len(sent))
B.get_hook = lambda s: Hook()
B.asyncio.sleep = (lambda real: (lambda *a: real(0)))(asyncio.sleep)
class Typ:
    async def __aenter__(a): pass
    async def __aexit__(a, *e): pass
th = types.SimpleNamespace(parent=None, typing=lambda: Typ(), get_partial_message=lambda i: types.SimpleNamespace(add_reaction=lambda e: reacts.append(("+", i)) or asyncio.sleep(0), remove_reaction=lambda e, u: reacts.append(("-", i)) or asyncio.sleep(0)))
s = {"ended": False, "char_name": "Hotaru-chan", "hook_ids": [9]}
asyncio.run(B.say(th, s, "*đoạn 1*\n\nđoạn 2\n\n*đoạn 3*\n\nđoạn 4"))
assert sent == ["*đoạn 1*", "đoạn 2", "*đoạn 3*", "đoạn 4"] and s["turn_ids"] == [101, 102, 103, 104] and reacts == [("+", 104)], (sent, s, reacts)
# đọc lịch sử: 4 tin của nhân vật gộp lại thành 1 lượt; người dùng chen giữa thì vẫn xếp đúng
C = lambda i, t: types.SimpleNamespace(id=i, author=types.SimpleNamespace(id=9, bot=True, display_name="H"), webhook_id=9, content="", embeds=[types.SimpleNamespace(description=t)])
U = lambda i, t: types.SimpleNamespace(id=i, author=types.SimpleNamespace(id=5, bot=False, display_name="An"), webhook_id=None, content=t, embeds=[])
class TH:
    def __init__(s, m): s.m, s.deleted = m, []
    def history(s, limit):
        async def g():
            for x in list(reversed(s.m))[:limit]: yield x
        return g()
S = lambda **k: dict({"hook_ids": [9], "char_name": "Hotaru-chan", "system_prompt": "sys", "summary": "", "summarized_upto_message_id": 0, "ended": False}, **k)
h = [U(1, "hi"), C(2, "p1"), C(3, "p2"), C(4, "p3"), C(5, "p4"), U(6, "tiếp")]
out, _ = asyncio.run(B.build_messages(TH(h), S()))
assert [m["role"] for m in out] == ["system", "user", "assistant", "user"] and out[2]["content"] == "p1\n\np2\n\np3\n\np4"
h = [U(1, "hi"), C(2, "p1"), C(3, "p2"), U(4, "chen ngang"), C(5, "p3"), C(6, "p4")]
out, _ = asyncio.run(B.build_messages(TH(h), S(last_input_id=1)))
assert [m["role"] for m in out] == ["system", "user", "assistant", "user"] and out[2]["content"] == "p1\n\np2\n\np3\n\np4" and out[3]["content"].startswith("[An]: chen ngang")
# viết lại: 🔄 vào đoạn bất kỳ -> xoá đủ 4 tin (kể cả khi người dùng chen giữa), trả lời lại "hi"
h = [U(1, "hi"), C(2, "p1"), C(3, "p2"), U(4, "chen"), C(5, "p3"), C(6, "p4")]
t = TH(h)
deleted = []
class Hook2:
    id = 9
    async def delete_message(self, mid, thread): deleted.append(mid); t.m[:] = [m for m in t.m if m.id != mid]
B.get_hook = lambda s: Hook2()
s = S(turn_ids=[2, 3, 5, 6], last_input_id=1); B.sessions["5"] = s; B.bot.get_channel = lambda c: t
got = []
async def grab(th_, s_, fallback=None): got.append((await B.build_messages(th_, s_), fallback))
B.respond = grab
asyncio.run(B.on_raw_reaction_add(types.SimpleNamespace(emoji=B.REROLL, channel_id=5, user_id=5, member=None, message_id=3)))
assert sorted(deleted) == [2, 3, 5, 6], deleted
(out, _), fb = got[0]
assert fb == "p1\n\np2\n\np3\n\np4" and [m["role"] for m in out] == ["system", "user", "user"], out
print("split ok")
