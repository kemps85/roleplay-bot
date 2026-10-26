# Kế hoạch nâng cấp bot Roleplay (CHỜ CHỐT — chưa làm)

## 🎛️ Bảng điều khiển đầu thread
Ghim ở đầu thread, nút bấm hoạt động lại được sau khi bot khởi động lại (persistent view).

**Hàng 1, thiết lập**
- ✏️ **Nhân vật**: sửa tên và tính cách giữa chừng (modal).
- 🌍 **Bối cảnh**: thời gian, địa điểm, tình huống. Đổi bối cảnh thì chuyển cảnh.
- 🖼️ **Ảnh**: up ảnh trong modal (FileUpload), thay cho `/doianh`.
- 🎨 **Màu khung**

**Hàng 2, lúc chơi**
- 🔄 **Viết lại**: xoá câu trả lời vừa rồi của nhân vật và sinh câu khác.
- ⏭️ **Tiếp tục**: nhân vật kể tiếp mà không cần người dùng nhắn.
- ↩️ **Hoàn tác**: xoá lượt gần nhất của cả người dùng và nhân vật. Tin của người dùng thì bot xoá (cần quyền Manage Messages) hoặc đánh dấu bỏ qua.
- 🛑 **Kết thúc**

## Bổ sung
- 👤 **Vai của bạn**: mỗi người khai tên và mô tả vai của mình, lưu theo từng thread và từng user, đưa vào prompt.
- 📝 **Ghi nhớ**: xem bản tóm tắt hiện tại, thêm hoặc xoá các chi tiết ghim (pinned facts luôn có trong prompt).
- 📏 **Độ dài trả lời**: ngắn, vừa hoặc dài, chỉnh max_tokens và câu dặn trong prompt.
- 💬 **Chat ngoài lề**: tin bắt đầu bằng `//` thì bot bỏ qua và không đưa vào lịch sử.
- 📚 **Lưu thành mẫu**: lưu nhân vật (tên, tính cách, ảnh, màu) vào `templates.json` và `templates/`, rồi hiện trong menu `/roleplay`.

## Dọn dẹp
- **Xoá thread**: xoá phiên khỏi `sessions.json`, xoá ảnh trong `avatars/` và xoá webhook. Mẫu đã lưu thì giữ nguyên.
- **Kết thúc**: giữ lại setup (archive và lock thread, xoá webhook).

## Đã chốt trước đó
- Không cắt avatar, giữ nguyên ảnh gốc.
