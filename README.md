# auto-htgroup — bộ kỹ năng điều phối phim HT-Group

Bộ này để **một AI khác điều phối việc làm phim** trong dự án HT-Group theo từng
checkpoint, thay vì đọc lung tung mã nguồn rồi sửa bậy.

Nguyên tắc: AI đọc **chỉ repo này** và ra lệnh cho dự án qua công cụ (MCP/HTTP).
Không đọc, không sửa mã sản phẩm.

## Cài

Máy Mac/Linux:

```bash
git clone https://github.com/teamak1-sys/auto-htgroup-skill.git "<chỗ bộ nạp kỹ năng đọc>"
```

Máy Windows (PowerShell):

```powershell
git clone https://github.com/teamak1-sys/auto-htgroup-skill.git "<chỗ bộ nạp kỹ năng đọc>"
```

Repo **công khai**: kéo được ngay, không cần đăng nhập. Muốn đẩy lên thì vẫn cần tài khoản có quyền.

Cập nhật: `git -C "<chỗ gói kỹ năng>" pull --ff-only`

## Trong này có gì

| Tệp | Việc |
|---|---|
| `SKILL.md` | hợp đồng vận hành, luồng 12 checkpoint, luật liền mạch giữa các cú |
| `references/00-checkpoint.md` | cách dùng sổ trạng thái, định dạng brief/manifest, payload |
| `references/01-thu-thap-anh.md` | phỏng vấn 5 câu, sinh ảnh tài sản và storyboard |
| `references/02-kich-ban.md` | viết kịch bản, chia cú, dựng thẻ cảnh trên bảng vẽ |
| `references/03-chay-gpu-xuat.md` | bật GPU, nộp từng cú, ghép và xuất phim |
| `references/BAI-HOC.md` | lỗi đã gặp và cách tránh |
| `scripts/workflow.py` | sổ trạng thái: init/status/advance/preflight/submit/export… |
| `scripts/kiem-anh.py` | cổng kiểm ảnh thật trước khi cho qua bước sinh video |
| `evals/` | ba ca thử cho AI (thiếu storyboard, clip kẹt queued, bỏ phỏng vấn) |

## Dùng ở máy không có dự án

Chỉ cần mạng tới máy chủ dữ liệu của dự án:

```bash
export HT_BACKEND_URL="http://<máy-chạy-dự-án>:8001"
export HT_GUI_URL="http://<máy-chạy-dự-án>:3001"   # tuỳ chọn
```

Công cụ tự nhận chế độ này (không thấy mã dự án). Sổ chạy để cạnh gói kỹ năng,
ảnh/clip tải về tạm để đo. Máy này cần Python 3.10+, `ffprobe`, không cần GPU,
không cần bản sao dự án.

## Kiểm sau khi sửa

```bash
python3 scripts/workflow.py selftest     # 15 bài
python3 scripts/kiem-anh.py --selftest   # 7 bài
```

## Không chứa

Không có mã sản phẩm, không có khoá API, không có dữ liệu phim, không có địa chỉ
máy GPU thật. Sổ trạng thái phim nằm trong dự án, do công cụ giữ,
không nằm trong repo này.
