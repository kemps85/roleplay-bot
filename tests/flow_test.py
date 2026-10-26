import asyncio, sys, types, time, shutil, tempfile, subprocess, os, json
from aiohttp import web
import discord
sys.path.insert(0, r'C:\Users\ASUS\Documents\Discord\roleplay-bot')
import bot as B

calls = []
async def handler(req):
    d = await req.json(); m = d["model"]; calls.append(m)
    n = calls.count(m)
    if m == "m429": return web.Response(status=429, text='{"error":{"details":[{"retryDelay":"17s"}]}}')
    if m == "mday": return web.Response(status=429, text="quota GenerateRequestsPerDay")
    if m == "m503": return web.Response(status=503, text="busy")
    if m == "m503ok": return web.json_response({"choices": [{"message": {"content": "ok503"}}]}) if n > 1 else web.Response(status=503)
    if m == "mlen": return web.json_response({"choices": [{"message": {"content": "Câu một. Câu hai dở"}, "finish_reason": "length"}]})
    if m == "mgood": return web.json_response({"choices": [{"message": {"content": "good"}, "finish_reason": "stop"}]})
    return web.Response(status=500)

async def llm_test():
    app = web.Application(); app.router.add_post("/chat/completions", handler)
    run = web.AppRunner(app); await run.setup(); site = web.TCPSite(run, "127.0.0.1", 0); await site.start()
    B.BASE_URL = f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}"
    B.API_KEY = "x"
    B.MODELS = ["m429", "mday", "m503", "mgood", "m500"]
    r = await B.llm([])
    # 3 model max: m429, mday, m503 (2 calls) all fail -> None, no mgood
    assert r is None, r
    assert calls == ["m429", "mday", "m503", "m503"], calls
    assert 10 < B.bad_until["m429"] - time.monotonic() <= 17, B.bad_until["m429"] - time.monotonic()
    assert B.bad_until["mday"] - time.monotonic() > 3600
    assert 50 < B.bad_until["m503"] - time.monotonic() <= 60
    # next turn: benched are skipped -> mgood
    assert await B.llm([]) == "good" and "mgood" not in B.bad_until
    # 503 then ok, length trimming
    B.bad_until.clear(); calls.clear(); B.MODELS = ["m503ok"]
    t = time.monotonic(); assert await B.llm([]) == "ok503" and time.monotonic() - t >= 2 and "m503ok" not in B.bad_until
    B.MODELS = ["mlen"]; assert await B.llm([]) == "Câu một."
    await run.cleanup()

class NF(discord.NotFound):
    def __init__(self): pass

async def say_test():
    sent = []
    class Hook:
        def __init__(self, ok): self.ok = ok
        async def send(self, **kw):
            assert kw["allowed_mentions"] is B.AM and kw["username"] == "Nhân vật"
            if not self.ok: raise NF()
            sent.append(("hook", kw["embed"].description)); return types.SimpleNamespace(id=len(sent))
    made = []
    async def fake_make(ch, s):
        made.append(1); s["webhook_token"] = "t2"; return Hook(True)
    B.make_hook = fake_make
    B.save = lambda: None
    B.get_hook = lambda s: Hook(False) if s.get("webhook_token") else None
    th = types.SimpleNamespace(parent=None, get_partial_message=lambda i: types.SimpleNamespace(add_reaction=lambda e: B.asyncio.sleep(0), remove_reaction=lambda e, u: B.asyncio.sleep(0)))
    async def thsend(**kw): sent.append(("bot", kw["embed"].description)); return types.SimpleNamespace(id=len(sent))
    th.send = thsend
    s = {"ended": False, "char_name": "Discord", "webhook_token": "t1"}
    await B.say(th, s, "hi")
    assert sent == [("hook", "hi")] and made == [1] and s["webhook_token"] == "t2"
    # remade hook also dead -> only one recreate, then bot fallback
    sent.clear(); made.clear()
    B.make_hook = lambda ch, s: (made.append(1), asyncio.sleep(0, Hook(False)))[1]
    s["webhook_token"] = "t1"
    await B.say(th, s, "yo")
    assert sent == [("bot", "yo")] and made == [1], (sent, made)
    # ended: nothing
    sent.clear(); s["ended"] = True; await B.say(th, s, "x"); assert not sent

asyncio.run(llm_test()); asyncio.run(say_test())

# broken sessions.json -> renamed
d = tempfile.mkdtemp()
shutil.copy(r"C:\Users\ASUS\Documents\Discord\roleplay-bot\bot.py", d)
open(os.path.join(d, "sessions.json"), "w").write("{broken")
out = subprocess.run([sys.executable, "-c", "import bot"], cwd=d, capture_output=True, text=True, encoding="utf-8")
print(out.stdout.strip(), out.stderr[-300:])
assert not os.path.exists(os.path.join(d, "sessions.json")) and any(f.startswith("sessions.json.broken-") for f in os.listdir(d)), os.listdir(d)
shutil.rmtree(d)
print("flow ok")
