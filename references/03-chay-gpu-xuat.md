# Chạy GPU + ghép phim + xuất

**Bản checkpoint mới:** đọc ở video/export. Chỉ deploy sau workflow.py preflight và đồng ý của operator. Không dùng các lệnh first_shot.py hay film_run minh họa để gửi phim thật: thử bằng cú đầu tiên qua workflow.py submit. Xuất qua workflow.py export và finish, không gọi trực tiếp timeline_export trong quy trình này.

Dùng cho bước 6 và 7 của SKILL.md.

## TRƯỚC KHI BẬT MÁY GPU — chạy cổng kiểm ảnh

Không có ảnh thì không sinh video. Chạy và đọc mã thoát:
```bash
python3 "$SKILL/scripts/kiem-anh.py" \
  --canvas-id <mã bảng vẽ> --brief <tệp brief.json>   # $SKILL = chỗ gói kỹ năng
```
- Mã thoát 0 («ĐỦ ẢNH») mới được bật máy GPU và nộp lệnh.
- Mã thoát 1 («CHẶN») thì quay lại bước 3 sinh ảnh — **không** bật GPU, **không**
  nộp lệnh chữ→video trần. Đã có lần bỏ qua bước này: 20 cú ra 20 khuôn mặt khác
  nhau (xem `BAI-HOC.md` ngày 2026-11-18).

## Máy GPU thuê (Modal A100) — bật, tắt, kiểm

Máy Mac là **não** (kịch bản, chia cú, câu mô tả, ghép phim); máy thuê là **cơ**
(chạy graph ComfyUI, trả tệp).

Bật (deploy lại — gọi địa chỉ không làm máy thức dậy sau khi đã `app stop`):
```bash
modal deploy <tệp ứng dụng Modal của dự án>     # đăng nhập profile đúng trước
curl -sS "<địa chỉ ComfyUI vừa deploy>/system_stats"
```
Tắt:
```bash
modal app stop -y <tên ứng dụng Modal>
```
Hoặc bảng điều khiển: `POST http://127.0.0.1:8899/api/gpu/sleep`.

Số đo thật (2026-11-17): A100-SXM4-80GB, ComfyUI 0.45.0; `modal deploy` 3,5 giây,
`/system_stats` trả 200 trong ~1 phút. Sau `app stop`, địa chỉ trả 404 mãi — phải
`deploy` lại.

## Bẫy đã gặp thật (đọc trước khi chạy)

- **Không lưu tệp quy trình lên máy thuê qua proxy Modal** (dấu `/` bị chặn, 405);
  bảng vẽ đặt trên máy này.
- **Cú hỏng phải sửa**: `shot.repair` chạy cho đúng cú đó (tối đa `--repair-attempts`,
  mặc định 1), ghi vào `repairs`; sửa không được mới dừng phim.
- **Video H3 bắt buộc có tiếng**; thiếu luồng tiếng là task bị đánh hỏng, không giao
  phim câm.
- **Mỗi lần hỏi `generation.refresh` phải đổi `command_id`** — không thì nhận lại câu
  cũ và tưởng còn chạy (lỗi từng làm giám sát kẹt 83 phút).
- Ảnh không gắn vào cảnh thì video không đổi; ảnh là khung đầu, phần sau do mô hình sinh.

## Thử cú 1.1 của chính phim

Sau khi có phép GPU và preflight, gửi cú 1.1 qua workflow.py submit, poll workflow.py refresh tới success có video hình + tiếng thật. Không gửi một cú thử khác hoặc gọi script bypass cổng.

## Xuất phim (bước 7)

1. Nối clip đúng thứ tự kịch bản (`timeline.append` / nút «Nối clip đã sinh»), ≤50
   thao tác mỗi lần, mỗi clip `duration_ms=5167`.
2. Sửa dòng thời gian nếu cần (`timeline.edit`: xoá/cắt/ẩn track).
3. Xuất qua `workflow.py export`, sau đó `workflow.py finish` để lấy đúng kết quả task.
4. Đo lại tệp ra bằng ffprobe: luồng hình + tiếng, codec, cỡ, thời lượng.
5. Đưa tệp ra chỗ bàn giao của người dùng và báo đúng tên tệp.

Đo tệp phim vừa ra:
```bash
ffprobe -v error -show_format -show_streams -of json "<chỗ bàn giao>/<ten-phim>.mp4"
```

Thời lượng đã đo thật: cú ~5,167 giây; cỡ 1344×768 nặng ~10 phút/cú (chỉ để thử),
cỡ 864×480 nhanh hơn ~2,5 lần (đường mặc định khi làm phim). Xuất 59 clip ≈ 2 phút 20 giây.

## Khi hỏng, nhìn gì

| Hiện tượng | Cách chữa |
| --- | --- |
| 404 ở `/mcp` hoặc `/health` | máy chủ chưa lên; khởi động lại uvicorn cổng 8001 |
| «mọi máy ComfyUI đều kín slot» | có lượt sinh bỏ ngang; khởi động lại máy chủ hoặc chờ `HT_SLOT_TTL_S` |
| Lệnh sinh báo `CAPABILITY_UNAVAILABLE` | model chưa có tệp mẫu quy trình trong dự án |
| ComfyUI «Required input is missing» | mẫu thiếu tham số bắt buộc; đối chiếu `/object_info` |
| Xuất báo «không đọc được thông tin clip đầu» | track hình có thẻ âm thanh; nối clip bỏ thẻ âm thanh |
| `chưa có ffmpeg ... không xuất được phim` | `kiểm ffmpeg trong PATH; cài nếu operator cho phép` |
