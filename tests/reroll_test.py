import asyncio, sys, types, contextlib
sys.path.insert(0, r'C:\Users\ASUS\Documents\Discord\roleplay-bot')
import bot as B
B.bot._connection.user = types.SimpleNamespace(id=1)
B.save = lambda: None  # không ghi đè sessions.json thật
h = []
def M(id, aid, wid, c, bot=False):
    m = types.SimpleNamespace(id=id, author=types.SimpleNamespace(id=aid, bot=bot, display_name="U"), webhook_id=wid, content=c, embeds=[])
    async def d(): h.remove(m)
    m.delete = d
    return m
async def hist(limit):
    for m in reversed(list(h)): yield m
th = types.SimpleNamespace(id=77, history=lambda limit: hist(limit), typing=lambda: contextlib.nullcontext())
class TC:
    async def __aenter__(self): pass
    async def __aexit__(self, *a): pass
th.typing = lambda: TC()
B.bot.get_channel = lambda i: th
async def hdel(mid, thread=None): h[:] = [m for m in h if m.id != mid]
B.get_hook = lambda s: types.SimpleNamespace(id=9, delete_message=hdel)
said, prompts = [], []
out = ["new reply"]
async def fake_llm(msgs): prompts.append(msgs); return out[0]
async def fake_say(t, s, text): said.append(text)
B.llm, B.say = fake_llm, fake_say
s = {"hook_ids": [9, 8], "webhook_id": 9, "char_name": "X", "system_prompt": "sys", "summary": "", "summarized_upto_message_id": 0, "ended": False, "last_input_id": 2}
B.sessions["77"] = s
c = lambda i, t="r", w=9: M(i, 99, w, t, True)
P = lambda mid, emoji="🔄", uid=5: types.SimpleNamespace(channel_id=77, message_id=mid, emoji=emoji, user_id=uid, member=None)
async def go():
    h[:] = [M(0, 1, None, "🎭 Phiên roleplay với ", True), c(1, "intro"), M(2, 5, None, "u1"), c(3, "bad part1"), c(4, "bad part2", 8)]
    await B.on_raw_reaction_add(P(1)); assert not said            # not latest turn
    await B.on_raw_reaction_add(P(4, "👍")); assert not said      # wrong emoji
    await B.on_raw_reaction_add(P(4, uid=1)); assert not said     # bot itself
    s["affinity"], s["aff_last"] = 50, 2  # lượt bị viết lại đã +2
    await B.on_raw_reaction_add(P(3))
    assert s["affinity"] == 48 and s["aff_last"] == 0, s  # hoàn điểm; "new reply" không có thẻ -> 0
    assert [m.id for m in h] == [0, 1, 2], [m.id for m in h]      # both parts deleted (webhook + old webhook)
    assert said == ["new reply"] and prompts[-1][-1]["role"] == "user" and prompts[-1][-1]["content"].startswith("[U]: u1")
    # intro only: no reroll
    said.clear(); h[:] = [M(0, 1, None, "🎭 Phiên roleplay với ", True), c(1, "intro")]
    await B.on_raw_reaction_add(P(1)); assert not said and len(h) == 2
    # reroll lượt có thẻ ♥: hoàn điểm cũ rồi cộng điểm mới, không đổi sang lượt khác
    out[0] = "new 2\n[♥+3]"; s["affinity"], s["aff_last"] = 50, 2; said.clear()
    h[:] = [M(0, 1, None, "🎭 Phiên roleplay với ", True), c(1, "intro"), M(2, 5, None, "u1"), c(3, "old")]
    await B.on_raw_reaction_add(P(3))
    assert said == ["new 2"] and s["affinity"] == 51 and s["aff_last"] == 3, (said, s)
    # reroll lượt đáp lại tin do nút gợi ý đăng (tác giả là webhook nhưng là tin người chơi): vẫn viết lại được, tên đúng
    out[0] = "again"; said.clear(); s["picked"] = {"2": 5}
    h[:] = [M(0, 1, None, "🎭 Phiên roleplay với ", True), c(1, "intro"), M(2, 99, 9, "đi dạo không?", True), c(3, "old")]
    await B.on_raw_reaction_add(P(3))
    assert said == ["again"] and [m.id for m in h] == [0, 1, 2] and prompts[-1][-1]["content"].startswith("[U]: đi dạo không?"), (said, prompts[-1][-1])
    s.pop("picked")
asyncio.run(go()); print("reroll ok")
