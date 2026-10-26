import asyncio, sys, types, discord
sys.path.insert(0, r'C:\Users\ASUS\Documents\Discord\roleplay-bot')
import bot as B
B.bot._connection.user = types.SimpleNamespace(id=1)
B.save = lambda: None  # không ghi đè sessions.json thật
log, n = [], [100]
class FakeResp:
    status = 404; reason = "x"
async def send(**kw):
    n[0] += 1; return types.SimpleNamespace(id=n[0])
B.get_hook = lambda s: types.SimpleNamespace(id=9, send=send)
B.char_kw = lambda s, p, *a: {}
def gpm(i):
    async def add(e): log.append(("add", i))
    async def rem(e, u):
        if i == 101: raise discord.NotFound(FakeResp(), "gone")
        log.append(("rem", i))
    return types.SimpleNamespace(add_reaction=add, remove_reaction=rem)
th = types.SimpleNamespace(get_partial_message=gpm, parent=None)
s = {"ended": False, "char_name": "X"}
async def go():
    await B.say(th, s, "a"); assert log == [("add", 101)] and s["reroll_id"] == 101
    await B.say(th, s, "b"); assert log[-1] == ("add", 102), log   # old 101 deleted -> remove fails, add still happens
    await B.say(th, s, "c"); assert log[-2:] == [("rem", 102), ("add", 103)], log
asyncio.run(go()); print("say ok")
