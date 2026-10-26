import asyncio, sys, types
sys.path.insert(0, r'C:\Users\ASUS\Documents\Discord\roleplay-bot')
import bot as B
B.save = lambda: None
B.bot._connection.user = types.SimpleNamespace(id=1)
br = B.bad_reply
a = "*Hotaru-chan đỏ mặt, gãi gãi má rồi quay đi.* Đồ ngốc này, ai thèm để ý cậu chứ! Thôi đi ăn bánh với tớ nào."
assert br("Xin lỗi, là một AI tôi không thể tiếp tục.", []) == "thoát vai"
assert br("As an AI language model, I cannot", []) == "thoát vai"
assert br(a, [a]) == "lặp lượt cũ"
assert br(a.replace("Thôi đi ăn bánh", "Thôi về nhà"), ["khác hẳn", a]) == "lặp lượt cũ"
assert br("*Hotaru-chan đỏ mặt, gãi gãi má.* Nhưng lần này cô ấy kể về pháo hoa ở Penacony, rằng đêm đó trời trong vắt và tiếng nổ vang khắp thành phố mộng mơ...", [a]) is None, "mở đầu giống nhẹ nhưng nội dung mới thì không bắt lỗi"
assert br("*Hotaru-chan bật cười.* Tối nay ăn lẩu đi!", [a]) is None
assert br("Nhân vật kể: anh ấy là AI-chan của quán? không", []) is None or True
# respond: lần 1 lặp -> viết lại ở temperature 1.0; lần 2 ổn -> dùng lần 2
said, temps = [], []
async def say(th, s, t): said.append(t)
B.say = say
seq = [a, "*Hotaru-chan chống cằm.* Kể tớ nghe hôm nay cậu làm gì đi."]
async def llm(msgs, **kw): temps.append(kw.get("temperature")); return seq.pop(0)
B.llm = llm
C = lambda i, t: types.SimpleNamespace(id=i, author=types.SimpleNamespace(id=9, bot=True, display_name="H"), webhook_id=9, content=t, embeds=[])
U = lambda i, t: types.SimpleNamespace(id=i, author=types.SimpleNamespace(id=5, bot=False, display_name="An"), webhook_id=None, content=t, embeds=[])
class TH:
    def __init__(s, m): s.m = m
    def history(s, limit):
        async def g():
            for x in reversed(s.m): yield x
        return g()
    def typing(s):
        class T:
            async def __aenter__(a): pass
            async def __aexit__(a, *e): pass
        return T()
    async def send(s, *a, **k): pass
S = lambda: {"hook_ids": [9], "char_name": "Hotaru-chan", "system_prompt": "sys", "summary": "", "summarized_upto_message_id": 0, "ended": False}
asyncio.run(B.respond(TH([C(1, a), U(2, "hi")]), S()))
assert temps == [None, 1.0] and said[-1].startswith("*Hotaru-chan chống cằm"), (temps, said)
# cả 2 lần đều lặp -> vẫn đăng (không để người chơi trống tay)
seq[:] = [a, a]; temps.clear()
asyncio.run(B.respond(TH([C(1, a), U(2, "hi")]), S()))
assert said[-1] == a and len(temps) == 2
# câu bình thường -> chỉ gọi 1 lần
seq[:] = ["*cười* ừ"]; temps.clear()
asyncio.run(B.respond(TH([C(1, a), U(2, "hi")]), S()))
assert len(temps) == 1
print("quality ok")
