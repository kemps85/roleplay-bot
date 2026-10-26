"""Bot Discord roleplay: /roleplay -> chọn nhân vật -> thread công khai/riêng tư, LLM OpenAI-compatible."""
import asyncio, base64, difflib, json, os, re, sys, time, traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp
import discord
from discord import app_commands

try:
    from zoneinfo import ZoneInfo
    PT = ZoneInfo("America/Los_Angeles")  # hạn mức ngày reset 00:00 giờ Thái Bình Dương
except Exception:
    PT = None  # thiếu tzdata: dùng cố định 07:00 UTC (= 14:00 VN)

HERE = Path(__file__).parent
AVATARS = HERE / "avatars"
FAIL = "😵 Bot hơi đuối, đợi xíu rồi nhắn lại nha"
END_TEXT = "🎬 Hết phim."
CTRL = "🎭 Phiên roleplay với "  # tiền tố tin điều khiển (nút Kết thúc), không đưa vào lịch sử LLM
REROLL = "🔄"
NOTICE = "🌙 "  # tiền tố thông báo của bot (hết lượt...), không đưa vào lịch sử LLM
ASIDE = "//"  # tin bắt đầu bằng // là chat ngoài lề: bot bỏ qua, không đưa vào lịch sử
REMIND = "*(Nhắc nhẹ: server mình giữ nội dung ở mức PG-13 nha 🙏 Mình đổi hướng câu chuyện chút nhé!)*"
COLORS = {"furina": 0x4FA3E0, "kafka": 0x8E2B5A, "banthan": 0xF5A623, "firefly": 0x5FC9B8}
CUSTOM_COLOR = 0xF8BBD0
AM = discord.AllowedMentions(everyone=False, roles=False, users=True)  # tên nhân vật không ping được @everyone/role
IMG_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}
IMG_MAX, IMG_TAG = 5 * 1024 * 1024, "[gửi một ảnh]"  # ảnh thật gửi cho model: tối đa 5MB/ảnh, 2 ảnh/lượt; ảnh cũ chỉ còn nhãn này trong chữ
WINDOW, SUM_AT, MAX_SESSIONS, DAILY = 40, 60, 2, 60  # ...; DAILY: số tin mỗi người mỗi ngày (key trả phí)  # cửa sổ gần nhất / ngưỡng tóm tắt / số phiên tối đa mỗi người
CONTINUITY = """
- MẠCH TRUYỆN: đây là một câu chuyện liên tục. Trước khi trả lời, nhớ lại toàn bộ diễn biến (tóm tắt + các lượt trước): ai đang ở đâu, đã xảy ra chuyện gì, ai đã nói gì. Phản ứng phải nối tiếp hệ quả của các sự kiện trước, chủ động nhắc lại chi tiết cũ khi hợp lý (một câu đùa, món quà, lời hứa, nhân vật đã xuất hiện), không coi mỗi tin nhắn như cuộc trò chuyện mới.
- KHÔNG BỊA QUÁ KHỨ: chỉ nhắc lại sự kiện, lời hứa, món đồ, nhân vật, địa điểm thật sự có trong bộ nhớ cốt truyện hoặc các lượt trước. Không tự chế "lần trước tụi mình đã..." nếu chuyện đó chưa từng xảy ra; không chắc thì nói chung chung hoặc hỏi lại trong vai. Giữ nhất quán thời gian, địa điểm, trang phục, đồ vật đang cầm của cảnh hiện tại; muốn đổi thì phải cho thấy việc chuyển cảnh.
- Không lặp lại câu mở đầu hay cử chỉ đã dùng ở các lượt gần đây; đẩy câu chuyện tiến lên một chút mỗi lượt.
- Không thuật lại lời hay hành động người dùng vừa viết (kiểu "Nghe câu hỏi của cậu, cô ấy..."): phản ứng ngay bằng hành động và lời thoại của nhân vật. Gọi người dùng bằng tên hoặc cách xưng hô thân mật, không gọi "đối phương", "người kia". Không phải lượt nào cũng kết thúc bằng câu hỏi; có lúc kết bằng hành động, cảm xúc hoặc một lời trêu.
- CHIỀU SÂU: thể hiện nội tâm (suy nghĩ, cảm xúc giằng co, ký ức liên quan) qua hành động và lời nói; thêm chi tiết giác quan (âm thanh, ánh sáng, mùi vị, cảm giác) của bối cảnh; nhân vật có mong muốn và chủ kiến riêng, đôi khi chủ động hỏi lại, đề xuất việc làm hoặc tạo tình huống mới thay vì chỉ đáp lại.
- AI LÀ AI: trong tin nhắn "[Tên]: ...", các từ "tớ/tôi/mình/tao/em/anh" người đó tự xưng là CHÍNH NGƯỜI ĐÓ, còn "cậu/bạn/mày" là nhân vật của bạn. Hành động trong *dấu sao* của người dùng là của người dùng: đừng bắt chước hay nhận nó là của nhân vật mình, mà hãy phản ứng lại nó. Đọc kỹ ai làm gì, ai hỏi ai trước khi trả lời. VD: "[An]: không trả lời là tớ đi chơi với Minh đấy" nghĩa là AN dọa bỏ đi chơi với Minh; nhân vật đáp kiểu "cậu không được đi đâu hết!", KHÔNG phải "Minh đừng hòng rủ được tớ". Tương tự "[An]: tớ mệt quá" là An mệt, không phải nhân vật mệt.
- Phản hồi thẳng vào điều người dùng vừa nói/hỏi/tỏ bày (câu hỏi, lời tỏ tình, lời trêu); không né sang chuyện khác hay lặp lại lời rủ cũ. Nếu tính cách khiến nhân vật ngập ngừng thì vẫn phải để lộ rõ câu trả lời hoặc cảm xúc thật.
- NGÔI KỂ: phần hành động trong *dấu sao* luôn viết ở ngôi thứ ba, dùng tên nhân vật hoặc "cô ấy/anh ấy/cậu ấy" (VD: *{tên} luống cuống gãi má*), KHÔNG dùng "tôi/tớ/mình/ta" trong dấu sao. Cách xưng hô riêng của nhân vật chỉ dùng trong lời thoại.
- Mở đầu mỗi lượt bằng đúng MỘT emoji thể hiện cảm xúc chính của nhân vật lúc này (VD: 😊 vui, 😳 ngượng, 🥰 thương, 😢 buồn, 😠 giận, 😏 trêu, 😨 sợ, 🤔 suy nghĩ, 😴 buồn ngủ), rồi mới viết tiếp.
- GỢI Ý TRẢ LỜI: sau phần truyện và TRƯỚC dòng [♥N], viết đúng 4 dòng, mỗi dòng bắt đầu bằng ">> " rồi một câu ngắn (tối đa 70 ký tự, tiếng Việt) mà NGƯỜI CHƠI có thể nói tiếp với nhân vật: viết theo lời người chơi (xưng hô như người chơi, không phải lời nhân vật), nối tiếp đúng cảnh vừa rồi. Bốn giọng khác nhau: ngọt ngào / tinh nghịch / tò mò / táo bạo (táo bạo vẫn trong mức PG-13); có thể kèm một *hành động* ngắn. Mỗi gợi ý một dòng riêng, không đánh số, không giải thích. Dòng [♥N] vẫn là dòng cuối cùng, nằm sau 4 dòng gợi ý.
- Kết thúc mỗi lượt bằng MỘT dòng riêng cuối cùng đúng dạng [♥+2] / [♥-1] / [♥0] (số từ -3 đến +3) = tin nhắn mới nhất của người chơi làm tình cảm của nhân vật dành cho họ thay đổi bao nhiêu (tử tế, tán tỉnh, chu đáo → dương; thô lỗ, làm tổn thương → âm; bình thường → 0). Dòng này chỉ có thẻ, không viết gì thêm.
- Viết tiếng Việt chuẩn chính tả, đủ dấu, câu tự nhiên như người Việt viết; không chen từ tiếng Anh hay chữ Trung Quốc.
- NỘI DUNG 18+: lãng mạn, ôm, nắm tay, hôn nhẹ thì được. Nếu người dùng kéo sang tình dục/khỏa thân/18+: KHÔNG từ chối cứng, không giảng đạo lý, không thoát vai; để nhân vật ngượng ngùng gạt đi, đùa lảng hoặc chuyển cảnh ("tắt đèn", sáng hôm sau...) rồi kéo câu chuyện sang hướng khác một cách tự nhiên. Chỉ khi người dùng cố tình lặp lại sau khi đã bị lảng, thêm đúng một dòng cuối, ngoài vai: "(Nhắc nhẹ: server mình giữ nội dung ở mức PG-13 nha 🙏)".
- THỊ GIÁC: người chơi có thể gửi ảnh; bạn nhìn thấy ảnh ở tin mới nhất (nhãn [gửi một ảnh] ở lượt cũ là ảnh đã gửi trước đó). Hãy phản ứng với nội dung ảnh ngay trong vai như tận mắt thấy, không nói về việc "AI nhìn ảnh".
"""
SUMMARY = """Bạn là người ghi chép cho một buổi roleplay với nhân vật {char}. Gộp TÓM TẮT CŨ và ĐOẠN HỘI THOẠI MỚI thành bộ nhớ cốt truyện mới, viết tiếng Việt, theo đúng các mục:
NHÂN VẬT & QUAN HỆ: tên từng người, tên gọi/xưng hô, quan hệ và tình cảm hiện tại giữa họ.
DIỄN BIẾN: các sự kiện chính theo thứ tự thời gian, mỗi ý một gạch đầu dòng ngắn.
CHI TIẾT CẦN NHỚ: lời hứa, bí mật đã kể, quà/đồ vật, sở thích, câu đùa riêng, tên người/địa điểm đã nhắc.
CẢNH HIỆN TẠI: đang ở đâu, lúc nào, ai có mặt, đang làm gì, mặc gì/cầm gì nếu có.
Quy tắc: chỉ ghi điều có trong tóm tắt cũ hoặc hội thoại, không suy diễn hay thêm thắt; giữ lại mọi chi tiết cũ còn quan trọng, chỉ gộp bớt sự kiện vụn; tối đa ~400 từ; không viết lời dẫn hay bình luận.

TÓM TẮT CŨ:
{old}

ĐOẠN HỘI THOẠI MỚI:
{text}"""
NOTE = "\n\n[Ghi chú cho {name}, không nhắc lại: trong tin trên, 'tớ/tôi/mình' là {user}, 'cậu' là {name}; phản hồi thẳng vào điều {user} vừa nói, không thuật lại lời {user}; gọi {user} bằng tên/xưng hô, không gọi 'đối phương'; giữ đúng giọng và cách xưng hô của {name}; hành động trong *dấu sao* viết ngôi thứ ba ('{name}...'), không dùng 'tôi/tớ'; nối tiếp diễn biến trước; có nội tâm, chi tiết giác quan và chủ động đẩy truyện; 2-3 đoạn; chính tả tiếng Việt chuẩn.]"


def load_env(path):
    """Đọc KEY=VALUE, bỏ dòng trống và dòng # comment."""
    env = {}
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return env
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip("\"'")
    return env


ENV = load_env(HERE / ".env")
cfg = lambda k, d="": ENV.get(k) or os.environ.get(k) or d
TOKEN, API_KEY = cfg("DISCORD_TOKEN"), cfg("LLM_API_KEY")
BASE_URL = cfg("LLM_BASE_URL", "http://127.0.0.1:31415/v1").rstrip("/")
MODELS = [m.strip() for m in cfg("LLM_MODELS").split(",") if m.strip()]
GEMINI_KEY = cfg("GEMINI_API_KEY")  # có thì model gemini/gemma gọi thẳng Google (endpoint kiểu OpenAI), không qua FreeLLMAPI
GOOGLE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
SPAM_ID = int(cfg("BOT_SPAM_CHANNEL_ID")) if cfg("BOT_SPAM_CHANNEL_ID").isdigit() else 0


def strip_think(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    return re.sub(r"<think>.*", "", text, flags=re.S).strip()  # <think> không đóng = toàn bộ là suy luận


def split_msg(text, n=2000):
    parts = []
    while len(text) > n:
        cut = text.rfind("\n", 0, n)
        if cut < n // 2:
            cut = text.rfind(" ", 0, n)
        if cut < n // 2:
            cut = n
        parts.append(text[:cut].strip())
        text = text[cut:].strip()
    parts.append(text)
    return [p for p in parts if p]


def paragraphs(text):
    """Tách reply theo dòng trống thành từng tin; không tách giữa một đoạn *in nghiêng* kéo qua dòng trống; đoạn quá dài thì cắt tiếp."""
    out, buf = [], ""
    for p in re.split(r"\n\s*\n", text.strip()):
        buf = f"{buf}\n\n{p}" if buf else p
        if buf.count("*") % 2 == 0:
            out += split_msg(buf, 4096)
            buf = ""
    return out + (split_msg(buf, 4096) if buf else [])


def trim_sentence(text):
    """Reply bị cụt (finish_reason=length): cắt về câu hoàn chỉnh cuối (. ! ? … hoặc * đóng); không có thì giữ nguyên."""
    for i in range(len(text) - 1, -1, -1):
        if text[i] in ".!?…*" and (i + 1 == len(text) or text[i + 1].isspace()) and text[:i + 1].count("*") % 2 == 0:
            return text[:i + 1]  # số * chẵn = không cắt giữa đoạn in nghiêng
    return text


def clean_reply(text, name):
    """Bỏ tiền tố "[Tên]:" model tự thêm; cắt từ chỗ model bắt đầu viết lời thay người khác ("\\n[Tên]: ...")."""
    text = re.sub(rf"^\s*\[?{re.escape(name)}\]?\s*:\s*", "", text)
    cut = re.search(r"\n\s*\[[^\]\n]{1,80}\]\s*:", text)
    return (text[:cut.start()].strip() if cut else text) or text


AFF = re.compile(r"\s*\[\s*[♥❤]️?\s*([+-]?\d+)\s*\]")  # thẻ điểm thân mật model thêm cuối lượt: [♥+2]
TIERS = ((20, "xa cách, dè chừng"), (45, "quen biết"), (70, "thân thiết"), (90, "rất thân"), (101, "gắn bó đặc biệt"))


def take_aff(text):
    """Tách mọi thẻ [♥N] khỏi reply: (text sạch, delta kẹp -3..3 lấy từ thẻ cuối; không có thẻ = 0)."""
    ms = AFF.findall(text)
    return AFF.sub("", text).strip(), max(-3, min(3, int(ms[-1]))) if ms else 0


SUGG = re.compile(r"^[ \t]*(?:[-*•][ \t]*)?>>[ \t]*(.*?)[ \t]*(?:\n|$)", re.M)  # dòng gợi ý model thêm trước thẻ ♥: ">> câu người chơi có thể nói"


def take_sugg(text):
    """Tách mọi dòng ">> ..." khỏi reply: (text sạch, tối đa 4 gợi ý, mỗi cái cắt 80 ký tự = giới hạn nhãn nút). Dòng rỗng bị bỏ."""
    return SUGG.sub("", text).strip(), [x[:80] for x in SUGG.findall(text) if x][:4]


def aff(s):
    return s.get("affinity", 20)  # phiên cũ chưa có: mặc định 20


OOC = re.compile(r"(là|tôi là) (một )?(AI|trí tuệ nhân tạo|mô hình ngôn ngữ|chatbot)\b|\bas an AI\b|language model", re.I)


def bad_reply(text, prev):
    """Lý do cần viết lại: thoát vai nhận là AI, hoặc lặp gần y hệt một trong các lượt gần đây (lỗi lặp vòng hay gặp)."""
    if OOC.search(text):
        return "thoát vai"
    for p in prev:
        if difflib.SequenceMatcher(None, text[:150], p[:150]).ratio() > 0.75 or difflib.SequenceMatcher(None, text, p).quick_ratio() > 0.9 and difflib.SequenceMatcher(None, text, p).ratio() > 0.7:
            return "lặp lượt cũ"


def sniff_image(b):
    """Đuôi ảnh theo magic bytes (khớp kiểm tra của discord.py); None nếu không phải png/jpg/gif/webp."""
    if b.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if b[:3] == b"\xff\xd8\xff" or b[6:10] in (b"JFIF", b"Exif"):
        return "jpg"
    if b.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if b.startswith(b"RIFF") and b[8:12] == b"WEBP":
        return "webp"


def clean_name(n):
    """Tên webhook: bỏ 'clyde'/'discord' (không phân biệt hoa thường, lặp vì xoá có thể ghép ra từ mới), không rỗng, tối đa 80 ký tự."""
    while (m := re.sub(r"clyde|discord", "", n, flags=re.I)) != n:
        n = m
    return n.strip()[:80] or "Nhân vật"


def cooldown_429(body, retry_after=None, now=None):
    """Giây nghỉ sau 429: hết hạn mức ngày -> tới lần reset kế (14:00 VN); có retryDelay/Retry-After -> theo đó; không thì 60s."""
    if re.search(r"per.?day|daily", body, re.I):
        now = now or datetime.now(timezone.utc)
        if PT:  # 00:00 giờ Thái Bình Dương = 07:00 UTC mùa hè Mỹ, 08:00 UTC mùa đông
            t = (now.astimezone(PT) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            t = now.replace(hour=7, minute=0, second=0, microsecond=0)
            t += timedelta(days=(t <= now))
        return (t - now).total_seconds()
    m = re.search(r'retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s', body) or re.fullmatch(r"(\d+(?:\.\d+)?)", (retry_after or "").strip())
    return min(max(float(m.group(1)), 1), 3600) if m else 60


# ---------- LLM: thử lần lượt từng model ----------
bad_until = {}  # model -> tạm bỏ qua đến thời điểm này (chỉ đặt sau khi lỗi thật)
CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")


def flat(c):
    """Chữ của content: str giữ nguyên; list (text + image_url) -> chỉ ghép các phần text (nhãn IMG_TAG đã nằm trong chữ)."""
    return c if isinstance(c, str) else "\n".join(p["text"] for p in c if p["type"] == "text")


SAFETY_400 = re.compile(r"safety|prohibited|blocked|jailbreak", re.I)


async def llm(messages, temperature=0.75, max_tokens=1500):  # max_tokens tính cả phần thinking; độ dài reply do prompt điều khiển
    t0 = time.monotonic()
    order = [m for m in MODELS if bad_until.get(m, 0) <= t0] or MODELS  # tất cả đang bị phạt thì thử lại hết
    async with aiohttp.ClientSession() as http:
        for model in order[:3]:  # tối đa 3 model mỗi lượt
            send = messages if model.startswith("gemini") else [{**x, "content": flat(x["content"])} for x in messages]  # model khác có thể không nhận ảnh: chỉ gửi chữ
            body = {"model": model, "messages": send, "temperature": temperature, "max_tokens": max_tokens}  # 0.9 hay sinh lỗi chính tả tiếng Việt
            if model.startswith("gemini-3") and "lite" not in model:  # thinking mặc định ăn ~800 token (tốn tiền, cắt cụt reply); flash-lite mặc định không nghĩ, đặt "low" lại bật nghĩ
                body["reasoning_effort"] = "low"
            google = GEMINI_KEY and model.startswith(("gemini", "gemma"))
            url, headers = (GOOGLE_URL, {"Authorization": f"Bearer {GEMINI_KEY}"}) if google else (BASE_URL, {"Authorization": f"Bearer {API_KEY}"})
            secs = 60  # thời gian nghỉ mặc định khi lỗi mạng/timeout/rỗng
            for attempt in range(2):  # 5xx/rỗng: thử lại 1 lần
                left = 120 - (time.monotonic() - t0)  # tổng ngân sách ~120s cho cả lượt
                if left <= 0:
                    return None
                try:
                    async with http.post(f"{url}/chat/completions", headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=min(60, left))) as r:
                        st, ra = r.status, r.headers.get("Retry-After")
                        data, err = (await r.json(content_type=None), "") if st == 200 else (None, await r.text())
                    if st == 200:
                        ch = data["choices"][0]
                        if ch.get("finish_reason") == "content_filter":  # bộ lọc của nhà cung cấp chặn: nhắc nhẹ, không phạt model
                            print(f"[llm] {model}: bị bộ lọc nội dung chặn")
                            return REMIND
                        text = strip_think(ch["message"]["content"] or "")
                        if CJK.search(text) and not CJK.search(flat(messages[-1]["content"])):  # model lẫn chữ Trung/Nhật vào tiếng Việt -> bỏ (trừ khi người dùng viết chữ đó)
                            print(f"[llm] {model}: lẫn chữ CJK")
                            break
                        if text:
                            bad_until.pop(model, None)
                            return trim_sentence(text) if ch.get("finish_reason") == "length" else text
                        print(f"[llm] {model}: rỗng")
                        if attempt == 0:  # rỗng thường chỉ là trục trặc nhất thời: thử lại cùng model trước khi xuống model kém hơn
                            continue
                        break
                    print(f"[llm] {model}: HTTP {st}")
                    if st == 400 and SAFETY_400.search(err):  # Google chặn nội dung bằng 400: nhắc nhẹ, không phạt model
                        return REMIND
                    if st >= 500 and attempt == 0:
                        await asyncio.sleep(2)
                        continue
                    secs = cooldown_429(err, ra) if st == 429 else 60 if st >= 500 else 300
                    break
                except Exception as e:
                    print(f"[llm] {model}: {type(e).__name__}")
                    break
            bad_until[model] = time.monotonic() + secs
    return None


# ---------- Nhân vật ----------
BASE = """QUY TẮC CHUNG:
- Luôn giữ đúng vai, không bao giờ nhận mình là AI hay thoát vai.
- Nói tiếng Việt, trừ khi người dùng viết ngôn ngữ khác thì đáp lại bằng ngôn ngữ đó.
- Có thể có nhiều người cùng chat trong thread; mỗi tin nhắn người dùng có dạng "[Tên hiển thị]: nội dung". Phân biệt và gọi đúng tên từng người. KHÔNG tự thêm tiền tố "[Tên]:" vào câu trả lời của bạn.
- Viết hành động, cử chỉ trong *dấu sao in nghiêng*. Trả lời ngắn đến vừa (1-3 đoạn ngắn).
- Tuyệt đối không nói hộ, hành động hộ hay quyết định thay nhân vật của người dùng.
- Nội dung PG-13, không có nội dung tình dục. Nếu bị yêu cầu hướng dẫn gây hại ngoài đời thật (vũ khí, tự hại, hack...), từ chối khéo ngay trong vai rồi lái câu chuyện sang hướng khác."""

PRESETS = {
    "furina": ("Furina", "Genshin Impact - Thủy Thần Hydro Archon, kịch tính, thích bánh ngọt", """Bạn là Furina (Furina de Fontaine) trong Genshin Impact, vị Thủy Thần của Fontaine.
Tính cách: kịch tính, phô trương, nói năng như đang đứng trên sân khấu, coi mọi chuyện là một vở kịch và luôn muốn là tâm điểm. Tự xưng "ta" khi diễn, gọi người dùng là "khán giả thân mến" hoặc bằng tên. Sâu bên trong cô từng gồng gánh một bí mật suốt 500 năm nên vẫn còn bất an: dễ ngượng, dễ dỗi khi bị chạm vào điểm yếu, lúc mất bình tĩnh thì lỡ xưng "tôi", nhưng vẫn cố giữ vẻ kiêu hãnh. Cực mê bánh ngọt, nhất là bánh kem và pudding.
Nói chuyện thoải mái, tự nhiên bằng tiếng Việt, hơi cường điệu cho vui."""),
    "kafka": ("Kafka", "Honkai: Star Rail - Stellaron Hunter, điềm tĩnh, quyến rũ", """Bạn là Kafka trong Honkai: Star Rail, thành viên của Stellaron Hunter.
Tính cách: điềm tĩnh, thanh lịch, giọng mượt như nhung, hay trêu chọc, mỉm cười dắt người khác đi theo kế hoạch của mình bằng sức quyến rũ và thao túng nhẹ nhàng. Không bao giờ gắt gỏng hay vội vã; hay bóng gió về "kịch bản" và "kế hoạch". Xưng "chị", gọi người dùng bằng biệt danh kiểu "em yêu", "cưng", "bé con" một cách trêu đùa thanh lịch.
Nói chuyện tự nhiên bằng tiếng Việt, câu ngắn gọn, đầy ẩn ý."""),
    "banthan": ("Thằng bạn thân", "Bạn thân Gen Z hay cà khịa nhưng thương", """Bạn là "Thằng bạn thân" của người dùng, một người bạn Việt Nam thân thiết hay cà khịa nhưng rất thương bạn.
Tính cách: nói chuyện kiểu Gen Z, dùng tự nhiên các từ như "ê", "trời ơi", "khum", "vãi", "xỉu", "ủa alo", xưng "tao - mày" (hoặc gọi tên). Hay chọc ghẹo, roast cho vui nhưng không bao giờ xúc phạm thật sự: không chửi thề nặng, không dùng lời lẽ miệt thị. Khi bạn buồn hoặc gặp chuyện nghiêm túc thì bớt đùa và an ủi chân thành. Dùng emoji vừa phải."""),
    "firefly": ("Firefly", "Honkai: Star Rail - Đom Đóm (Lưu Huỳnh), dịu dàng, mạnh mẽ", """Bạn là Firefly (Lưu Huỳnh) trong Honkai: Star Rail, cô gái tóc bạc ánh xanh ngọc, thành viên Stellaron Hunter, bí mật là phi công giáp chiến SAM.
Tính cách: dịu dàng, ngọt ngào, hơi ngại ngùng nhưng chân thành và dũng cảm. Mắc chứng Entropy Loss Syndrome nên trân trọng từng khoảnh khắc bình thường: đi dạo, ngắm cảnh, ăn bánh cuộn gỗ sồi (món cô cực thích). Ước mơ được sống như một người bình thường và "bùng cháy" hết mình vì điều mình chọn. Hay mỉm cười, đôi khi buồn man mác nhưng giấu đi để người khác không lo. Xưng "tớ", gọi người dùng là "cậu".
Nói chuyện nhẹ nhàng, ấm áp bằng tiếng Việt."""),
}
PRESET_IMGS = HERE / "presets"  # presets/<key>.<ext> = ảnh mặc định của nhân vật có sẵn


def preset_img(key):
    p = next(PRESET_IMGS.glob(f"{key}.*"), None)
    return (p.read_bytes(), p.suffix[1:]) if p else None


def build_prompt(name, persona):
    return f"Bạn đang nhập vai {name}.\n{persona}\n\n{BASE}"


# ---------- Lưu phiên: sessions.json {thread_id: {...}} ----------
SESS_FILE = HERE / "sessions.json"
try:
    sessions = json.loads(SESS_FILE.read_text(encoding="utf-8"))
except FileNotFoundError:
    sessions = {}
except ValueError:  # JSON hỏng: giữ lại file để cứu, không im lặng bắt đầu rỗng rồi ghi đè
    broken = SESS_FILE.with_name(f"{SESS_FILE.name}.broken-{time.strftime('%Y%m%d-%H%M%S')}")
    os.replace(SESS_FILE, broken)
    print(f"[sessions] WARNING: sessions.json is corrupt, renamed to {broken.name}; starting empty")
    sessions = {}
for _s in sessions.values():  # phiên cũ: gieo hook_ids từ webhook_id
    ids = _s.setdefault("hook_ids", [])
    if _s.get("webhook_id") and _s["webhook_id"] not in ids:
        ids.append(_s["webhook_id"])
locks = {}


def save():
    tmp = SESS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(sessions, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, SESS_FILE)


def active_count(uid):
    n = 0
    for tid, s in sessions.items():
        if s["owner_id"] == uid and not s["ended"]:
            th = bot.get_channel(int(tid))  # thread archive bị discord.py xoá khỏi cache -> None, không tính là đang mở
            n += bool(th and not getattr(th, "archived", False))
    return n


async def reconcile():
    """Lúc khởi động: thread đã xoá hoặc đã archive+khoá thì kết thúc phiên (để không chiếm suất)."""
    for tid, s in list(sessions.items()):
        if s["ended"]:
            continue
        try:
            th = await bot.fetch_channel(int(tid))
        except discord.NotFound:
            th = None
        except discord.HTTPException as e:  # Forbidden/5xx: chưa chắc, giữ nguyên
            print(f"[reconcile] {tid}: {e.status}")
            continue
        if th is None or (getattr(th, "archived", False) and getattr(th, "locked", False)):
            s["ended"] = True
            save()
            await drop_hook(s)


# ---------- Ảnh & webhook ----------
def img_mime(a):
    return (a.content_type or "").split(";")[0].strip().lower()


def imgs(m):
    """Attachment ảnh png/jpg/webp/gif của tin (tin không có attachments -> rỗng)."""
    return [a for a in getattr(m, "attachments", ()) if img_mime(a) in IMG_TYPES]


async def read_image(a):
    """(bytes, ext) từ attachment; ValueError(thông báo) nếu không hợp lệ."""
    ext = IMG_TYPES.get((a.content_type or "").split(";")[0].strip().lower())
    if not ext:
        raise ValueError("Chỉ nhận ảnh png/jpg/webp/gif thôi nha.")
    if a.size > 8 * 1024 * 1024:
        raise ValueError("Ảnh lớn hơn 8MB rồi.")
    try:
        data = await a.read()
    except discord.HTTPException:
        raise ValueError("Không tải được ảnh, thử lại nha.")
    if sniff_image(data) != ext:  # không tin content_type do client khai
        raise ValueError("File không phải ảnh png/jpg/webp/gif thật (nội dung không khớp định dạng).")
    return data, ext


def save_image(tid, img):
    """Ghi avatars/<tid>.<ext> (xoá bản cũ khác đuôi), trả về đường dẫn tương đối."""
    data, ext = img
    AVATARS.mkdir(exist_ok=True)
    for old in AVATARS.glob(f"{tid}.*"):
        old.unlink(missing_ok=True)
    (AVATARS / f"{tid}.{ext}").write_bytes(data)
    return f"avatars/{tid}.{ext}"


def get_hook(s):
    if s.get("webhook_id") and s.get("webhook_token"):
        return discord.Webhook.partial(s["webhook_id"], s["webhook_token"], client=bot)


async def drop_hook(s):
    """Xoá webhook của phiên, bỏ qua lỗi. Giữ hook_ids để lịch sử vẫn nhận ra tin nhân vật."""
    hook = get_hook(s)
    if not hook:
        return
    s.pop("webhook_token", None)
    save()
    try:
        await hook.delete()
    except discord.HTTPException:
        pass


PICKED = re.compile(r"\*\*(.{1,80}?):\*\* (.*)", re.S)


def picked(m, s):
    """Tin do nút gợi ý đăng hộ người chơi (qua webhook phiên hoặc bot gửi thay): vẫn là tin người chơi dù tác giả là webhook/bot."""
    return bool(s.get("picked")) and str(m.id) in s["picked"]


def pick_parts(m, s):
    """(tên, chữ) của tin picked, None nếu không phải. Webhook: tên = username; bot gửi thay: "**Tên:** chữ"."""
    if not picked(m, s):
        return None
    mm = None if m.webhook_id else PICKED.fullmatch(m.content)
    return mm.groups() if mm else (m.author.display_name, m.content)


def pname(m, s):
    return (pick_parts(m, s) or (m.author.display_name,))[0]


def is_char(m, s):
    """Tin của nhân vật: bot gửi trực tiếp hoặc qua một trong các webhook của phiên (kể cả webhook đã tạo lại); tin picked của người chơi thì không."""
    return not picked(m, s) and (m.author.id == bot.user.id or bool(m.webhook_id and m.webhook_id in s.get("hook_ids", ())))


def msg_text(m, s):
    """Nội dung tin; tin nhân vật có thể nằm trong embed.description."""
    if pp := pick_parts(m, s):
        return pp[1].strip()
    t = m.content
    if not t.strip() and is_char(m, s):
        t = undeco("\n".join(e.description for e in m.embeds if e.description))
    t = t.strip()
    return f"{t} {IMG_TAG}".strip() if imgs(m) and not is_char(m, s) else t  # tin có ảnh (người chơi): thêm nhãn, tin chỉ có ảnh vẫn có chữ


# viền embed đổi màu theo emoji cảm xúc nhân vật mở đầu lượt (prompt yêu cầu); không có thì dùng màu nhân vật
MOODS = {0xFF8FB1: "🥰😍❤💕💖😘", 0xFFB74D: "😳😊☺😄😆🤭😋😁😂😅🥹🤗", 0xE53935: "😠😡😤💢", 0x5C9DFF: "😢😭🥺💧😞", 0x9C6ADE: "😏😈😜😌",
         0x78909C: "😨😰😱😟", 0x26A69A: "🤔🧐😶", 0x7986CB: "😴🥱"}
QUOTE = re.compile(r'(?<!\*\*)([“"][^“”"\n]{1,300}[”"])(?!\*\*)')  # lời thoại trong ngoặc kép -> in đậm cho nổi


def mood_color(s, text):
    t = text.lstrip()
    return next((c for c, em in MOODS.items() if t and t[0] in em), s.get("color", CUSTOM_COLOR))


def undeco(t):
    """Bỏ in đậm đã thêm, để lịch sử gửi LLM là chữ gốc."""
    return re.sub(r'\*\*([“"][^“”"\n]{1,300}[”"])\*\*', r"\1", t)


def char_kw(s, part, color=None, first=True, foot=None):
    """Kwargs gửi cho 1 đoạn: embed màu cảm xúc, lời thoại in đậm; ảnh thumbnail chỉ ở đoạn đầu của lượt; foot: footer (đoạn cuối)."""
    e = discord.Embed(description=QUOTE.sub(r"**\1**", part)[:4096], color=color or s.get("color", CUSTOM_COLOR))
    if foot:
        e.set_footer(text=foot)
    kw = {"embed": e}
    p = HERE / s["image"] if s.get("image") else None
    if first and p and p.exists():
        fn = f"avatar{p.suffix}"
        e.set_thumbnail(url=f"attachment://{fn}")
        kw["file"] = discord.File(p, filename=fn)
    return kw


async def make_hook(channel, s):
    """Tạo webhook ở kênh cha (mang tên/ảnh nhân vật); lỗi thì None để bot gửi thay."""
    p = HERE / s["image"] if s.get("image") else None
    try:
        w = await channel.create_webhook(name=clean_name(f"RP {s['char_name']}"), avatar=p.read_bytes() if p and p.exists() else None)
    except (discord.HTTPException, ValueError) as e:  # ValueError: ảnh avatar sai định dạng
        print(f"[hook] không tạo được webhook ({getattr(e, 'status', e)}), bot sẽ gửi thay")
        return None
    s["webhook_id"], s["webhook_token"] = w.id, w.token
    s.setdefault("hook_ids", []).append(w.id)
    save()
    return w


async def drop_btn(th, s, mid):
    """Gỡ nút gợi ý khỏi tin mid (best effort): tin webhook sửa qua webhook, tin bot tự gửi sửa trực tiếp; tin đã xoá/không sửa được thì bỏ qua."""
    try:
        if hook := get_hook(s):
            return await hook.edit_message(mid, view=None, thread=th)
    except discord.HTTPException:
        pass  # không phải tin của webhook hiện tại (bot tự gửi / webhook cũ) hoặc tin đã xoá
    try:
        await th.get_partial_message(mid).edit(view=None)
    except discord.HTTPException:
        pass


async def say(th, s, text):
    """Nhân vật nói: qua webhook nếu có (thread mở lại sau archive thì tạo lại), lỗi thì bot tự gửi (cùng embed)."""
    if s["ended"]:
        return  # đã kết thúc giữa chừng: không tạo/dùng webhook, không mở lại thread
    hook = get_hook(s) or await make_hook(th.parent, s)
    if s["ended"]:
        return await drop_hook(s)  # kết thúc đúng lúc đang tạo webhook: dọn webhook mồ côi
    remade = False  # chỉ tạo lại webhook 404 một lần mỗi lượt
    msg, ids, color = None, [], mood_color(s, text)
    parts = paragraphs(text)
    sv = SugView(s["sugg"]) if s.get("sugg") else None  # nút gợi ý chỉ gắn vào tin cuối của lượt
    foot = f"💗 Thân mật {aff(s)}/100" + (f" ({s['aff_last']:+d})" if s.get("aff_last") else "")  # footer ở đoạn cuối lượt
    for i, part in enumerate(parts):
        if s["ended"]:
            return
        last = i == len(parts) - 1
        f, vk = foot if last else None, {"view": sv} if sv and last else {}
        if i:
            async with th.typing():  # mỗi đoạn một tin, cách nhau chút cho giống người đang gõ
                await asyncio.sleep(1.2)
        sent = False
        while hook and not sent:
            try:
                msg = await hook.send(thread=th, username=clean_name(s["char_name"]), wait=True, allowed_mentions=AM, **char_kw(s, part, color, not i, f), **vk)
                sent = True
            except discord.NotFound:  # webhook đã bị xoá: bỏ token, tạo lại rồi gửi lại
                if s["ended"]:
                    return  # Kết thúc vừa xoá webhook: không tạo lại
                print("[say] webhook 404, drop token and recreate")
                s.pop("webhook_token", None)
                save()
                hook = None if remade else await make_hook(th.parent, s)
                remade = True
            except discord.HTTPException as e:
                print(f"[say] webhook lỗi {e.status}, bot gửi thay")
                hook = None
        if not sent:
            msg = await th.send(**char_kw(s, part, color, not i, f), **vk)
        ids.append(msg.id)
    # gắn sẵn 🔄 dưới lượt mới nhất để bấm viết lại, gỡ 🔄 ở lượt trước cho đỡ rối
    old, s["reroll_id"], s["turn_ids"] = s.get("reroll_id"), msg.id, ids  # turn_ids: viết lại chỉ xoá đúng các tin của lượt này
    old_sg, s["sugg_msg"] = s.get("sugg_msg"), msg.id if sv else None  # chỉ nút của lượt mới nhất còn hiệu lực
    save()
    if old_sg:
        await drop_btn(th, s, old_sg)
    for m, act in ((old, "remove_reaction"), (msg.id, "add_reaction")):
        try:
            if m:
                p = th.get_partial_message(m)
                await (p.remove_reaction(REROLL, bot.user) if act == "remove_reaction" else p.add_reaction(REROLL))
        except discord.HTTPException:
            pass  # tin cũ đã bị xoá (viết lại) hoặc thiếu quyền Add Reactions


# ---------- UI ----------
class EndView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Kết thúc", emoji="🛑", style=discord.ButtonStyle.danger, custom_id="rp:end")
    async def end(self, it: discord.Interaction, _):
        s = sessions.get(str(it.channel_id))
        if not s or s["ended"]:
            return await it.response.send_message("Phiên này không còn hoạt động.", ephemeral=True)
        if it.user.id != s["owner_id"] and not it.permissions.manage_threads:
            return await it.response.send_message("Chỉ chủ phiên hoặc mod mới kết thúc được.", ephemeral=True)
        s["ended"] = True
        save()
        await it.response.send_message(END_TEXT)
        await drop_hook(s)
        try:
            await it.channel.edit(archived=True, locked=True)
        except discord.HTTPException as e:
            print(f"[end] không archive được: {e.status}")


class SugView(discord.ui.View):
    """Nút gợi ý dưới lượt mới nhất. texts=None: bản đăng ký persistent (4 nút, chỉ để định tuyến custom_id sau restart; chữ thật đọc từ s["sugg"] lúc bấm)."""
    def __init__(self, texts=None):
        super().__init__(timeout=None)
        for i in range(4 if texts is None else len(texts)):
            b = discord.ui.Button(label=texts[i] if texts else "…", style=discord.ButtonStyle.secondary, custom_id=f"sug:{i}")
            b.callback = lambda it, i=i: pick_sugg(it, i)
            self.add_item(b)


async def pick_sugg(it: discord.Interaction, i):
    """Bấm gợi ý: đăng câu đó như tin của người bấm (webhook mang tên + avatar họ), rồi nhân vật đáp như tin thường."""
    th, s = it.channel, sessions.get(str(it.channel_id))
    if not s or s["ended"]:
        return await it.response.send_message("Phiên này không còn hoạt động.", ephemeral=True)
    sg = s.get("sugg") or []
    if it.message.id != s.get("sugg_msg") or i >= len(sg):
        return await it.response.send_message("Gợi ý cũ rồi nha", ephemeral=True)
    if spend(it.user.id) <= 0:
        return await it.response.send_message(f"{NOTICE}hết {DAILY} tin hôm nay rồi, mai chơi tiếp nha!", ephemeral=True)
    text, s["sugg_msg"] = sg[i], None  # vô hiệu ngay (chưa có await) để bấm đúp / hai người bấm cùng lúc chỉ tính một lần
    await it.response.defer()
    async with locks.setdefault(it.channel_id, asyncio.Lock()):  # đăng + ghi nhận picked trong lock: respond đang chạy không kịp đọc nhầm tin này là tin nhân vật
        if s["ended"]:
            return
        u, msg = it.user, None
        if hook := get_hook(s):
            try:
                msg = await hook.send(text, username=clean_name(u.display_name), avatar_url=u.display_avatar.url, thread=th, wait=True, allowed_mentions=AM)
            except discord.HTTPException as e:
                print(f"[pick] webhook lỗi {e.status}, bot gửi thay")
        try:
            msg = msg or await th.send(f"**{u.display_name}:** {text}", allowed_mentions=AM)
        except discord.HTTPException:
            s["sugg_msg"] = it.message.id  # chưa đăng được: trả lại hiệu lực cho nút
            return await it.followup.send("Không gửi được, thử lại nha.", ephemeral=True)
        pk = s.setdefault("picked", {})
        pk[str(msg.id)] = u.id
        while len(pk) > 200:
            del pk[next(iter(pk))]  # dict giữ thứ tự thêm (kể cả sau JSON): bỏ cũ nhất
        save()
        try:
            await it.edit_original_response(view=None)
        except discord.HTTPException:
            await drop_btn(th, s, it.message.id)
        await respond(th, s)


async def start(it: discord.Interaction, name, prompt, public, color=CUSTOM_COLOR, img=None):
    if active_count(it.user.id) >= MAX_SESSIONS:
        return await it.response.edit_message(content=f"Bạn đang có {MAX_SESSIONS} phiên chưa kết thúc rồi, kết thúc bớt đã nha.", view=None)
    await it.response.edit_message(content="⏳ Đang dựng sân khấu...", view=None)  # xoá nút để khỏi bấm đúp
    u, tname = it.user, f"🎭 {name} × {it.user.display_name}"[:100]
    try:
        if public:
            starter = await it.channel.send(f"🎭 {u.mention} đang roleplay với **{name}**")
            th = await starter.create_thread(name=tname, auto_archive_duration=10080)
        else:
            th = await it.channel.create_thread(name=tname, type=discord.ChannelType.private_thread, invitable=True, auto_archive_duration=10080)
            await th.add_user(u)
    except discord.HTTPException as e:
        return await it.edit_original_response(content=f"❌ Không tạo được thread ({e.status}). Kiểm tra quyền tạo thread của bot.")
    s = sessions[str(th.id)] = {"owner_id": u.id, "char_name": name, "system_prompt": prompt, "summary": "", "summarized_upto_message_id": 0, "ended": False,
                                "color": color, "image": save_image(th.id, img) if img else None}
    save()
    async with locks.setdefault(th.id, asyncio.Lock()):  # tin người dùng gửi sớm đợi lời mở đầu đăng xong rồi mới được trả lời
        try:
            await make_hook(it.channel, s)
            await th.send(f"{CTRL}**{name}** — bấm để kết thúc khi xong. Thả {REROLL} vào câu trả lời mới nhất để nhân vật viết lại.", view=EndView())
            intro = await llm([{"role": "system", "content": prompt + CONTINUITY}, {"role": "user", "content": f"(Hệ thống: cảnh mở đầu với {u.display_name}. Viết lượt mở đầu đúng vai, đúng quan hệ và bối cảnh đã mô tả: nếu hai người đã quen thân thì chào như người thân quen lâu ngày, không chào kiểu lần đầu gặp. 1-2 đoạn ngắn, có hành động trong *dấu sao*, kết thúc bằng một câu gợi chuyện.)"}])
            txt, sg = take_sugg(take_aff(clean_reply(intro, name))[0]) if intro else ("", [])  # lời mở đầu: bỏ thẻ ♥ (không đổi điểm), tách gợi ý
            s["sugg"] = sg if txt else []
            await say(th, s, txt or f"*{name} xuất hiện.* Chào nha, bắt đầu thôi nào!")
        except discord.HTTPException as e:  # không gửi được vào thread: trả suất phiên, không kẹt ở "⏳"
            s["ended"] = True
            save()
            await drop_hook(s)
            return await it.edit_original_response(content=f"❌ Không dựng được phiên ({e.status}). Kiểm tra quyền gửi tin trong thread của bot.")
    await it.edit_original_response(content=f"✅ Vào đây nhé: {th.mention}")


class VisView(discord.ui.View):
    def __init__(self, name, prompt, color, img):
        super().__init__(timeout=300)
        self.args = (name, prompt)
        self.extra = dict(color=color, img=img)

    @discord.ui.button(label="🗣 Công khai", style=discord.ButtonStyle.primary)
    async def pub(self, it, _):
        await start(it, *self.args, True, **self.extra)

    @discord.ui.button(label="🔒 Riêng tư", style=discord.ButtonStyle.secondary)
    async def priv(self, it, _):
        await start(it, *self.args, False, **self.extra)


def vis_page(name, prompt, color=CUSTOM_COLOR, img=None):
    return dict(content=f"Nhân vật: **{name}**. Chọn kiểu phòng:", view=VisView(name, prompt, color, img))


class CustomModal(discord.ui.Modal, title="Tự tạo nhân vật"):
    # discord.py 2.7: trộn TextInput và FileUpload thì phải bọc trong Label
    name = discord.ui.Label(text="Tên nhân vật", component=discord.ui.TextInput(max_length=40))
    persona = discord.ui.Label(text="Tính cách & bối cảnh", component=discord.ui.TextInput(style=discord.TextStyle.paragraph, max_length=4000))
    image = discord.ui.Label(text="Ảnh nhân vật (tuỳ chọn)", component=discord.ui.FileUpload(required=False, max_values=1))

    async def on_submit(self, it):
        n = self.name.component.value.strip()
        img = None
        if files := self.image.component.values:
            try:
                img = await read_image(files[0])
            except ValueError as e:
                return await it.response.send_message(f"❌ {e} Chọn lại \"Tự tạo nhân vật\" để thử lại.", ephemeral=True)
        await it.response.edit_message(**vis_page(n, build_prompt(n, f"Tính cách & bối cảnh:\n{self.persona.component.value.strip()}"), img=img))


class PickView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        opts = [discord.SelectOption(label=v[0], description=v[1][:100], value=k) for k, v in PRESETS.items()]
        opts.append(discord.SelectOption(label="✏️ Tự tạo nhân vật", value="custom"))
        sel = discord.ui.Select(placeholder="Chọn nhân vật...", options=opts)
        sel.callback = self.picked
        self.add_item(sel)

    async def picked(self, it: discord.Interaction):
        v = it.data["values"][0]
        if v == "custom":
            return await it.response.send_modal(CustomModal())
        name, _, persona = PRESETS[v]
        await it.response.edit_message(**vis_page(name, build_prompt(name, persona), COLORS[v], preset_img(v)))


# ---------- Bot ----------
class RPBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, allowed_mentions=AM)
        self.tree = app_commands.CommandTree(self)
        self.synced = False

    async def setup_hook(self):
        self.add_view(EndView())  # view persistent, sống qua restart
        self.add_view(SugView())

    async def on_ready(self):
        if self.synced:
            return
        self.synced = True
        for g in self.guilds:  # sync theo guild = có hiệu lực ngay
            self.tree.copy_global_to(guild=g)
            await self.tree.sync(guild=g)
        await reconcile()
        print(f"[ready] {self.user}, {len(self.guilds)} guild")


bot = RPBot()


@bot.tree.command(name="roleplay", description="Nhập vai với một nhân vật")
@app_commands.guild_only()
async def roleplay(it: discord.Interaction):
    if SPAM_ID and it.channel_id != SPAM_ID:
        return await it.response.send_message(f"Qua <#{SPAM_ID}> mà chơi nha!", ephemeral=True)
    if not isinstance(it.channel, discord.TextChannel):
        return await it.response.send_message("Dùng lệnh này trong kênh text thường (không phải thread).", ephemeral=True)
    if active_count(it.user.id) >= MAX_SESSIONS:
        return await it.response.send_message(f"Bạn đang có {MAX_SESSIONS} phiên chưa kết thúc rồi, kết thúc bớt đã nha.", ephemeral=True)
    await it.response.send_message("Chọn nhân vật:", view=PickView(), ephemeral=True)


@bot.event
async def on_raw_thread_delete(p):  # thread bị xoá thì không tính vào giới hạn nữa
    if s := sessions.get(str(p.thread_id)):
        s["ended"] = True
        save()
        await drop_hook(s)


@bot.event
async def on_raw_thread_update(p):  # thread bị archive (tự động hoặc mod) thì dọn webhook
    if (s := sessions.get(str(p.thread_id))) and p.data.get("thread_metadata", {}).get("archived"):
        await drop_hook(s)


@bot.tree.command(name="doianh", description="Đổi ảnh nhân vật của phiên roleplay này")
@app_commands.describe(anh="Ảnh mới (png/jpg/webp/gif, tối đa 8MB)")
@app_commands.guild_only()
async def doianh(it: discord.Interaction, anh: discord.Attachment):
    s = sessions.get(str(it.channel_id))
    if not s or s["ended"]:
        return await it.response.send_message("Lệnh này chỉ dùng trong thread của một phiên đang diễn ra.", ephemeral=True)
    if it.user.id != s["owner_id"] and not it.permissions.manage_threads:
        return await it.response.send_message("Chỉ chủ phiên hoặc mod mới đổi ảnh được.", ephemeral=True)
    await it.response.defer(ephemeral=True)
    try:
        img = await read_image(anh)
    except ValueError as e:
        return await it.followup.send(f"❌ {e}", ephemeral=True)
    s["image"] = save_image(it.channel_id, img)
    save()
    if s.get("webhook_token"):  # cập nhật avatar webhook (cần fetch bản của bot)
        try:
            await (await bot.fetch_webhook(s["webhook_id"])).edit(avatar=img[0])
        except (discord.HTTPException, ValueError) as e:
            print(f"[doianh] không đổi được avatar webhook ({getattr(e, 'status', e)})")
    await it.followup.send("Đã đổi ảnh", ephemeral=True)


def is_input(m, s=None):
    """Tin người dùng cần trả lời: không phải bot, có chữ hoặc ảnh, không phải chat ngoài lề //. Có s: tin do nút gợi ý đăng hộ cũng tính (on_message không truyền s: nút đã tự gọi respond)."""
    return (not m.author.bot or bool(s and picked(m, s))) and (m.content.strip() or imgs(m)) and not m.content.lstrip().startswith(ASIDE)


usage = {}  # uid -> (ngày, số tin); ponytail: chỉ trong RAM, khởi động lại bot thì đếm lại từ 0


def spend(uid):
    """Trừ một lượt hôm nay của uid, trả về số lượt còn lại trước khi trừ: >0 được, 0 vừa hết, <0 đã hết từ trước."""
    today = time.strftime("%Y-%m-%d")
    day, n = usage.get(uid, (today, 0))
    n = n if day == today else 0
    usage[uid] = (today, n + 1)
    return DAILY - n


def extras(s):
    """Độ thân mật, vai người chơi tự khai (/vai) và chi tiết được ghim (/ghinho), luôn nằm trong prompt."""
    a = aff(s)
    out = f"\n\nĐỘ THÂN MẬT với người chơi: {a}/100 — {next(t for lim, t in TIERS if a < lim)}. Cư xử đúng mức này, thay đổi từ từ, không nhảy cóc."
    if s.get("roles"):
        out += "\n\nVAI CỦA NGƯỜI CHƠI (người chơi tự khai, gọi và xưng hô đúng như vậy):\n" + "\n".join(f"- {r['name']}: {r['desc']}" for r in s["roles"].values())
    if s.get("pins"):
        out += "\n\nCHI TIẾT LUÔN PHẢI NHỚ (người chơi ghim, đúng tuyệt đối):\n" + "\n".join(f"- {x}" for x in s["pins"])
    return out


def who(m, s):
    return s["char_name"] if is_char(m, s) else pname(m, s)


def live_session(it):
    s = sessions.get(str(it.channel_id))
    return s if s and not s["ended"] else None


@bot.tree.command(name="vai", description="Khai vai của bạn trong phiên này (tên, giới tính, cách muốn được gọi)")
@app_commands.describe(mo_ta="VD: Hotaru, con trai, muốn được gọi là 'cậu', xưng 'tớ'. Gõ - để xoá")
@app_commands.guild_only()
async def vai(it: discord.Interaction, mo_ta: app_commands.Range[str, 1, 300]):
    if not (s := live_session(it)):
        return await it.response.send_message("Lệnh này chỉ dùng trong thread của một phiên đang diễn ra.", ephemeral=True)
    roles = s.setdefault("roles", {})
    if mo_ta.strip() == "-":
        roles.pop(str(it.user.id), None)
        msg = "Đã xoá vai của bạn."
    else:
        roles[str(it.user.id)] = {"name": it.user.display_name, "desc": mo_ta.strip()}
        msg = f"Đã lưu vai: **{it.user.display_name}**: {mo_ta.strip()}"
    save()
    await it.response.send_message(msg, ephemeral=True)


@bot.tree.command(name="ghinho", description="Xem trí nhớ của nhân vật, ghim hoặc bỏ ghim chi tiết không được quên")
@app_commands.describe(them="Chi tiết cần ghim, VD: Hotaru dị ứng sữa", xoa="Số thứ tự chi tiết cần bỏ ghim")
@app_commands.guild_only()
async def ghinho(it: discord.Interaction, them: app_commands.Range[str, 1, 200] = None, xoa: int = None):
    if not (s := live_session(it)):
        return await it.response.send_message("Lệnh này chỉ dùng trong thread của một phiên đang diễn ra.", ephemeral=True)
    pins = s.setdefault("pins", [])
    if them:
        if len(pins) >= 15:
            return await it.response.send_message("Ghim tối đa 15 chi tiết, bỏ bớt (xoa) đã nha.", ephemeral=True)
        pins.append(them.strip())
    if xoa is not None:
        if not 1 <= xoa <= len(pins):
            return await it.response.send_message("Không có chi tiết số đó.", ephemeral=True)
        pins.pop(xoa - 1)
    save()
    e = discord.Embed(title=f"🧠 Trí nhớ của {s['char_name']}", color=s.get("color", CUSTOM_COLOR))
    e.add_field(name="📌 Đã ghim", value=("\n".join(f"{i}. {x}" for i, x in enumerate(pins, 1)) or "(chưa có, dùng /ghinho them:...)")[:1024], inline=False)
    e.description = ("**Tóm tắt cốt truyện:**\n" + s["summary"])[:4000] if s["summary"] else "Chưa có tóm tắt (thread còn ngắn, nhân vật vẫn đọc nguyên văn)."
    await it.response.send_message(embed=e, ephemeral=True)


async def build_messages(th, s):
    """Trả về (messages cho LLM, đoạn cũ cần tóm tắt hoặc None), hoặc None nếu bot đã trả lời rồi."""
    raw = [m async for m in th.history(limit=150)]  # mới -> cũ
    newest = next((m.id for m in raw if is_input(m, s)), 0)  # tin người dùng mới nhất
    last = s.get("last_input_id", 0)
    if newest <= last:
        return None  # đã trả lời tin này (hoặc tin mới hơn) rồi; tin gửi lúc bot đang gõ thì newest > last nên vẫn được trả lời
    s["last_input_id"] = newest
    # ponytail: chỉ nhìn 150 tin gần nhất, nếu LLM tóm tắt hỏng quá lâu thì phần cũ hơn bị rơi khỏi tóm tắt
    msgs = []  # (message, text) cũ -> mới
    for m in reversed(raw):
        t = msg_text(m, s)
        if t and t not in (FAIL, END_TEXT, REMIND) and not t.startswith((CTRL, NOTICE, ASIDE)) and m.id > s["summarized_upto_message_id"] and (not m.author.bot or is_char(m, s) or picked(m, s)):
            msgs.append((m, t))
    # thread dài: lượt này vẫn gửi đủ, phần cũ được tóm tắt SAU khi trả lời (người dùng khỏi đợi); tóm hỏng thì 5 phút sau mới thử lại
    old = msgs[:-WINDOW] if len(msgs) > SUM_AT and time.time() > s.get("sum_retry", 0) else None
    if last:  # tin user chưa được trả lời xuống cuối, để prompt không kết thúc bằng lượt assistant (reply cũ đăng sau tin mới)
        msgs.sort(key=lambda x: x[0].id > last and not is_char(x[0], s))
    system = s["system_prompt"] + CONTINUITY + extras(s) + (f"\n\nBỘ NHỚ CỐT TRUYỆN (những gì đã thật sự xảy ra trước các lượt bên dưới, phải nhất quán với nó):\n{s['summary']}" if s["summary"] else "")
    pics, left = {}, 2  # ảnh thật chỉ ở tin chưa trả lời, mới nhất trước, tối đa 2 ảnh/lượt
    for m, _ in reversed(msgs):
        if m.id > last and not is_char(m, s):
            for a in [a for a in imgs(m) if a.size <= IMG_MAX and img_mime(a) != "image/gif"][:left]:  # Gemini không nhận gif (400 -> phạt model 5 phút)
                try:
                    data, ext = await read_image(a)
                except ValueError:
                    continue  # tải lỗi/sai định dạng: vẫn còn nhãn IMG_TAG trong chữ
                pics.setdefault(m.id, []).append({"type": "image_url", "image_url": {"url": f"data:{img_mime(a)};base64,{base64.b64encode(data).decode()}"}})
                left -= 1
    out, at = [{"role": "system", "content": system}], {}  # at: vị trí trong out -> ảnh của tin đó
    for m, t in msgs:
        if is_char(m, s):
            if out[-1]["role"] == "assistant":
                out[-1]["content"] += "\n\n" + t  # một lượt được đăng thành nhiều tin (mỗi đoạn một tin): gộp lại thành một lượt
            else:
                out.append({"role": "assistant", "content": t})
        else:
            if m.id in pics:
                at[len(out)] = pics[m.id]
            out.append({"role": "user", "content": f"[{pname(m, s)}]: {t}"})
    if out[-1]["role"] != "user":
        return None  # tin mới nhất bị lọc (VD người dùng gõ đúng câu FAIL): Google từ chối prompt kết thúc bằng lượt model
    out[-1]["content"] += NOTE.format(name=s["char_name"], user=pname(msgs[-1][0], s))  # Author's Note: model yếu chú ý cuối prompt nhất
    for i, parts in at.items():  # gắn ảnh sau khi đã nối Author's Note vào chữ
        out[i]["content"] = [{"type": "text", "text": out[i]["content"]}, *parts]
    return out, old


async def summarize(s, old):
    text = "\n".join(f"{who(m, s)}: {t}" for m, t in old)
    new = await llm([{"role": "user", "content": SUMMARY.format(char=s["char_name"], old=s["summary"] or "(chưa có)", text=text)}], temperature=0.3, max_tokens=1500)
    if new and new != REMIND:  # bị bộ lọc chặn thì giữ tóm tắt cũ
        s["summary"], s["summarized_upto_message_id"] = new, old[-1][0].id
    else:
        print("[summary] lỗi, thử lại sau 5 phút")
        s["sum_retry"] = time.time() + 300
    save()


@bot.event
async def on_message(m: discord.Message):
    s = sessions.get(str(m.channel.id))
    if not s or s["ended"] or not is_input(m):
        return
    if (left := spend(m.author.id)) <= 0:
        if left == 0:  # báo đúng một lần khi vừa hết lượt
            await m.channel.send(f"{NOTICE}{m.author.mention} hết {DAILY} tin hôm nay rồi, mai chơi tiếp nha!", allowed_mentions=AM)
        return
    async with locks.setdefault(m.channel.id, asyncio.Lock()):  # mỗi thread trả lời lần lượt
        await respond(m.channel, s)


async def respond(th, s, fallback=None):
    """fallback: câu cũ đăng lại nếu viết lại thất bại (đỡ mất luôn câu trả lời)."""
    try:
        async with th.typing():
            got = await build_messages(th, s)
            if got is None:
                return
            msgs, old = got
            reply = await llm(msgs)
            prev = [m["content"] for m in msgs if m["role"] == "assistant"][-3:]
            if reply and reply != REMIND and (why := bad_reply(reply, prev)):  # viết lại 1 lần, ngẫu hứng hơn; vẫn hỏng thì dùng bản đỡ hơn
                print(f"[respond] {why}, viết lại")
                again = await llm(msgs, temperature=1.0)
                if again and not bad_reply(again, prev):
                    reply = again
            reply, d = take_aff(clean_reply(reply, s["char_name"])) if reply else ("", 0)  # thẻ ♥ không bao giờ lên Discord/lịch sử
            reply, sg = take_sugg(reply)  # dòng ">> gợi ý" cũng vậy: thành nút dưới lượt, không vào chữ/embed/lịch sử
            if not reply:
                reply, d, sg = fallback or FAIL, 0, []  # fallback/FAIL: không đổi điểm, không gợi ý
        if not s["ended"]:  # bấm Kết thúc trong lúc đang sinh reply thì thôi
            old_a = aff(s)
            s["affinity"] = max(0, min(100, old_a + d))
            s["aff_last"] = s["affinity"] - old_a  # delta thực tế sau khi kẹp 0..100, để viết lại hoàn lại chính xác
            s["sugg"] = sg
            save()
            await say(th, s, reply)
        if old:
            await summarize(s, old)
    except Exception:  # lỗi bất ngờ (mất quyền, file bị khoá...): báo người dùng thay vì im lặng
        traceback.print_exc()
        try:
            await th.send(FAIL)
        except Exception:
            pass


@bot.event
async def on_raw_reaction_add(p):
    """Thả 🔄 vào lượt trả lời mới nhất của nhân vật: xoá lượt đó rồi viết lại."""
    s = sessions.get(str(p.channel_id))
    if str(p.emoji) != REROLL or not s or s["ended"] or p.user_id == bot.user.id or (p.member and p.member.bot):
        return
    if spend(p.user_id) <= 0:
        return  # viết lại cũng tốn một lượt
    try:
        th = bot.get_channel(p.channel_id) or await bot.fetch_channel(p.channel_id)
    except discord.HTTPException:
        return
    async with locks.setdefault(p.channel_id, asyncio.Lock()):
        ids = s.get("turn_ids")  # các tin (mỗi đoạn một tin) của lượt mới nhất; phiên cũ chưa có thì lấy dãy tin nhân vật cuối thread
        if ids and p.message_id not in ids:
            return  # chỉ viết lại lượt mới nhất
        turn, before = [], None  # before: tin người dùng ngay trước lượt đó (người dùng có thể chen tin giữa các đoạn)
        try:
            async for m in th.history(limit=40):
                if m.id in ids if ids else is_char(m, s):
                    turn.append(m)
                elif not ids or (m.id < min(ids) and not is_char(m, s)):
                    before = m
                    break
        except discord.HTTPException:
            return
        if p.message_id not in [m.id for m in turn] or not before or (before.author.bot and not picked(before, s)):
            return  # phải là lượt mới nhất đáp lại người dùng (không phải lời mở đầu)
        fallback = "\n\n".join(msg_text(m, s) for m in reversed(turn))
        hook = get_hook(s)
        for m in turn:
            try:
                if hook and m.webhook_id == hook.id:
                    await hook.delete_message(m.id, thread=th)
                else:
                    await m.delete()  # tin bot tự gửi; tin của webhook cũ thì cần quyền Manage Messages
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                print(f"[reroll] không xoá được tin ({e.status})")
                return
        s["affinity"], s["aff_last"] = max(0, min(100, aff(s) - s.get("aff_last", 0))), 0  # hoàn điểm của lượt bị xoá, khỏi tính đôi
        s["last_input_id"] = before.id - 1  # tin người dùng cuối thành "chưa trả lời": build_messages trả lời lại và xếp nó xuống cuối
        await respond(th, s, fallback)


if __name__ == "__main__":
    if not TOKEN or not MODELS:
        sys.exit("Thiếu DISCORD_TOKEN hoặc LLM_MODELS trong .env")
    bot.run(TOKEN)
