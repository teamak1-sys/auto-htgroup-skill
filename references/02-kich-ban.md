# Viết kịch bản + dựng bảng vẽ

**Bản checkpoint mới:** chỉ đọc brief ở plan, dựng thẻ ở scenes. Không dùng lệnh film_run hoặc first_shot.py để chạy video thật: các lệnh minh họa cũ ở cuối tệp không thuộc quy trình mới. Phải dùng workflow.py submit (cổng khóa ảnh + xác nhận + payload). Mỗi cú một thẻ, scene_number tăng toàn phim; reference_node_ids create-only.

Dùng cho bước 4 của SKILL.md.

## Ảnh có ảnh hưởng video/chuyển cảnh không? (hỏi quan trọng nhất)

- Ảnh **không tự động** đi vào video. Sinh 50 ảnh mà không gắn vào cảnh nào thì
  video không đổi một khung.
- Chỉ ảnh mà **cảnh đó trỏ tới** (`reference_node_ids`) được dùng, theo hai đường:
  - `first_frame` (mặc định): ảnh làm **khung đầu** cú máy — không cần thêm gì trên GPU.
  - `ref2v`: giữ **khuôn mặt** nhân vật xuyên nhiều cú — cần checkpoint `ref2va` tuỳ chọn (~21 GB).
- Chuyển cảnh chỉ là **cắt rồi nối** clip theo thứ tự; ảnh không làm hỏng chuyển cảnh.
- Mỗi cú máy dài cố định **5,167 giây** (124 khung, 24 hình/giây). Muốn phim dài thì
  chia nhiều cú, không xin một cú dài.

**Kết luận:** tạo nhân vật/sinh vật → bối cảnh → đạo cụ → storyboard từng cảnh →
sinh video từng cú ở chế độ khung đầu.

## Soạn brief JSON (ý tưởng → cảnh → cú)

Mẫu ở `examples/brief_mau.json` của dự án. Tối thiểu cần:

```json
{
  "title": "Tên phim",
  "idea": "Một câu tóm ý tưởng",
  "duration_seconds": 60,
  "aspect": "16:9",
  "characters": ["tên nhân vật", "..."],
  "scenes": [
    {"title": "Cảnh 1", "summary": "...", "shots": ["câu mô tả cú 1", "..."]}
  ],
  "project_id": "p-duy-nhat-cua-ban"
}
```

Số cú cần = thời lượng ÷ 5,17 giây. Brief 5 phút ≈ 58 cú; 20 phút ≈ 233 cú. Thiếu
câu mô tả cú thì máy dùng câu mẫu theo vòng (không bịa tình tiết mới).

## Dựng bảng vẽ và thẻ cảnh

Qua cổng MCP `POST /api/v1`... không — cổng MCP là `POST http://127.0.0.1:8001/mcp`
(JSON-RPC 2.0, 47 công cụ). Thứ tự làm phim qua cổng:

| # | Lệnh | Việc |
| --- | --- | --- |
| 1 | `canvas_list` → `canvas_create` | tìm bảng cũ hoặc mở bảng mới |
| 2 | `canvas_state_get` | xem bảng đang có thẻ gì |
| 3 | `skill_get story.plan` | đọc cách chia hồi → cảnh → cú |
| 4 | `canvas_node_create_scene` | mỗi cú một thẻ cảnh (mỗi lần một `command_id` mới) |
| 5 | `workflow.py submit` → `workflow.py refresh` | gửi lệnh sinh rồi hỏi tới khi xong |
| 6 | `timeline_append` → `workflow.py export` | ghép clip rồi xuất phim |

15 kỹ năng của dự án (đọc bằng `skill_get <id>`): `canvas.bootstrap`, `story.plan`,
`shot.generate`, `timeline.assemble`, `image.make`, `audio.speak`, `asset.lock`,
`film.longform`, `video.replicate`, `ecommerce.product`, `social.vertical`,
`research.web`, `shot.repair`, `board.cleanup`, `deliver.review`.

Luật khi gọi lệnh qua MCP:
- **Mỗi lần hỏi trạng thái phải đổi `command_id`** (không thì máy trả lại câu cũ).
- Lệnh tốn credit (`generation_submit`, `image.*`, `audio.*`, `timeline_export`):
  hỏi người dùng trước.
- Mọi lệnh đi qua sáu cổng như giao diện; không lách được quy tắc.


## Cấm chạy tắt

Dùng scripts/workflow.py theo SKILL.md. Không dùng film_run để chạy phim: bộ tự điền có thể chọn đầu vào không đúng storyboard và tự rơi về text_to_video. Cổng mới kiểm ảnh và ánh xạ từng cú trước khi nộp.
