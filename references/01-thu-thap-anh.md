# Thu thập ý tưởng + sinh ảnh (ChatGPT & Gemini)

**Bản checkpoint mới:** đọc mục Phỏng vấn ở checkpoint interview; sinh ảnh tài sản ở assets, dựng thẻ/dây ở scenes rồi mới sinh storyboard ở storyboards. Giá trị generated/failed/skipped từ autofill phải được xử lý hết; ảnh rời không được tính. Gắn ảnh trực tiếp vào node bằng autofill. Nếu có mâu thuẫn, theo SKILL.md và 00-checkpoint.md.

Dùng cho bước 2 và 3 của SKILL.md. Đọc đúng phần cần, không cần đọc cả tệp.

## Phỏng vấn (bước 2) — đúng 5 câu, mỗi lượt một câu

Hỏi tuần tự, không hỏi hai câu cùng lúc, không tự bịa thêm câu hỏi về phong
cách/tỉ lệ/số cảnh (máy tự quyết phần đó):

1. **Chủ đề** — đưa 8 chủ đề + một dòng «chọn số 1–8 hoặc tự gõ chủ đề riêng»:
   1. Quái vật khổng lồ thức tỉnh · 2. Biến dị sinh học · 3. Tận thế sau đại dịch ·
   4. Ký sinh trùng trong cơ thể người · 5. Thế giới bị nấm xâm chiếm ·
   6. Sinh vật dưới đáy vực sâu · 7. Người lai thú giữa đô thị ·
   8. Thành phố bỏ hoang có thứ đang sống.
2. **Tên phim** — gợi ý 4 tên kèm tiền đề một câu; chọn số 1–4 hoặc gõ tên riêng.
3. **Thời lượng** — gõ số phút (tối thiểu 3).
4. **Ngôn ngữ lời thoại** — 1. Anh–Mỹ · 2. Đức · 3. Pháp · 4. Tây Ban Nha · 5. Khác.
5. **Dàn nhân vật** — gợi ý 4 phương án (tuổi, vai trò, mối đe doạ); chọn 1–4.

Ghi kết quả 5 mục vào bản ghi nhớ tạm (chủ đề / tên phim / thời lượng / ngôn ngữ /
dàn nhân vật). Đây là «bảng dữ kiện» để bước sau không phải hỏi lại.

## Sinh ảnh (bước 3) — sinh cho thứ phim CÓ, theo thứ tự cần dùng

Thứ tự cần dùng, không theo ý người bấm (bỏ nhóm nào phim không có):

1. Nhân vật (người/sinh vật/quái vật) — ảnh diện mạo.
2. Bối cảnh — toàn cảnh, không có người.
3. Đạo cụ — vật thể trên nền trơn.
4. Phong cách — bảng màu, ánh sáng, chất liệu.
5. Storyboard từng cảnh — sau cùng, vì nó dựa trên ảnh tài sản ở trên.

Đây là **thứ tự ưu tiên**, không phải danh sách bắt buộc đủ: phim không có đạo cụ
thì không tạo thẻ đạo cụ; phim chỉ 1 nhân vật, 1 cảnh thì chỉ cần 2 ảnh. Nhưng
**thứ phim có thì phải có ảnh**:

- nhân vật/sinh vật ghi trong brief → có thẻ tài sản mang ảnh;
- mỗi cảnh → có ảnh storyboard;
- bối cảnh/đạo cụ/phong cách đã lập thẻ → thẻ đó có ảnh.

Thiếu mấy thứ đó là **chưa qua checkpoint ảnh**: `scripts/kiem-anh.py` in «CHẶN» và bước
sinh video không được phép chạy.

Máy chủ tự soạn câu mô tả khi dùng «sinh ảnh tự động»; tự gõ câu thì **tả 7 phần**
(chủ thể · diện mạo · tư thế · môi trường · góc máy · ánh sáng · phong cách),
**không viết chữ «storyboard»**, luôn thêm «không chữ, không viền, không ô chú thích».

## Ba tuyến ảnh trên máy chủ 8001 (không tốn GPU thuê)

| Việc | Gọi | Tham số chính |
| --- | --- | --- |
| Sinh 1–4 ảnh (ChatGPT `gpt-image-2.5` qua tổng đài) | `POST /api/v1/images/generate` | `prompt`, `size`, `count` (1–4), `aspect` |
| Ảnh storyboard bằng Gemini (bể tài khoản) | `POST /api/v1/images/generate-gemini` | `prompt`, `references` (object_key), `aspect`, `count` |
| Sinh tự động cả bảng theo thứ tự | `POST /api/v1/images/autofill` | `canvas_id`, `scope` (assets/storyboards/all), `limit` (≤12) |

Ví dụ một ảnh nhân vật 16:9:
```bash
curl -sS -X POST http://127.0.0.1:8001/api/v1/images/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Chân dung một bác sĩ sinh học thực địa, áo dã chiến, ánh sáng lạnh, 16:9, không chữ, không viền, không ô chú thích","aspect":"16:9"}'
```
Trả `{"ok": true, "object_key": "...", "width": ..., "height": ...}`; `ok:false`
kèm `error.code` thì đọc mã lỗi rồi tra `LOI_THUONG_GAP.md` của dự án.

Ảnh sinh ra nằm trong kho (khoá `object_key`). Tuyến autofill gắn ảnh trực tiếp lên đúng thẻ tài sản hoặc cảnh; ảnh rời không được tính.

## Số đo thật (đã kiểm chứng, đừng hứa khác)

| Việc | Kết quả | Thời gian |
| --- | --- | --- |
| Ảnh nhân vật | 1024×1536 | 32,6 giây |
| Ảnh một cảnh 16:9 | 1672×941 | 35,9 giây |
| Ảnh Gemini dự phòng | 1376×768 | 13,45 giây |
