# Remielle Dan — lời thoại và chỉ mục nguồn đã kiểm tra

Ngày kiểm tra: **25/10/2026**. Ngôn ngữ ưu tiên: **Việt → Trung giản thể → Nhật**. Không dùng tiếng Anh làm bản thay thế.

## 1. Kết quả và giới hạn

Đã đọc `personality_voice.md` và `youtube_giabaolam.md` trước khi nghiên cứu. Phát hiện mới quan trọng là **đọc được TextMap và cấu hình tin nhắn của ZenlessData**, thay vì tiếp tục dựa vào bản chép phụ đề video.

**Đây là bản nghiên cứu có trích đoạn ngắn và chỉ mục tra cứu, không phải bản chép toàn bộ lời thoại.** Không thể cung cấp hàng loạt nguyên văn có bản quyền chưa được người dùng cung cấp; các vị trí không trích nguyên văn được ghi rõ bằng khóa dữ liệu, không điền lời diễn giải vào ô lời thoại. Bản này vì vậy chỉ hoàn thành một phần mục tiêu sưu tập nguyên văn.

Các tầng bằng chứng phải phân biệt:

1. **HoYoWiki chính thức:** trang nhân vật do HoYoverse cung cấp, truy cập lại thành công bằng API ở cả ba ngôn ngữ.
2. **ZenlessData:** kho dữ liệu cộng đồng, tự mô tả là dữ liệu bản phát hành; không phải GitHub chính thức của HoYoverse. Văn bản được đọc trực tiếp từ dump, không dịch lại. Việc một chuỗi có trong dump **không tự chứng minh đã xuất hiện trong bản game đang vận hành**, đặc biệt các đường dẫn mang nhãn `test`.
3. **Wiki Nhật/BWIKI:** bản chép cộng đồng; hữu ích đối chiếu, không đồng nghĩa nguồn phát hành chính thức.
4. **Ghi chú YouTube cũ:** không được nâng thành bản chép chính xác chỉ vì trông khớp nghĩa. Phụ đề tự động Nhật không dùng làm lời chính thức.

### Mốc dữ liệu cố định

- Kho: [malu-no996/ZenlessData](https://github.com/malu-no996/ZenlessData).
- Commit đã đọc: [`1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23`](https://github.com/malu-no996/ZenlessData/commit/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23).
- Thông điệp commit: `CNPRODWin3.2.0_R19329161_S19159270_D19329161`.
- Cây GitHub API: **20.241 mục, `truncated=false`**. Đây là số mục của cây kho, không phải số tệp hội thoại.
- Đã đọc đủ base + overwrite của VI, CN, JA. VI base có **427.439 khóa**, overwrite có **4.365 khóa**. Khi khóa trùng, tra overwrite trước. Không xóa khoảng trắng hoặc chuẩn hóa khóa.

### Đường dẫn nguồn dùng trong tài liệu

Các mã nguồn dưới đây đều trỏ tới commit cố định nói trên:

| Mã | Tệp / URL |
|---|---|
| VI | [TextMap/TextMap_VITemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/TextMap/TextMap_VITemplateTb.json) |
| VI-O | [TextMap/TextMap_VIOverwriteTemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/TextMap/TextMap_VIOverwriteTemplateTb.json) |
| CN | [TextMap/TextMapTemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/TextMap/TextMapTemplateTb.json) |
| CN-O | [TextMap/TextMapOverwriteTemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/TextMap/TextMapOverwriteTemplateTb.json) |
| JA | [TextMap/TextMap_JATemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/TextMap/TextMap_JATemplateTb.json) |
| JA-O | [TextMap/TextMap_JAOverwriteTemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/TextMap/TextMap_JAOverwriteTemplateTb.json) |
| MSG | [FileCfg/MessageConfigTemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/FileCfg/MessageConfigTemplateTb.json) |
| NPC | [FileCfg/MessageNPCTemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/FileCfg/MessageNPCTemplateTb.json) |
| PARTNER | [FileCfg/PartnerConfigTemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/FileCfg/PartnerConfigTemplateTb.json) |
| TALENT | [FileCfg/AvatarTalentTemplateTb.json](https://raw.githubusercontent.com/malu-no996/ZenlessData/1277ebca4b8a7a6c3bcbaac6d5708dc9f4a55f23/FileCfg/AvatarTalentTemplateTb.json) |
| HW | [HoYoWiki entry 1112](https://wiki.hoyolab.com/pc/zzz/entry/1112) / [API entry_page](https://sg-wiki-api-static.hoyolab.com/hoyowiki/zzz/wapi/entry_page?entry_page_id=1112) |

API HW cần header `x-rpc-wiki_app: zzz`, cùng `x-rpc-language: vi-vn`, `zh-cn` hoặc `ja-jp`. Ngôn ngữ là header, không phải suy ra từ URL API.

## 2. Trích đoạn nguyên văn ngắn

Không đổi dấu ba chấm, dấu câu hoặc tự thay đại từ. Các trích dẫn sau là toàn bộ câu ngắn ở vị trí đã chỉ rõ; phần chỉ mục phía sau không phải lời thoại được viết lại.

### 2.1. Tiếng Việt

| Loại | Nguyên văn | Nguồn / vị trí | Mức xác minh |
|---|---|---|---|
| Mindscape M4 — lời kết | Này, muốn cùng tôi... nhảy một bài không? | VI / VI-O, `Remielle_Talent_04_Desc_02`, câu trong ngoặc kép cuối đoạn; TALENT gắn với nhân vật 1581 | Đọc trực tiếp dump; cùng loại nội dung với module Phim Ý Cảnh chính thức |
| Điện thoại — đáp tin nhắn | Vậy mới ra dáng đồng phạm chứ | VI / VI-O, `Message_45800326`; MSG record `45800326`, nhóm `458003` | Có chuỗi nối cấu hình người gửi, không chỉ trùng tên |

### 2.2. Tiếng Trung giản thể

| Loại | Nguyên văn | Nguồn / vị trí |
|---|---|---|
| Mindscape M4 — lời kết | 「嗨，要和我…共舞一曲吗？」 | CN / CN-O, `Remielle_Talent_04_Desc_02`, dòng cuối |

### 2.3. Tiếng Nhật

| Loại | Nguyên văn | Nguồn / vị trí |
|---|---|---|
| Mindscape M4 — lời kết | 「ねえ、私と一曲、踊らない？」 | JA / JA-O, `Remielle_Talent_04_Desc_02`, dòng cuối |

## 3. Agent-profile quotes và sáu Mindscape: vị trí chính xác

Đã tìm thấy nguyên văn trong nguồn, nhưng không chép hàng loạt tại đây. **Không phải khoảng trống dữ liệu**: đây là giới hạn tái bản. Một khóa ở bảng có thể chứa cả lời dẫn và lời nhiều nhân vật, không được dùng toàn bộ giá trị làm lời Remielle.

| Loại | Vị trí cần mở | Cách xác định đúng lời cô |
|---|---|---|
| Câu giới thiệu nhân vật | HW `data.page.desc`, cả VI/CN/JA | Lấy câu được ký tên Remielle Dan / 蕾米埃尔·丹 / レミエール・ダン. Không lấy câu ký tên Cissia, thành viên Bang Um Ne, phim hoặc sách lịch sử. Thứ tự các câu khác nhau giữa các ngôn ngữ. |
| M1 | `Remielle_Talent_01_Desc_02` | Câu cô phàn nàn với Beli. **Dòng thoại cuối cùng của cả đoạn là câu Beli trả lời**, không phải lời Remielle. Không dùng quy tắc lấy câu trích dẫn cuối cùng cho M1. |
| M2 | `Remielle_Talent_02_Desc_02` | Câu trong ngoặc kép cuối đoạn; cảnh vũ hội. |
| M3 | `Remielle_Talent_03_Desc_02` | Câu trong ngoặc kép cuối đoạn. |
| M4 | `Remielle_Talent_04_Desc_02` | Câu trong ngoặc kép cuối đoạn; đã trích ngắn ở mục 2. |
| M5 | `Remielle_Talent_05_Desc_02` | Câu trong ngoặc kép cuối đoạn. |
| M6 | `Remielle_Talent_06_Desc_02` | Câu trong ngoặc kép cuối đoạn; giữ placeholder giới tính trong VI. |
| Trang phục | `AvatarSkin_RemielleOrigin_Desc_001`, `_002`, `_003` | Có lời hướng tới người đối thoại; không mặc định mọi lời dẫn trong mô tả trang phục đều là thoại được lồng tiếng. |
| Hồ sơ | `Partner_ProfileDesc_1581`, `Partner_ProfileDesc_1581_1` | Đây là hồ sơ mô tả, không phải bộ voice-over About Us. |
| Nhận xét của Proxy | `Partner_Impression_f_1581`, `Partner_Impression_m_1581` | **Không phải Remielle nói.** |
| Ngày sinh | `Partner_Birthday_1581` | Dữ liệu ngày sinh, **không phải câu chúc sinh nhật**. |

Tất cả khóa TextMap trên tra ở VI → CN → JA, mỗi ngôn ngữ áp overwrite tương ứng. Module HW `id="4"` là Phim Ý Cảnh, `id="6"` là Thiết Lập Nhân Vật.

## 4. Điện thoại: bằng chứng gán người gửi

Đây là tiến triển rõ nhất so với hai ghi chú cũ.

### Chuỗi nối đã kiểm tra

1. Trong PARTNER, record của Remielle có `PBNPPFFJCGN=1581`, `AAADFNAAAJJ=Partner_Name_1581`, `CNADDEKOAIO=Remielle`, `ADBMDAODKHF=261581`.
2. Trong NPC, **ba ID `10182`, `10183`, `10185`** đều có `HAKHHHCAENA=Message_NPC142`.
3. `Message_NPC142` giải ra Remielle / 蕾米埃尔 / レミエール trong ba bản địa hóa.
4. Trong MSG, chọn record có `NMIFFJEFBJI` thuộc ba ID trên. Ở **97 record tìm được**, `HPKJODNLJOA` cũng trùng cùng ID; `LDHNMACDKLH` là khóa nội dung.
5. **Cả 97 khóa đều có văn bản VI, CN và JA** trong các map đã đọc. Không có record trong tập này bị thiếu văn bản VI; không có record mà hai trường ID nói trên mâu thuẫn.

Tên trường bị obfuscate nên ý nghĩa trường là **suy luận cấu trúc**, không phải schema chính thức được giải mã. Tuy nhiên, kiểm tra cả nhóm `458001` cho thấy các record trả lời của người chơi có ID `0` và khóa nội dung chính trống; các record Remielle có hai trường ID cùng là `10182` và khóa `Message_*`. Tin nhắn mời tới nhà ở đầu nhóm này còn khớp bối cảnh video cũ. Độ chắc chắn gán người gửi cao hơn đáng kể so với ghép khóa `_Name_` với số thứ tự.

Không tính 97 record là 97 sự kiện riêng, không tuyên bố đã kiểm chứng từng nhánh hiển thị trực tiếp trong game. Các record nhóm `601*` không tự động được gọi là trust-event: nội dung có bối cảnh sự kiện/đi dạo nhưng chưa nối đầy đủ với cấu hình nhiệm vụ.

## 5. Hangout, trust-event, trò chuyện đô thị: đã tìm thấy gì?

Tập khóa mang stem `PartnerRemielle` trong bản VI có:

| Họ khóa | Số khóa gồm cả nhãn tên | Nhận định |
|---|---:|---|
| `PartnerTalk_BubbleStory_PartnerRemielle` | 66 | Thoại nổi/ambient theo cấu trúc tên khóa; chưa gán từng người nói. |
| `PartnerTalk_ChatAudio_PartnerRemielle` | 65 | 62 khóa nội dung và 3 nhãn tên. Không coi đây là standard VO. |
| `PartnerTalk_Chat_PartnerRemielle` | 585 | Hội thoại gồm nhiều người, lựa chọn và lời dẫn. |
| `PartnerTalk_GalGame_PartnerRemielle` | 249 | 239 khóa không mang `_Name_`; không tự nhận tất cả là lời Remielle. |
| `PartnerTalk_OngoingMainCityPartner_PartnerRemielle` | 14 | Có cả nhãn tên; cần nối cấu hình trước khi gán. |
| `PartnerTalk_OngoingMainCity_PartnerRemielle` | 28 | Có cả nhãn tên; cần nối cấu hình trước khi gán. |

**Các con số trên là số khóa, không phải số câu đã chứng minh Remielle nói.** Một câu có thể có nhánh Wise/Belle riêng hoặc nhiều mảnh; một nhãn tên không chứng minh tất cả các khóa cùng stem thuộc về cô.

### Các điểm mở ưu tiên, không lặp lại phần video đã biết

- `PartnerTalk_ChatAudio_PartnerRemielle_330580001`: 20 khóa nội dung; nói chuyện về học viện, Bangboo và quá trình thiết kế. Nhãn `_Name_01` là Remielle.
- `PartnerTalk_ChatAudio_PartnerRemielle_330580002`: 23 khóa nội dung; mở đầu bằng chuyện gặp nhau ban đêm và ngắm hoàng hôn. Nhãn `_Name_01` là Remielle.
- `PartnerTalk_ChatAudio_PartnerRemielle_330580003`: 19 khóa nội dung; mở đầu bằng chuyện Proxy và người thân trân trọng tiệm băng hình. Nhãn `_Name_01` là Remielle.
- `PartnerTalk_Chat_PartnerRemielle_330580008_09`: có câu cô tự nói tên thật khi nói với Burnice. Nhóm `_330580008` có **37 khóa nội dung**, có nhiều người nói; không lấy cả nhóm làm lời cô.
- `PartnerTalk_GalGame_PartnerRemielle_105800002_030` và `_031`: cặp câu ứng với Proxy nữ/nam, khớp cảnh trạm gác đã mô tả trong ghi chú YouTube. Dùng để đối chiếu, không coi là phát hiện thêm một sự kiện.
- `PartnerTalk_GalGame_PartnerRemielle_105800002_043`: vị trí đầy đủ của đoạn ngừng trêu rồi chỉ vật đang quan sát, chỗ ghi chú video cũ đọc chưa chắc.
- `PartnerTalk_GalGame_PartnerRemielle_105800003_006`, `_007`, `_082`, `_083`: có cặp xưng hô giới tính riêng. Không hợp nhất bằng cách tự sửa cô thành cậu.

### Đối chiếu tiếng Nhật mới tìm được

[Wiki Nhật: 信頼イベント/レミエール](https://wikiwiki.jp/zenless/信頼イベント/レミエール) đọc được; nội dung có bảng tên người nói tách riêng, không chỉ lời kể bài cảm nhận:

- Neo `ue4788ae`: cửa hàng hoa tại Luminous Square; đối thoại với Lan, hoa hướng dương/bồ công anh, sau đó đi dạo ven sông.
- Neo `ne8ca011`: vách đá Blazewood; có Burnice, biệt danh giả được nhắc tới, chăm sóc cánh và lời trêu sau khi Proxy tỉnh.
- Phần sửa Bangboo: có lựa chọn của người chơi và thoại NPC xen kẽ, motif đồng phạm được dùng thành trò đùa về trách nhiệm.

Đây vẫn là **bản chép cộng đồng tiếng Nhật**, chưa phải nguồn chính thức cho nguyên văn Việt. Không dịch những câu Nhật này sang Việt rồi gắn nhãn bản địa hóa chính thức. Nội dung hiển thị giữa bản tìm kiếm và bản mở trang có thể khác nhau; ưu tiên bản trang thực đọc được, không tự ghép thành transcript hoàn chỉnh.

## 6. Phong cách nói — suy luận có giới hạn

Các nhận xét dưới đây là phân tích, không phải câu thoại mới. Bằng chứng ưu tiên là tin nhắn đã nối ID và các câu Mindscape/profile, không dựa vào fanfic hay giọng AI.

### Xưng hô và biệt danh

- Bản Việt dùng **tôi**; đối với Wise là **cậu**, Belle là **cô**. Các placeholder như `{F#cô}{M#cậu}` phải được giữ nguyên khi lưu bản thô. Cụ thể M6 và tin nhắn `45800109` có cấu trúc giới tính này.
- Cách gọi đặc trưng là **đồng phạm**, có biến thể **Quý ngài đồng phạm / Quý cô đồng phạm**. Bằng chứng: `Message_45800208`, `Message_45800301`, `Message_45800401`, `Message_45800601`, `Message_45800701`; các cặp GalGame ở mục 5.
- **Chủ tiệm** gắn với vai trò quản lý tiệm băng hình, có ở `Message_45800103`; không mặc định đó là biệt danh cô dùng mọi lúc.
- Nhận định về **quý ngài thám tử** đã có trong ghi chú video cũ, nhưng lượt này chưa nối được chính xác câu đó với record người nói; không nâng lên ngang tập tin nhắn đã kiểm chứng.
- CN và JA có bản địa hóa riêng. Không dùng cách xưng hô Nhật để tự viết lại câu Việt.

### Hạt tình thái, nhịp và hài hước

- Mềm hóa lời bằng **nhỉ, nhé, nha, đó, chứ**, câu hỏi đuôi và dấu `~`. Các vị trí rõ: `Message_45800108`, `45800111`, `45800210`, `45800216`, `45800401`, `45800326`.
- Có nhịp ngập ngừng hoặc cố tình giữ lại thông tin, dùng dấu ba chấm rồi chuyển thành câu đố. Xem `Message_601060102`, `601060103`, `601060106`, `601060109`.
- Trêu bằng **vờ trách người kia quên mình**, hoặc biến một cuộc hẹn thành chuyện phạm tội/đồng phạm. Xem nhóm `458003`–`458007`. Đó là cách tạo thân mật qua diễn vai, không có cơ sở biến thành lời đe dọa thật.
- Đôi khi nói rất đời thường, thậm chí ngắn cụt như chat điện thoại: trong nhóm `458002` có chuỗi nói về đang ở trên không và tín hiệu kém. Vì vậy không nên ép mọi câu thành văn chương dài, bí hiểm hoặc tán tỉnh liên tục.
- Khung hẹn hò và chuẩn bị diện mạo có trong `458002`; trò đùa thân mật không phải bằng chứng cho quan hệ yêu đương đã được xác lập.
- Câu Mindscape M4 dùng lời mời nhẹ, không mệnh lệnh. Các Mindscape khác cho phép nghiên cứu sự thay đổi sắc thái nghiêm túc, nhưng **chưa có corpus chiến đấu** để kết luận cô không bao giờ quát.

### Những điều không được gán cho cô

**Không thể chứng minh “cô không bao giờ nói X” bằng tập dữ liệu chưa đầy đủ.** Cách kết luận đúng là “chưa thấy trong tập đã xác minh”.

- Chưa có cơ sở đặt **em–anh**, cách gọi tình nhân hoặc lời tỏ tình trực tiếp thành quy tắc nói chuyện mặc định.
- Chưa có bằng chứng từ bộ VO để khẳng định cô luôn nhẹ giọng, không chửi hoặc không hô lớn khi chiến đấu.
- Không dùng ngày sinh trong hồ sơ để sáng tác lời chúc sinh nhật; không dùng tiêu đề kỹ năng làm câu hô kỹ năng.
- Không coi Cissia gọi cô là người phụ nữ xấu xa, hoặc lời Proxy nhận xét về cô, là cách Remielle tự xưng.
- Không lấy việc nhắc tên Remielle làm bằng chứng người nói là Remielle. Trường hợp rất rõ: nhóm `Activity_Chat_ActivityRemielle_30060131` mở đầu bằng Sigrid và chuyên viên công vụ.
- Không thể khẳng định sở thích đồ ngọt từ các nguồn đã kiểm tra ở đây; cũng không được biến “chưa có bằng chứng” thành “cô ghét đồ ngọt”.

## 7. Nhật ký truy cập và khoảng trống

| Tuyến đã thử | Kết quả lượt này | Hệ quả |
|---|---|---|
| GitHub API + raw | Đọc được bằng `gh api`; metadata, cây và TextMaps/config đều có dữ liệu | Dùng làm nguồn nghiên cứu chính, ghim commit |
| PowerShell Invoke-RestMethod / curl.exe | Lỗi xác thực TLS/Schannel tại môi trường, không phải chứng cứ kho bị khóa | Đổi sang GitHub CLI; không tiếp tục lặp cùng lỗi |
| HoYoWiki API | Node fetch trả `retcode=0` cho VI/CN/JA | Module `id=7`, component `voice`, đều có `data=""`; xác nhận lại khoảng trống VO |
| Fandom `/Remielle_Dan/Voice-Overs` và `/Chinese` | Web open không truy cập được | Không có transcript đáng dùng; không gán mã HTTP cũ cho lần thử này |
| BWIKI trang nhân vật | Đọc được trang chính, không tìm thấy mục `语音` trong văn bản trả về | Trang chính không cung cấp được bộ VO |
| BWIKI `/蕾米埃尔/语音` | Không truy cập được | Giữ là gap, không suy ra câu thoại không tồn tại |
| Miyoushe | Tìm theo tên + ngữ âm không cho nguồn thích hợp; URL tìm kiếm trực tiếp không đọc được | Không có câu được xác minh từ tuyến này |
| Wiki Nhật trang nhân vật | Đọc được, không thấy `ボイス` trong văn bản trả về | Không lấy stat/skill làm thoại |
| Wiki Nhật trust-event | Đọc được các bảng hội thoại | Nguồn đối chiếu cộng đồng, chưa thay thế game dump |
| Trang character chính thức bản Việt | Trả trang không có văn bản đọc được qua web | Không bổ sung được transcript từ trang này |

### Các loại còn thiếu

- **Greeting / chào hỏi standard VO:** chưa xác định được bản ghi đúng loại.
- **About Us / chat standard VO:** chưa có; `PartnerTalk_ChatAudio` là nhóm khác, không đổi nhãn.
- **Hobbies standard VO:** chưa có bản ghi được gắn đúng loại.
- **Birthday voice-over:** chưa có; khóa ngày sinh không đáp ứng yêu cầu này.
- **Idle và combat/skill shouts:** chưa có liên kết đáng tin giữa câu chữ, sự kiện âm thanh và nhân vật.
- **Mọi nhánh hangout/trust:** đã tìm được nhiều khóa nhưng chưa gán từng người nói; chỉ mục không phải transcript đã hoàn tất.
- **Kiểm tra âm thanh nguyên gốc:** chưa nghe/đối chiếu audio; chưa có chứng minh text–audio join.

`Data/_unsorted/VoiceData.json` đã đọc: có `allExternalEvents`, `allPrefixes`, `specificPckList`, `voidBlocks`. Có các prefix Remielle cho Accompany/Chat và cả đường dẫn `Ver3_3/test`. `Data/JsonBytes/Audio/AudioResourceData.json` có các bảng sự kiện/ngân hàng số. Đây chỉ là **metadata**, chưa cung cấp nội dung câu hoặc phép nối văn bản–âm thanh. Không báo cáo chúng như đã tìm được combat lines.

## 8. Chỉ mục tin nhắn đã nối ID

Mỗi dòng dưới là một record tin nhắn trong MSG và khóa nội dung tương ứng; **không phải chép nguyên văn**. Nguồn văn bản cho từng dòng: VI/VI-O → CN/CN-O → JA/JA-O ở bảng nguồn mục 1. Cột nguồn cụ thể ghi rõ khóa nằm trong base hay overwrite. “Người gửi” dựa vào chuỗi nối ở mục 4; chưa kiểm tra từng nhánh trong client live.

| Nhóm | Record MSG | Người gửi (NPC ID) | Khóa nguyên văn | Nguồn Việt | CN / JA |
|---|---:|---:|---|---|---|
| 458001 | 45800101 | 10182 | `Message_45800101` | VI | Có / Có |
| 458001 | 45800103 | 10182 | `Message_45800103` | VI | Có / Có |
| 458001 | 45800104 | 10182 | `Message_45800104` | VI | Có / Có |
| 458001 | 45800105 | 10182 | `Message_45800105` | VI | Có / Có |
| 458001 | 45800106 | 10182 | `Message_45800106` | VI | Có / Có |
| 458001 | 45800108 | 10182 | `Message_45800108` | VI | Có / Có |
| 458001 | 45800109 | 10182 | `Message_45800109` | VI | Có / Có |
| 458001 | 45800111 | 10182 | `Message_45800111` | VI | Có / Có |
| 458002 | 45800202 | 10182 | `Message_45800202` | VI | Có / Có |
| 458002 | 45800204 | 10182 | `Message_45800204` | VI | Có / Có |
| 458002 | 45800205 | 10182 | `Message_45800205` | VI | Có / Có |
| 458002 | 45800206 | 10182 | `Message_45800206` | VI | Có / Có |
| 458002 | 45800207 | 10182 | `Message_45800207` | VI | Có / Có |
| 458002 | 45800208 | 10182 | `Message_45800208` | VI | Có / Có |
| 458002 | 45800210 | 10182 | `Message_45800210` | VI | Có / Có |
| 458002 | 45800211 | 10182 | `Message_45800211` | VI | Có / Có |
| 458002 | 45800212 | 10182 | `Message_45800212` | VI | Có / Có |
| 458002 | 45800213 | 10182 | `Message_45800213` | VI | Có / Có |
| 458002 | 45800215 | 10182 | `Message_45800215` | VI | Có / Có |
| 458002 | 45800216 | 10182 | `Message_45800216` | VI | Có / Có |
| 458002 | 45800218 | 10182 | `Message_45800218` | VI | Có / Có |
| 458002 | 45800219 | 10182 | `Message_45800219` | VI | Có / Có |
| 458002 | 45800221 | 10182 | `Message_45800221` | VI | Có / Có |
| 458002 | 45800222 | 10182 | `Message_45800222` | VI | Có / Có |
| 458002 | 45800223 | 10182 | `Message_45800223` | VI | Có / Có |
| 458002 | 45800225 | 10182 | `Message_45800225` | VI | Có / Có |
| 458002 | 45800227 | 10182 | `Message_45800227` | VI | Có / Có |
| 458002 | 45800228 | 10182 | `Message_45800228` | VI | Có / Có |
| 458002 | 45800230 | 10182 | `Message_45800230` | VI | Có / Có |
| 458002 | 45800231 | 10182 | `Message_45800231` | VI | Có / Có |
| 458002 | 45800232 | 10182 | `Message_45800232` | VI | Có / Có |
| 458002 | 45800233 | 10182 | `Message_45800233` | VI | Có / Có |
| 458002 | 45800235 | 10182 | `Message_45800235` | VI | Có / Có |
| 458002 | 45800236 | 10182 | `Message_45800236` | VI | Có / Có |
| 458003 | 45800301 | 10182 | `Message_45800301` | VI | Có / Có |
| 458003 | 45800302 | 10182 | `Message_45800302` | VI | Có / Có |
| 458003 | 45800303 | 10182 | `Message_45800303` | VI | Có / Có |
| 458003 | 45800305 | 10182 | `Message_45800305` | VI | Có / Có |
| 458003 | 45800306 | 10182 | `Message_45800306` | VI | Có / Có |
| 458003 | 45800308 | 10182 | `Message_45800308` | VI | Có / Có |
| 458003 | 45800309 | 10182 | `Message_45800309` | VI | Có / Có |
| 458003 | 45800311 | 10182 | `Message_45800311` | VI | Có / Có |
| 458003 | 45800312 | 10182 | `Message_45800312` | VI | Có / Có |
| 458003 | 45800313 | 10182 | `Message_45800313` | VI | Có / Có |
| 458003 | 45800314 | 10182 | `Message_45800314` | VI | Có / Có |
| 458003 | 45800315 | 10182 | `Message_45800315` | VI | Có / Có |
| 458003 | 45800317 | 10182 | `Message_45800317` | VI | Có / Có |
| 458003 | 45800318 | 10182 | `Message_45800318` | VI | Có / Có |
| 458003 | 45800319 | 10182 | `Message_45800319` | VI | Có / Có |
| 458003 | 45800320 | 10182 | `Message_45800320` | VI | Có / Có |
| 458003 | 45800321 | 10182 | `Message_45800321` | VI | Có / Có |
| 458003 | 45800323 | 10182 | `Message_45800323` | VI | Có / Có |
| 458003 | 45800324 | 10182 | `Message_45800324` | VI | Có / Có |
| 458003 | 45800326 | 10182 | `Message_45800326` | VI | Có / Có |
| 458003 | 45800327 | 10182 | `Message_45800327` | VI | Có / Có |
| 458003 | 45800328 | 10182 | `Message_45800328` | VI | Có / Có |
| 458003 | 45800330 | 10182 | `Message_45800330` | VI | Có / Có |
| 458003 | 45800331 | 10182 | `Message_45800331` | VI | Có / Có |
| 458003 | 45800332 | 10182 | `Message_45800332` | VI | Có / Có |
| 458004 | 45800401 | 10182 | `Message_45800401` | VI | Có / Có |
| 458004 | 45800402 | 10182 | `Message_45800402` | VI | Có / Có |
| 458004 | 45800404 | 10182 | `Message_45800404` | VI | Có / Có |
| 458004 | 45800405 | 10182 | `Message_45800405` | VI | Có / Có |
| 458004 | 45800406 | 10182 | `Message_45800406` | VI | Có / Có |
| 458005 | 45800501 | 10182 | `Message_45800501` | VI | Có / Có |
| 458005 | 45800502 | 10182 | `Message_45800502` | VI | Có / Có |
| 458005 | 45800503 | 10182 | `Message_45800503` | VI | Có / Có |
| 458005 | 45800505 | 10182 | `Message_45800505` | VI | Có / Có |
| 458005 | 45800506 | 10182 | `Message_45800506` | VI | Có / Có |
| 458005 | 45800507 | 10182 | `Message_45800507` | VI | Có / Có |
| 458005 | 45800508 | 10182 | `Message_45800508` | VI | Có / Có |
| 458006 | 45800601 | 10182 | `Message_45800601` | VI | Có / Có |
| 458006 | 45800602 | 10182 | `Message_45800602` | VI | Có / Có |
| 458006 | 45800603 | 10182 | `Message_45800603` | VI | Có / Có |
| 458006 | 45800605 | 10182 | `Message_45800605` | VI | Có / Có |
| 458006 | 45800606 | 10182 | `Message_45800606` | VI | Có / Có |
| 458006 | 45800607 | 10182 | `Message_45800607` | VI | Có / Có |
| 458006 | 45800608 | 10182 | `Message_45800608` | VI | Có / Có |
| 458006 | 45800609 | 10182 | `Message_45800609` | VI | Có / Có |
| 458007 | 45800701 | 10182 | `Message_45800701` | VI | Có / Có |
| 458007 | 45800703 | 10182 | `Message_45800703` | VI | Có / Có |
| 458007 | 45800704 | 10182 | `Message_45800704` | VI | Có / Có |
| 458007 | 45800705 | 10182 | `Message_45800705` | VI | Có / Có |
| 458007 | 45800706 | 10182 | `Message_45800706` | VI | Có / Có |
| 458007 | 45800707 | 10182 | `Message_45800707` | VI | Có / Có |
| 6010601 | 601060102 | 10183 | `Message_601060102` | VI | Có / Có |
| 6010601 | 601060103 | 10183 | `Message_601060103` | VI | Có / Có |
| 6010601 | 601060104 | 10183 | `Message_601060104` | VI | Có / Có |
| 6010601 | 601060106 | 10183 | `Message_601060106` | VI | Có / Có |
| 6010601 | 601060107 | 10183 | `Message_601060107` | VI | Có / Có |
| 6010601 | 601060109 | 10183 | `Message_601060109` | VI | Có / Có |
| 6010902 | 601090201 | 10183 | `Message_601090201` | VI | Có / Có |
| 6010902 | 601090202 | 10183 | `Message_601090202` | VI | Có / Có |
| 6010902 | 601090203 | 10183 | `Message_601090203` | VI | Có / Có |
| 6010903 | 601090301 | 10183 | `Message_601090301` | VI | Có / Có |
| 6010903 | 601090302 | 10183 | `Message_601090302` | VI | Có / Có |
| 6010903 | 601090303 | 10183 | `Message_601090303` | VI | Có / Có |

## 9. Chỉ mục nhóm hangout/trust để tra cứu tiếp

Bảng này đếm khóa không chứa `_Name_`, không bảo đảm tất cả đều là lời nhân vật. Nguồn mỗi nhóm: VI/VI-O; đối chiếu cùng khóa tại CN/CN-O và JA/JA-O. `Chat`/`GalGame` chưa có phép nối người nói từng câu. Không gọi số khóa là số lời Remielle đã xác minh.

| Stem khóa | Số khóa nội dung VI | Nhãn tên / giới hạn |
|---|---:|---|
| `PartnerTalk_ChatAudio_PartnerRemielle_330580001` | 20 | `_Name_01` = Remielle; chưa xác minh audio |
| `PartnerTalk_ChatAudio_PartnerRemielle_330580002` | 23 | `_Name_01` = Remielle; chưa xác minh audio |
| `PartnerTalk_ChatAudio_PartnerRemielle_330580003` | 19 | `_Name_01` = Remielle; chưa xác minh audio |
| `PartnerTalk_Chat_PartnerRemielle_330580004` | 42 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580005` | 2 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580006` | 45 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580007` | 3 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580008` | 37 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580009` | 2 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580010` | 2 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580011` | 7 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580012` | 12 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580013` | 42 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580014` | 67 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580015` | 9 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580016` | 42 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580017` | 9 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580018` | 49 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580019` | 1 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580020` | 3 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580021` | 32 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580022` | 2 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580023` | 34 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580024` | 38 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580025` | 30 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580026` | 5 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580027` | 16 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580028` | 23 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580029` | 5 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580030` | 6 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_Chat_PartnerRemielle_330580031` | 13 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_GalGame_PartnerRemielle_105800001` | 85 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_GalGame_PartnerRemielle_105800002` | 69 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |
| `PartnerTalk_GalGame_PartnerRemielle_105800003` | 85 | Nhiều vai hoặc lựa chọn; chưa gán từng câu |

## 10. Ghi chú tái kiểm tra

- Chỉ ghi/chỉnh sửa `voice_lines.md` trong thư mục công việc; không chỉnh hai ghi chú đầu vào hoặc các ghi chú khác.
- Không tải toàn bộ kho xuống đĩa. Các JSON dùng để nghiên cứu được xử lý trong bộ nhớ tiến trình.
- Các bản TextMap và cấu hình kể trên được đọc qua `gh api` với URL raw cố định commit; không suy ra nội dung từ tên tệp.
- Công cụ Agent Reach theo môi trường local không khởi chạy được do đường dẫn Python nền không dùng được; kiểm tra cập nhật không hoàn tất. Điều này không ảnh hưởng dữ liệu GitHub đã đọc thành công qua CLI.
- Tài liệu là kết quả một lượt nghiên cứu giới hạn công cụ, chưa phải corpus đầy đủ hoặc bằng chứng user acceptance.
