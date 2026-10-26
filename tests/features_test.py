"""//, giới hạn DAILY tin/ngày, /vai và /ghinho đi vào prompt, điểm thân mật."""
import asyncio, sys, types
sys.path.insert(0, r'C:\Users\ASUS\Documents\Discord\roleplay-bot')
import bot as B
B.save = lambda: None
B.bot._connection.user = types.SimpleNamespace(id=1)


def M(id, aid, c, wid=None, bot=False):
    return types.SimpleNamespace(id=id, author=types.SimpleNamespace(id=aid, bot=bot, display_name="U"), webhook_id=wid, content=c, embeds=[])


def TH(msgs):  # cũ -> mới
    async def h(limit):
        for m in reversed(msgs): yield m
    return types.SimpleNamespace(history=lambda limit: h(limit))


def S(**kw):
    return dict({"hook_ids": [9], "char_name": "X", "system_prompt": "sys", "summary": "", "summarized_upto_message_id": 0, "ended": False}, **kw)


async def go():
    real_llm = B.llm  # phần respond bên dưới thay B.llm bằng bản giả
    c = lambda i, t: M(i, 9, t, 9, True)
    # // bị bỏ qua: không phải input, không vào lịch sử
    assert not B.is_input(M(1, 5, "  // đi ăn cơm đã"))
    assert B.is_input(M(1, 5, "chào"))
    s = S()
    out, _ = await B.build_messages(TH([c(1, "hello"), M(2, 5, "chào"), M(3, 5, "// brb")]), s)
    assert [m["role"] for m in out] == ["system", "assistant", "user"] and "brb" not in str(out), out
    assert s["last_input_id"] == 2
    # chỉ có tin // mới -> không trả lời lại
    assert await B.build_messages(TH([c(1, "hello"), M(2, 5, "chào"), c(3, "r"), M(4, 5, "// lol")]), s) is None
    # thông báo hết lượt (bot gửi, tiền tố NOTICE) không vào lịch sử
    s = S()
    out, _ = await B.build_messages(TH([c(1, "hello"), M(2, 5, "a"), M(3, 1, B.NOTICE + "hết lượt", bot=True), M(4, 6, "b")]), s)
    assert "hết lượt" not in str(out), out

    # giới hạn: DAILY lượt được, lượt kế trả 0 (báo 1 lần), sau đó âm (im lặng); qua ngày reset
    B.usage.clear()
    assert [B.spend(7) for _ in range(B.DAILY)][-1] == 1
    assert B.spend(7) == 0 and B.spend(7) < 0
    assert B.spend(8) == B.DAILY  # người khác không ảnh hưởng
    B.usage[7] = ("2000-01-01", 999)
    assert B.spend(7) == B.DAILY

    # /vai và /ghinho nằm trong system prompt
    s = S(roles={"5": {"name": "Hotaru", "desc": "con trai, xưng tớ"}}, pins=["dị ứng sữa"])
    out, _ = await B.build_messages(TH([c(1, "hello"), M(2, 5, "chào")]), s)
    sysmsg = out[0]["content"]
    assert "Hotaru: con trai, xưng tớ" in sysmsg and "- dị ứng sữa" in sysmsg, sysmsg
    assert "ĐỘ THÂN MẬT với người chơi: 20/100 — quen biết." in B.extras(S()) and "Hotaru" not in B.extras(S())

    # lệnh /vai, /ghinho qua interaction giả
    sent = []
    async def send_message(msg=None, embed=None, ephemeral=False): sent.append(embed or msg)
    def IT(cid): return types.SimpleNamespace(channel_id=cid, user=types.SimpleNamespace(id=5, display_name="Hotaru"), response=types.SimpleNamespace(send_message=send_message))
    B.sessions.clear(); B.sessions["42"] = S(color=1)
    await B.vai.callback(IT(42), "con trai")
    assert B.sessions["42"]["roles"]["5"]["desc"] == "con trai"
    await B.vai.callback(IT(42), "-")
    assert B.sessions["42"]["roles"] == {}
    await B.ghinho.callback(IT(42), "A", None)
    await B.ghinho.callback(IT(42), "B", None)
    await B.ghinho.callback(IT(42), None, 1)
    assert B.sessions["42"]["pins"] == ["B"] and "1. B" in sent[-1].fields[0].value
    await B.ghinho.callback(IT(42), None, 5)
    assert sent[-1] == "Không có chi tiết số đó."
    await B.vai.callback(IT(99), "x")  # không phải thread phiên
    assert "chỉ dùng trong thread" in sent[-1]

    # trang trí: màu theo emoji cảm xúc, lời thoại in đậm (gỡ lại khi đọc lịch sử), thumbnail chỉ đoạn đầu
    s = {"color": 1}
    assert B.mood_color(s, "😳 *đỏ mặt*") == 0xFFB74D and B.mood_color(s, "❤️ thương") == 0xFF8FB1
    assert B.mood_color(s, "*cười*") == 1 and B.mood_color(s, "") == 1
    kw = B.char_kw(s, '*cười* "Chào cậu" rồi “đi thôi”', 5, False)
    d = kw["embed"].description
    assert '**"Chào cậu"**' in d and "**“đi thôi”**" in d and "file" not in kw and kw["embed"].color.value == 5, d
    assert B.undeco(d) == '*cười* "Chào cậu" rồi “đi thôi”'
    assert B.QUOTE.sub(r"**\1**", '**"a"**') == '**"a"**'  # đã đậm thì không đậm lại

    # điểm thân mật: tách thẻ, kẹp -3..3, thiếu thẻ = 0, bỏ MỌI thẻ khỏi text
    assert B.take_aff("😊 hi\n[♥+2]") == ("😊 hi", 2) and B.take_aff("hi [♥-1]") == ("hi", -1) and B.take_aff("hi\n[♥0]") == ("hi", 0)
    assert B.take_aff("hi\n[ ❤️ +3 ]") == ("hi", 3) and B.take_aff("hi\n[❤ -2]") == ("hi", -2)
    assert B.take_aff("hi\n[♥+9]")[1] == 3 and B.take_aff("hi\n[♥-9]")[1] == -3 and B.take_aff("hi") == ("hi", 0)
    assert B.take_aff("[♥+1] a\n\nb\n[♥-2]") == ("a\n\nb", -2) and "♥" not in B.take_aff("a [♥+1] b [♥+1]")[0]
    # tầng + extras
    for a, tier in ((0, "xa cách"), (19, "xa cách"), (20, "quen biết"), (44, "quen biết"), (45, "thân thiết"), (69, "thân thiết"), (70, "rất thân"), (89, "rất thân"), (90, "gắn bó"), (100, "gắn bó")):
        assert f"{a}/100 — {tier}" in B.extras(S(affinity=a)), (a, tier)

    # respond: áp delta, kẹp 0..100, fallback/FAIL không đổi điểm, thẻ không lên Discord
    real_say, said, replies = B.say, [], []
    async def fake_say(t, s, text): said.append(text)
    class TC:
        async def __aenter__(self): pass
        async def __aexit__(self, *a): pass
    async def fake_llm(msgs, **kw): return replies.pop(0)
    B.say, B.llm = fake_say, fake_llm
    async def turn(s, reply, fb=None, uid=2):
        th = TH([c(1, "hello"), M(uid, 5, "chào")]); th.typing = lambda: TC()
        replies[:] = [reply]
        await B.respond(th, s, fb)
    s = S()  # phiên cũ không có affinity -> 20
    await turn(s, "😊 *cười*\n[♥+2]")
    assert said[-1] == "😊 *cười*" and s["affinity"] == 22 and s["aff_last"] == 2, (said, s)
    await turn(s, "😠 hừ\n[♥-1]", uid=3)
    assert s["affinity"] == 21 and s["aff_last"] == -1
    await turn(s, "😐 ừ", uid=4)  # thiếu thẻ -> 0
    assert said[-1] == "😐 ừ" and s["affinity"] == 21 and s["aff_last"] == 0
    s = S(affinity=99); await turn(s, "🥰 a\n[♥+3]")
    assert s["affinity"] == 100 and s["aff_last"] == 1  # kẹp 100, aff_last là delta thực tế
    s = S(affinity=1); await turn(s, "😢 a\n[♥-3]")
    assert s["affinity"] == 0 and s["aff_last"] == -1
    s = S(affinity=50, aff_last=2); await turn(s, None)  # LLM hỏng -> FAIL, giữ nguyên điểm
    assert said[-1] == B.FAIL and s["affinity"] == 50 and s["aff_last"] == 0
    await turn(s, None, "câu cũ", uid=3)
    assert said[-1] == "câu cũ" and s["affinity"] == 50
    s = S(affinity=50); await turn(s, "[♥+3]")  # chỉ có thẻ -> FAIL, không cộng
    assert said[-1] == B.FAIL and s["affinity"] == 50 and s["aff_last"] == 0
    assert all("♥" not in x for x in said)

    # footer ở embed cuối của lượt (không ở đoạn trước), (+N) chỉ hiện khi delta != 0; msg_text không đọc footer
    B.say, embeds = real_say, []
    async def hsend(**kw): embeds.append(kw["embed"]); return types.SimpleNamespace(id=len(embeds))
    async def noop(*a, **k): pass
    B.get_hook = lambda s: types.SimpleNamespace(id=9, send=hsend)
    thx = types.SimpleNamespace(typing=lambda: TC(), get_partial_message=lambda i: types.SimpleNamespace(add_reaction=noop, remove_reaction=noop))
    await B.say(thx, S(affinity=42, aff_last=2), "đoạn 1\n\nđoạn 2")
    assert [e.footer.text for e in embeds] == [None, "💗 Thân mật 42/100 (+2)"], [e.footer.text for e in embeds]
    embeds.clear(); await B.say(thx, S(affinity=42, aff_last=-1), "một đoạn")
    assert embeds[0].footer.text == "💗 Thân mật 42/100 (-1)"
    embeds.clear(); await B.say(thx, S(affinity=42, aff_last=0), "một đoạn")
    assert embeds[0].footer.text == "💗 Thân mật 42/100"
    embeds.clear(); await B.say(thx, S(), "phiên cũ")
    assert embeds[0].footer.text == "💗 Thân mật 20/100"
    e = embeds[0]; e.description = "😊 *cười*"
    assert B.msg_text(M(1, 9, "", 9, True), S()) == "" and B.msg_text(types.SimpleNamespace(content="", embeds=[e], author=types.SimpleNamespace(id=9), webhook_id=9), S()) == "😊 *cười*"


    # ảnh: tin chỉ có ảnh vẫn là input (trừ khi //), tin mới nhất có part ảnh, tin cũ chỉ còn nhãn, tối đa 2 ảnh/lượt
    PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20
    def A(data=PNG, ct="image/png", size=None):
        async def rd(): return data
        return types.SimpleNamespace(content_type=ct, size=len(data) if size is None else size, read=rd)
    def MI(id, text, *atts, aid=5):
        m = M(id, aid, text); m.attachments = list(atts); return m
    assert B.is_input(MI(1, "", A())) and B.is_input(MI(1, "  ", A(ct="image/jpeg; charset=x")))
    assert not B.is_input(MI(1, "// brb", A())) and not B.is_input(MI(1, "", A(ct="application/pdf"))) and not B.is_input(MI(1, "", ))
    s = S(last_input_id=2)  # tin 2 (có ảnh) đã được trả lời; 3 chỉ có ảnh, 4 có chữ + ảnh
    out, _ = await B.build_messages(TH([c(1, "hello"), MI(2, "xem nè", A()), c(3, "ừ"), MI(4, "", A()), MI(5, "đây nữa", A())]), s)
    tag = B.IMG_TAG
    assert out[2]["content"] == f"[U]: xem nè {tag}", out[2]  # ảnh cũ: chuỗi thường + nhãn
    assert isinstance(out[-2]["content"], list) and isinstance(out[-1]["content"], list), out
    assert out[-2]["content"][0] == {"type": "text", "text": f"[U]: {tag}"}  # tin chỉ có ảnh -> "[Tên]: [gửi một ảnh]"
    assert out[-1]["content"][0]["text"].startswith(f"[U]: đây nữa {tag}") and "Ghi chú cho X" in out[-1]["content"][0]["text"]
    u = out[-1]["content"][1]["image_url"]["url"]
    assert out[-1]["content"][1]["type"] == "image_url" and u.startswith("data:image/png;base64,") and B.base64.b64decode(u.split(",", 1)[1]) == PNG
    assert "THỊ GIÁC" in out[0]["content"]
    # 3 ảnh mới: chỉ 2 ảnh của tin mới nhất được gửi, tin cũ hơn chỉ có nhãn
    out, _ = await B.build_messages(TH([c(1, "hello"), MI(2, "a", A()), MI(3, "b", A()), MI(4, "c", A(), A())]), S())
    assert isinstance(out[2]["content"], str) and tag in out[2]["content"] and isinstance(out[3]["content"], str), out
    assert sum(len(m["content"]) - 1 for m in out if isinstance(m["content"], list)) == 2 and len(out[-1]["content"]) == 3, out
    # quá 5MB / sai định dạng thật / tải lỗi: không có part ảnh, chỉ nhãn, không sập
    async def boom(): raise B.discord.HTTPException(types.SimpleNamespace(status=404, reason="x"), "x")
    bad = types.SimpleNamespace(content_type="image/png", size=10, read=boom)
    for att in (A(size=B.IMG_MAX + 1), A(data=b"not an image"), bad):
        out, _ = await B.build_messages(TH([c(1, "hello"), MI(2, "hi", att)]), S())
        assert isinstance(out[-1]["content"], str) and tag in out[-1]["content"], out[-1]
    # tin nhân vật có file đính kèm (thumbnail) không bị gắn nhãn / không tính là ảnh người chơi
    ch = c(1, "hello"); ch.attachments = [A()]
    out, _ = await B.build_messages(TH([ch, M(2, 5, "chào")]), S())
    assert out[1]["content"] == "hello", out

    # llm: gemini nhận list nguyên vẹn, model khác chỉ nhận chữ (không còn list); CJK check đọc phần text của list
    sent_bodies, resp = [], []
    class R2:
        status, headers = 200, {}
        async def __aenter__(self): return self
        async def __aexit__(self, *e): pass
        async def json(self, content_type=None): return {"choices": [{"message": {"content": resp.pop(0)}, "finish_reason": "stop"}]}
    class CS2:
        async def __aenter__(self): return self
        async def __aexit__(self, *e): pass
        def post(self, url, headers, json, timeout): sent_bodies.append(json); return R2()
    real_cs, real_models = B.aiohttp.ClientSession, B.MODELS[:]
    B.aiohttp.ClientSession = CS2
    try:
        msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": [{"type": "text", "text": f"[An]: {tag}"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]}]
        for model, as_list in (("gemini-3.8-flash", True), ("gpt-oss-120b", False)):
            B.MODELS[:] = [model]; B.bad_until.clear(); sent_bodies.clear(); resp[:] = ["ok"]
            assert await real_llm(msgs) == "ok"
            got = sent_bodies[0]["messages"][-1]["content"]
            assert (isinstance(got, list) and got[1]["type"] == "image_url") if as_list else got == f"[An]: {tag}", (model, got)
        assert msgs[1]["content"][1]["type"] == "image_url"  # không sửa messages gốc
        B.MODELS[:] = ["gemini-3.8-flash"]; B.bad_until.clear(); resp[:] = ["こんにちは"]
        assert await real_llm(msgs) is None  # người chơi không viết CJK (chỉ có part text + ảnh) -> bỏ câu CJK
        B.bad_until.clear(); resp[:] = ["こんにちは"]
        msgs[1]["content"][0]["text"] = "[An]: こんにちは"
        assert await real_llm(msgs) == "こんにちは"
    finally:
        B.aiohttp.ClientSession, B.MODELS[:], B.llm = real_cs, real_models, real_llm
        B.bad_until.clear()
    assert B.flat("abc") == "abc" and B.flat([{"type": "text", "text": "a"}, {"type": "image_url", "image_url": {}}, {"type": "text", "text": "b"}]) == "a\nb"

    # gợi ý ">>": tách khỏi text cùng thẻ ♥, tối đa 4, cắt 80, không có dòng nào -> không có nút
    assert B.take_sugg("hi\n>> a\n>> b\n>> c\n>> d") == ("hi", ["a", "b", "c", "d"])
    assert B.take_sugg("t\n>> 1\n>> 2\n>> 3\n>> 4\n>> 5\n>> 6")[1] == ["1", "2", "3", "4"]  # kẹp 4
    t6, g6 = B.take_sugg("a\n>> " + "x" * 100 + "\n\nb"); assert t6 == "a\n\nb" and g6 == ["x" * 80], (t6, g6)  # dòng ở giữa truyện: bỏ nguyên dòng, trim 80
    assert B.take_sugg("hi\n  - >>x\n*  >>   y  \n>>\n>> ") == ("hi", ["x", "y"])  # tolerant: bullet, thiếu/thừa cách, bỏ dòng rỗng
    assert B.take_sugg("chuyện thường > không phải gợi ý") == ("chuyện thường > không phải gợi ý", []) and B.take_sugg("") == ("", [])
    raw = "😊 *cười*\n\n>> Ngọt\n>> *nháy mắt* Tinh nghịch\n>> Tò mò?\n>> Táo bạo\n[♥+2]"
    t7, d7 = B.take_aff(raw); t7, g7 = B.take_sugg(t7)
    assert (t7, d7, len(g7)) == ("😊 *cười*", 2, 4) and "♥" not in t7 and ">>" not in t7
    # respond: sugg lưu vào s, không lọt vào chữ lên Discord; FAIL/fallback/chỉ-có-gợi-ý -> sugg rỗng
    B.say, B.llm = fake_say, fake_llm
    s = S(); await turn(s, raw)
    assert said[-1] == "😊 *cười*" and s["sugg"] == ["Ngọt", "*nháy mắt* Tinh nghịch", "Tò mò?", "Táo bạo"] and s["affinity"] == 22, (said[-1], s)
    await turn(s, "😐 ừ", uid=3); assert s["sugg"] == [] and said[-1] == "😐 ừ"  # không có dòng gợi ý -> không nút
    await turn(s, "x\n>> a", uid=4); assert s["sugg"] == ["a"]
    await turn(s, ">> a\n[♥+1]", uid=5); assert said[-1] == B.FAIL and s["sugg"] == []  # chỉ có gợi ý = không có truyện
    await turn(s, None, "câu cũ", uid=6); assert said[-1] == "câu cũ" and s["sugg"] == []
    assert all(">>" not in x for x in said)
    assert "TRƯỚC dòng [♥N]" in B.CONTINUITY  # prompt yêu cầu 4 dòng ">> " trước thẻ ♥

    # say: view chỉ ở tin cuối, gỡ view ở tin gợi ý của lượt trước, không gợi ý -> không view
    B.say, kws, edits = real_say, [], []
    async def hsend2(**kw): kws.append(kw); return types.SimpleNamespace(id=100 + len(kws))
    async def hedit(mid, **kw): edits.append((mid, kw))
    B.get_hook = lambda s: types.SimpleNamespace(id=9, send=hsend2, edit_message=hedit)
    s = S(sugg=["Một", "Hai"])
    await B.say(thx, s, "đoạn 1\n\nđoạn 2")
    assert "view" not in kws[0] and [b.label for b in kws[1]["view"].children] == ["Một", "Hai"], kws
    assert [b.custom_id for b in kws[1]["view"].children] == ["sug:0", "sug:1"] and s["sugg_msg"] == 102 and not edits
    s["sugg"] = ["Ba"]; await B.say(thx, s, "lượt sau")
    assert s["sugg_msg"] == 103 and edits == [(102, {"view": None, "thread": thx})], edits  # gỡ nút lượt cũ
    s["sugg"] = []; await B.say(thx, s, "không gợi ý")
    assert "view" not in kws[-1] and s["sugg_msg"] is None and edits[-1][0] == 103
    assert [b.custom_id for b in B.SugView().children] == [f"sug:{i}" for i in range(4)] and B.SugView().is_persistent()  # bản persistent đăng ký ở setup_hook

    # tin picked (nút gợi ý đăng hộ) = tin người chơi, đúng tên, không phải nhân vật
    def W(id, text, name, wid=9, aid=9, bot=True):
        m = M(id, aid, text, wid, bot); m.author.display_name = name; return m
    s = S(picked={"5": 77, "7": 78})
    wm, bm, ch = W(5, "hay lắm", "Hotaru"), W(7, "**An:** xin chào", "RP bot", wid=None, aid=1), c(3, "ừ")
    assert B.is_input(wm, s) and B.is_input(bm, s) and not B.is_input(wm) and not B.is_input(wm, S())  # on_message (không s) bỏ qua tin webhook
    assert not B.is_char(wm, s) and not B.is_char(bm, s) and B.is_char(ch, s) and B.is_char(W(6, "x", "RP", wid=None, aid=1), s)
    assert B.msg_text(wm, s) == "hay lắm" and B.msg_text(bm, s) == "xin chào" and B.who(wm, s) == "Hotaru" and B.who(bm, s) == "An" and B.who(ch, s) == "X"
    s["last_input_id"] = 0
    out, _ = await B.build_messages(TH([c(1, "hello"), wm, c(6, "r"), bm]), s)
    assert [(m["role"], m["content"][:14]) for m in out[1:]] == [("assistant", "hello"), ("user", "[Hotaru]: hay "), ("assistant", "r"), ("user", "[An]: xin chào")], out
    assert "Ghi chú cho X" in out[-1]["content"] and "'tớ/tôi/mình' là An" in out[-1]["content"] and s["last_input_id"] == 7
    assert await B.build_messages(TH([c(1, "hello"), wm, c(6, "r"), bm, c(8, "reply")]), s) is None  # đã trả lời tin picked mới nhất
    assert await B.build_messages(TH([c(1, "hello"), W(5, "hay lắm", "Hotaru")]), S()) is None  # tin webhook không picked vẫn là nhân vật, không phải input

    # nút gợi ý: phiên hết/stale/hết lượt bị từ chối; hợp lệ thì đăng webhook theo tên+avatar người bấm, ghi picked, gọi respond; bấm đúp = cũ
    ev, posted, resp, real_respond = [], [], [], B.respond
    async def smsg(msg=None, ephemeral=False): ev.append((msg, ephemeral))
    async def defer(): ev.append("defer")
    async def eor(view=None): ev.append(("eor", view))
    async def fsend(msg, ephemeral=False): ev.append((msg, ephemeral))
    async def psend(text, **kw): posted.append((text, kw)); return types.SimpleNamespace(id=500 + len(posted))
    async def fake_respond(th, s, fb=None): resp.append(dict(s["picked"]))
    B.respond, thp = fake_respond, types.SimpleNamespace(id=42)
    B.get_hook = lambda s: types.SimpleNamespace(id=9, send=psend)
    def CLK(mid, uid=5, cid=42):
        u = types.SimpleNamespace(id=uid, display_name="Hotaru", display_avatar=types.SimpleNamespace(url="http://av"))
        return types.SimpleNamespace(channel=thp, channel_id=cid, message=types.SimpleNamespace(id=mid), user=u, response=types.SimpleNamespace(send_message=smsg, defer=defer),
                                     edit_original_response=eor, followup=types.SimpleNamespace(send=fsend))
    B.sessions.clear(); B.usage.clear()
    await B.pick_sugg(CLK(1, cid=99), 0); assert ev.pop() == ("Phiên này không còn hoạt động.", True)
    B.sessions["42"] = s = S(ended=True, sugg=["a", "b"], sugg_msg=10)
    await B.pick_sugg(CLK(10), 0); assert ev.pop() == ("Phiên này không còn hoạt động.", True)
    s["ended"] = False
    await B.pick_sugg(CLK(9), 0); assert ev.pop() == ("Gợi ý cũ rồi nha", True) and not posted and s["sugg_msg"] == 10  # nút của lượt cũ
    await B.pick_sugg(CLK(10), 2); assert ev.pop() == ("Gợi ý cũ rồi nha", True) and not posted  # chỉ số ngoài danh sách gợi ý hiện tại
    B.usage[5] = (B.time.strftime("%Y-%m-%d"), B.DAILY)  # hết lượt: báo ephemeral, nút vẫn còn cho người khác bấm
    await B.pick_sugg(CLK(10), 1); assert ev.pop() == (f"{B.NOTICE}hết {B.DAILY} tin hôm nay rồi, mai chơi tiếp nha!", True) and s["sugg_msg"] == 10 and not posted
    B.usage.clear()
    await B.pick_sugg(CLK(10), 1)
    assert posted == [("b", dict(username="Hotaru", avatar_url="http://av", thread=thp, wait=True, allowed_mentions=B.AM))], posted
    assert s["picked"] == {"501": 5} and s["sugg_msg"] is None and resp == [{"501": 5}] and ev[-2:] == ["defer", ("eor", None)], (s, resp, ev)
    await B.pick_sugg(CLK(10), 1); assert ev.pop() == ("Gợi ý cũ rồi nha", True) and len(posted) == 1  # bấm đúp
    s["sugg_msg"] = 11; s["picked"] = {str(i): 1 for i in range(200)}  # cap 200: bỏ cũ nhất
    await B.pick_sugg(CLK(11), 0); assert len(s["picked"]) == 200 and "0" not in s["picked"] and s["picked"]["502"] == 5
    B.get_hook = lambda s: None  # không webhook: bot gửi "**Tên:** chữ" và vẫn được nhận là tin người chơi
    sent_bot = []
    async def tsend(text, **kw): sent_bot.append(text); return types.SimpleNamespace(id=900)
    thp.send = tsend; s["sugg_msg"] = 12
    await B.pick_sugg(CLK(12), 0); assert sent_bot == ["**Hotaru:** a"] and s["picked"]["900"] == 5
    B.respond = real_respond

asyncio.run(go()); print("features ok")
