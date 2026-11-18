---
name: auto-htgroup
description: "Bắt buộc nạp skill khi operator gọi /auto-htgroup, auto htgroup, chạy phim tự động, làm phim tự động, auto làm phim hoặc yêu cầu tiếp tục một phiên HT-Group. Điều phối phim trong dự án HT-Group (công cụ tự tìm chỗ dự án; máy chưa có thì skill dừng hỏi cách lấy) qua checkpoint tuần tự: bài học, máy chủ 8001/giao diện 3001, 5 câu phỏng vấn, kịch bản và kế hoạch từng cú, ảnh tài sản ChatGPT, thẻ cảnh có dây tham chiếu, storyboard Gemini, cổng ảnh thực, xin phép GPU thuê, sinh video, kiểm từng cú, ghép/xuất tệp phim, ghi bài học. Không dùng lệnh chạy tắt hoặc biến câu trả lời thành báo cáo suông; thực hiện bằng công cụ."
compatibility: "Python 3.10+, ffprobe, curl; dự án HT-Group do công cụ tự tìm; máy chủ dữ liệu 8001, giao diện 3001; GPU 8188/Modal chỉ sau phê duyệt."
---

# /auto-htgroup — ĐIỀU PHỐI PHIM CÓ CHECKPOINT

## 1. Hợp đồng vận hành

Khi kích hoạt, thao tác thật trên dự án; không chỉ trả lời hướng dẫn. Dùng tiếng Việt, mỗi bước một dòng, ghi rõ **đã kiểm chứng** (lệnh + kết quả thật), **suy luận**, **chưa kiểm chứng**. Không chạy phim thật nếu operator đang yêu cầu đọc/sửa/test skill.

- Một phim = một run ID = một canvas_id = một bản brief/manifest. Không tạo canvas mới khi tiếp tục. Không dùng file trạng thái của phim khác.
- Sổ trạng thái trên đĩa là nguồn sự thật; không dùng lịch sử chat hoặc tự tick checklist để suy ra đã xong. Đọc trạng thái đầu mỗi lượt. Không tự sửa state.json, không nhảy checkpoint, không đánh dấu done bằng chữ.
- Chỉ dùng cổng 8001, 3001, 8188 của dự án. Tuyệt đối không dùng 8000. Không đọc/in/tìm API key, .env hoặc media_providers.json; không ghi khóa/URL có chữ ký vào báo cáo.
- Chỉ đọc tệp tham chiếu của bước hiện tại. Nếu tham chiếu cũ mâu thuẫn, thứ tự và cổng trong SKILL.md + references/00-checkpoint.md thắng.
- Chỉ có 5 câu phỏng vấn, mỗi lượt một câu; không hỏi lại dữ kiện đã có. Ngoài phỏng vấn, chỉ hỏi bắt buộc trước chi phí GPU (và bất kỳ chi phí/credit nào chưa được operator cho phép).
- Mọi lỗi, mã thoát khác 0, thiếu dữ liệu, queued/running hoặc không có công cụ → giữ nguyên checkpoint; sửa đúng phần lỗi rồi đo lại. Không chuyển bước vì hết thời gian, hết ngữ cảnh hoặc operator nói "tiếp đi".
- Không dùng film_run, first_shot.py hoặc gọi thẳng generation_submit để chạy video của phim: chúng có thể tạo bảng khác, chọn ảnh sai hoặc rơi về text_to_video. Chỉ nộp qua workflow.py submit.
- Không dùng dry-run, phản hồi giả, hoặc selftest để thay thế bằng chứng từ canvas thật. Không chạy GPU thử khi chưa có đồng ý. Không tự mua thêm credit.
- **Chỉ đọc skill này. Không đọc mã sản phẩm.** Nguồn duy nhất: repo GitHub `teamak1-sys/auto-htgroup-skill` (bản cài trên máy là bản sao của repo). Không mở, không grep, không "đọc cho hiểu" phần mã sản phẩm, phần giao diện, phần lệnh hay phần kiểm của dự án. Điều khiển dự án **chỉ** bằng lệnh trong references. Mã sản phẩm đang khoá: đọc lén rồi sửa là vi phạm; thấy lỗi thì báo chủ dự án, không tự sửa.
- Cần biết hệ thống làm gì thì đọc skill và gọi lệnh; **không suy ra từ mã nguồn**. Thiếu thông tin trong skill → hỏi một câu, không đi lục mã.

## 2. Dự án — công cụ tự tìm, không tự dạo

Skill không giả định chỗ đặt nào trên máy. Chỗ dự án để công cụ tự dò; chỉ khi máy có nhiều dự án mới cần người dùng chỉ.

- Không thấy dự án: **dừng**, không tự tạo chỗ rỗng. Hỏi đúng một câu: «Máy này chưa thấy dự án HT-Group. Bạn muốn (a) tôi kéo từ repo về chỗ mặc định, hay (b) bạn chỉ tôi chỗ dự án đã copy sẵn?» Có câu trả lời thì đặt biến `HT_PROJECT_ROOT` trỏ đúng chỗ đó rồi chạy lại.
- Kéo từ repo: `git clone https://github.com/teamak1-sys/TAN-CONG-TOP-VIEW.git`. Repo **riêng**: cần đăng nhập GitHub trước, chỉ người dùng tự đăng nhập; không xin họ dán token vào chat, không đoán chỗ.
- Không tự dạo đĩa để đoán chỗ đặt dự án. Công cụ tự báo lỗi kèm cách chỉ chỗ.

Bản cài skill **là bản sao repo riêng** `teamak1-sys/auto-htgroup-skill`.

- Địa chỉ gói: `https://github.com/teamak1-sys/auto-htgroup-skill.git` (repo **riêng**).
- Máy mới: `git clone https://github.com/teamak1-sys/auto-htgroup-skill.git "<chỗ bộ nạp kỹ năng đọc>"`. Repo riêng nên máy đó phải đăng nhập GitHub trước (hoặc nhận tệp nén của gói, không cần mạng). Không xin người dùng dán token vào chat.
- Cập nhật: `git -C "<chỗ gói kỹ năng>" pull --ff-only`.
- Máy lạc hậu bản: thiếu lệnh hoặc sai cú pháp thì hỏi chủ dự án cho cập nhật, không tự chắp vá.
- Sửa skill thì sửa trong repo rồi commit/push, không mỗi máy một kiểu.

Đọc references/00-checkpoint.md để biết cách dùng sổ trạng thái, định dạng manifest, payload và các lệnh. Gọi công cụ của gói kỹ năng (chỗ gói do bộ nạp cấp, ký hiệu `$SKILL`):

```bash
python3 "$SKILL/scripts/workflow.py" init --run "$RUN"
python3 "$SKILL/scripts/workflow.py" status --run "$RUN"
```

`workflow.py` tự dò chỗ dự án; không thấy thì báo lỗi kèm cách chỉ. Chọn RUN duy nhất khi bắt đầu phim mới; giữ RUN trong mọi lượt (ghi lại trong câu trả lời). Nếu tiếp tục, tìm đúng run của phim qua chính công cụ (`status`), không init lại, không tự chọn giữa nhiều run khi chưa xác định được phim. Các lệnh dưới dùng W = `python3 "$SKILL/scripts/workflow.py"`, chạy thêm `--run "$RUN"`. Mỗi bước đọc status, thực hiện công việc, chạy lệnh chuyển bước; chỉ tiếp tục khi mã thoát 0 và CHECKPOINT đúng.

### Máy Windows

- Chép nguyên gói kỹ năng sang chỗ bộ nạp kỹ năng đọc trên Windows (cùng cách bố trí như máy Mac).
- Đặt biến môi trường bằng PowerShell, **không dùng `export`**:
  ```powershell
  $env:HT_PROJECT_ROOT = "<chỗ dự án>"   # cho cửa sổ hiện tại
  setx HT_PROJECT_ROOT "<chỗ dự án>"     # giữ lâu, mở cửa sổ mới mới thấy
  ```
- `workflow.py` và `kiem-anh.py` chạy được bằng Python trên Windows (chỉ thư viện chuẩn + HTTP), miễn `HT_PROJECT_ROOT` đúng.
- Mở cổng trên Windows theo tài liệu Windows của dự án (mục 3–6): máy chủ dữ liệu 8001 và giao diện 3001, bằng PowerShell; **không** dùng lệnh của máy Mac.
- Máy Windows chưa cài: làm đúng mục 3 tài liệu đó (Python 3.11, ffmpeg, kéo dự án, tạo môi trường Python, cài gói phụ thuộc, đặt biến ffmpeg/ffprobe) rồi mới chạy skill. Tài liệu Windows **chưa chạy thử trên máy Windows thật** — nói rõ mức đó khi báo cáo.

### Máy KHÔNG có dự án — vẫn điều khiển được

Máy khác chỉ cần **mạng tới máy chủ dữ liệu**, không cần bản sao dự án:

```bash
export HT_BACKEND_URL="http://<máy-chạy-dự-án>:8001"   # bắt buộc khi khác máy
export HT_GUI_URL="http://<máy-chạy-dự-án>:3001"       # tuỳ chọn, để kiểm giao diện
export HT_REMOTE=1                                      # tự bật khi máy không có mã dự án
```

- Công cụ tự bật chế độ này khi không thấy dự án: sổ chạy để cạnh gói kỹ năng (đổi bằng `HT_RUNS_DIR`), **không** đụng đĩa của dự án.
- Đọc/ghi bảng vẽ, nộp cú, xuất phim đều qua máy chủ; ảnh và clip tải về tạm để đo, không cần kho media trên máy này.
- Máy này cần: Python 3.10+, `ffprobe` để đo clip, và quyền vào cổng 8001. Không cần GPU, không cần ComfyUI.
- Kịch bản, brief, manifest do agent viết ngay trên máy này (trong sổ chạy); máy chủ chỉ nhận lệnh và giữ dữ liệu phim.
- Đích giao phim: bất kỳ chỗ nào ghi được (không bắt buộc Downloads); vẫn phải là `.mp4` mới.

## 3. Luồng bắt buộc — không đảo thứ tự

Bước 0 luôn là mục 2: để công cụ xác định chỗ dự án; chưa có dự án thì dừng hỏi cách lấy, không chạy tiếp.

| Checkpoint hiện tại | Hành động thực tế | Cổng chuyển bước |
|---|---|---|
| lessons | đọc references/BAI-HOC.md, áp dụng lỗi đã có | advance --value "đã đọc; ... " |
| health | kiểm dự án + mở đúng backend, GUI nếu cần | advance (kiểm HTTP thật) |
| interview | 5 câu lần lượt, ghi ngay từng câu | answer --field ... --value ... |
| plan | viết brief, script, manifest đầy đủ cảnh/cú/tài sản | advance |
| assets | tạo một canvas; tạo đúng thẻ; ChatGPT sinh và gắn ảnh tài sản | advance (kiểm node + tệp ảnh thật) |
| scenes | tạo thẻ từng cú, nối đúng tài sản bằng reference_node_ids ngay lúc tạo | advance (kiểm đủ ID, thứ tự, dây) |
| storyboards | Gemini ưu tiên; tạo/gắn storyboard từng cú; kiểm tất cả | advance (đủ ảnh thật + snapshot) |
| approval | hỏi operator và dừng; không bật GPU | approve --value "có" chỉ sau lời đồng ý thật |
| video | preflight → bật GPU → submit/refresh theo từng cú | advance (tất cả clip có hình + tiếng thật) |
| export | ghép timeline chính xác, export, finish | finish (download thật + ffprobe) |
| lessons_end | ghi lỗi mới vào BAI-HOC.md hoặc xác nhận không lỗi | advance --value "..." |
| done | giao tệp phim và số đo | status |

### lessons / health
Mở references/BAI-HOC.md. Dùng W advance để ghi checkpoint. Kiểm dự án và hai cổng: máy chủ dữ liệu 8001 (có `/health`), giao diện 3001. Cổng thiếu thì mở bằng lệnh khởi động của dự án (tài liệu vận hành của dự án ghi lệnh mở máy chủ và giao diện); dùng trình quản lý tiến trình phù hợp để không chặn phiên. Kiểm lại `/health` và HTTP 3001 bằng W advance. Nếu thiếu dự án hoặc lỗi mở cổng, báo CHẶN.

### interview
Mở references/01-thu-thap-anh.md mục Phỏng vấn. Hỏi đúng chủ đề → tên phim → thời lượng (tối thiểu 3 phút) → ngôn ngữ → dàn nhân vật. Dùng W answer cho từng field theme, title, duration_minutes, language, characters. characters lưu mảng JSON tên nhân vật đã chọn (không tự bỏ nhân vật); mô tả chi tiết đưa vào kịch bản/manifest. Nếu operator đã cung cấp một mục rõ ràng, ghi mục đó đúng thứ tự, không hỏi lại. Khi thiếu dữ kiện, dừng ở đúng câu hỏi tiếp theo. Đủ 5 câu mới tự chuyển plan.

### plan
Mở references/02-kich-ban.md phần brief. Soạn kịch bản tự sự hoàn chỉnh, thoại đúng ngôn ngữ, mô tả từng cú, âm thanh, logic nối cảnh, hành động đầu/cuối; không dùng /scripts/generate kiểu quảng cáo. Ghi brief.json, script.md, manifest.json theo references/00-checkpoint.md. Số cú tối thiểu ceil(thời lượng giây / (124/24)); viết đủ cú thật, không lặp câu mẫu hoặc dùng --max-shots để rút phim. Liệt kê tài sản phim thực sự dùng và tài sản xuất hiện theo từng cú, kể cả sinh vật/quái vật. Một cảnh lớn nhiều cú → mỗi cú có một thẻ cảnh, một storyboard riêng. W advance rồi mới lập canvas.

### assets
Mở references/01-thu-thap-anh.md mục Sinh ảnh. Tạo đúng canvas của run bằng MCP; ghi canvas_id vào manifest. Tạo thẻ nhân vật/sinh vật trước, sau đó bối cảnh, đạo cụ, phong cách nếu thực sự có. Tạo ảnh gốc qua autofill scope=assets, từng lô tối đa 12, đọc generated/skipped/failed. Ảnh **đầu tiên** của thẻ nhân vật là **bảng tham chiếu nhân vật gốc** (16:9: một chân dung lớn bên trái + ba hình thân không đầu bên phải), sinh đúng một lần rồi khoá, không sinh lại mỗi cú. Mỗi ảnh phải gắn trực tiếp vào đúng thẻ tài sản; ảnh rời trong kho không được tính. Ghi node_id vào manifest. Nếu operator đã đưa ảnh gốc, dùng và kiểm tệp thật thay vì sinh lại. Không tạo thẻ vô nghĩa để đủ nhóm. W advance chỉ qua khi tất cả thẻ có ảnh thật.

### scenes
Mở references/02-kich-ban.md mục Dựng bảng vẽ. Dùng canvas_node_create_scene cho từng cú đúng thứ tự manifest, scene_number = số thứ tự toàn phim từ 1. Điền scene_summary, scene_text, duration, aspect, vị trí. reference_node_ids là danh sách node_id tài sản của cú và là create-only: phải điền ngay khi tạo, không trông chờ tự nối sau. Ghi node_id từng cú vào manifest ngay. Kiểm dây và đặt ảnh gốc trên đầu bảng, các cảnh/storyboard theo thứ tự, nhóm hợp lý; không thay bố cục nếu không cần. W advance đối chiếu toàn bộ node thật; thiếu hoặc trùng cú/dây thì sửa đúng thẻ rồi kiểm lại.

### storyboards
Mở references/01-thu-thap-anh.md phần ảnh. POST /api/v1/images/autofill với scope=storyboards, limit<=12, ưu tiên Gemini, từng lô cho đến đủ. Không chỉ tạo một lô 12 rồi báo xong. Có tài sản tham chiếu thì ảnh phải dùng ảnh gốc của chính cú; không biến ảnh thành bảng nhiều ô có chữ. Kiểm generated/skipped/failed và ảnh gắn trên từng thẻ cảnh. Từng cú có đúng storyboard 1 khung đầy đủ, nhân vật **có đầu, mặt, tóc** đầy đủ; tuyệt đối không dùng mẫu bảng tham chiếu không đầu cho storyboard hay khung video. Sửa ảnh sai mặt/trang phục/bối cảnh/hành động. Không dùng GPU để sinh storyboard.

Chạy cổng cũ **và** cổng mới:
```bash
python3 "$SKILL/scripts/kiem-anh.py" --canvas-id "$CANVAS" --brief "$DIR/brief.json"
python3 "$SKILL/scripts/workflow.py" advance --run "$RUN"
```
Cả hai phải mã 0. Cổng mới còn kiểm số cú, ảnh thực đọc được, mapping, dây và dấu vân tay ảnh. Nếu chặn, báo chính xác mục thiếu; bổ sung, dùng rewind khi cần rồi kiểm lại. Không hỏi GPU khi chưa có CHECKPOINT=approval và dòng ĐỦ ẢNH. Không bắt phim có đủ loại tài sản nếu phim không dùng.

### approval — điểm dừng cứng
Sau đủ ảnh, kết thúc lượt bằng đúng câu hỏi:
> Đã xong ý tưởng, kịch bản, ảnh tài sản, storyboard và cổng kiểm ảnh. Tôi có bật máy GPU thuê (sevo ảo) để sinh video không? (Có tốn tiền theo giờ.)

Nếu không, giữ approval, dừng an toàn. "Tiếp đi", "ok" mơ hồ hoặc lời đồng ý trước khi qua cổng không phải phê duyệt GPU. Chỉ ghi W approve --value "có" khi operator trả lời có/đồng ý bật GPU rõ ràng ở lượt sau. Sau đó W preflight; nếu brief/ảnh/bảng đổi, không bật và xin phép lại sau khi kiểm lại.

### video
Chỉ ở checkpoint video. Mở references/03-chay-gpu-xuat.md phần GPU. W preflight thành công rồi mới deploy/kiểm /system_stats. Lấy capability thật qua generation_capabilities. Chọn image_to_video, role=start_frame, source.kind=canvas_node + node_id của storyboard chính cú. ref2v chỉ khi checkpoint ref2va có sẵn và capability cho phép; dùng reference_image, có ảnh storyboard chính cú. Không gửi inputs rỗng, không dùng asset đầu tiên làm ảnh đầu cho mọi cú. Đừng dùng film_run có fallback text_to_video.

Làm đúng thứ tự manifest. Cú đầu tiên dùng chính cú 1.1 của phim để kiểm đầu ra, không tạo clip thử ngoài phim. Tạo payload theo schema trong references/00-checkpoint.md rồi W submit --shot ID --payload file.json. Mỗi lần poll W refresh --shot ID; queued/running chỉ là đang chạy. Khi success phải có media_ref, file và ffprobe hình + tiếng; chỉ lúc đó mới sang cú kế tiếp. Mã refresh tự đổi; retry nộp dùng mã cũ nếu chưa rõ kết quả. Nếu fail, đọc nguyên nhân, sửa đúng cú qua W repair rồi submit lại tối đa một lần; không xóa state. Nếu chưa xử lý được thì CHẶN, không ghép thiếu. Đối chiếu từng clip với prompt và storyboard, kiểm nội dung/nhân vật/chuyển cảnh, ghi kết quả; ffprobe không thay kiểm hình. W advance chỉ qua khi đủ toàn bộ cú.

### export
Mở references/03-chay-gpu-xuat.md mục Xuất phim. Dùng timeline_get, timeline_append theo etag và thứ tự manifest; tối đa 50 op/lô, duration_ms theo clip thật (~5167), start_ms nối liên tục. Không đưa thẻ ảnh/âm thanh độc lập vào track video. Kiểm cắt/ghép, thoại/tiếng, không thiếu hoặc lặp cú. W export kiểm thứ tự và tệp nguồn rồi xuất đúng thời lượng brief. W finish --file "<chỗ bàn giao>/<ten-phim>.mp4" poll task xuất, tải chính file kết quả; nếu còn running thì giữ export, hỏi lại thân task, không xuất lại. Không nhập đường dẫn giả hoặc một phim có sẵn.

### lessons_end / done
Đọc lại BAI-HOC.md, thêm một dòng cho mỗi lỗi mới (hiện tượng → nguyên nhân → cách tránh), không lặp lỗi cũ, tuyệt đối không ghi bí mật. W advance --value "đã ghi lỗi..." hoặc "không có lỗi mới". Nếu phiên dừng vì lỗi ở bước trước, ghi bài học ngay trước khi kết thúc lượt nhưng không đánh dấu done. Chỉ báo phim hoàn tất ở CHECKPOINT=done. Báo đường dẫn, số giây, số byte theo state.delivery; nếu chưa kiểm nội dung thì nói chưa kiểm, không gọi phim chuẩn.

## 4. Liền mạch giữa các cú — luật bắt buộc (không có cổng tự kiểm)

Phim rời rạc là do bỏ mục này, không phải do máy sinh kém. Bốn luật, áp dụng ngay từ brief:

1. **Khoá hình:** mỗi cú ghi rõ trục máy, ống kính, hướng nhìn, trạng thái đồ của nhân vật. Hai cú liền nhau cùng bối cảnh thì giữ nguyên trục và ánh sáng; đổi trục phải vì kịch bản, không đổi ngẫu nhiên.
2. **Nối hành động:** khung cuối cú trước phải khớp khung đầu cú sau. Mẫu H3 hiện tại chỉ nhận `first_frame` (không có `end_frame`), nên muốn nối thật thì trích khung cuối clip trước bằng ffmpeg, đưa lên kho, dùng làm `start_frame` cho cú sau — hoặc vẽ storyboard cú sau đúng trạng thái cuối cú trước. Ghi rõ dùng cách nào.
3. **Storyboard là một khung, không phải bảng:** mỗi cú một ảnh đầy đủ, không chữ, không viền, không ô chú thích; ảnh phải cùng nhân vật, cùng phục trang, cùng bối cảnh với ảnh tài sản.
4. **Nói thật về ghép:** xuất phim nối cứng từng clip bằng ffmpeg, **không có chuyển cảnh mềm, không có nhạc nền, không nối tiếng giữa các cú** trừ khi làm thêm bằng tay và phải nói rõ đã làm. Không được mô tả phim là liền mạch nếu chỉ nối cứng 36 clip rời.

Kiểm bằng mắt trước khi xuất: mở ba cú liền nhau, xem mặt/áo/phố/ánh sáng có nhảy không. Nhảy thì sửa storyboard rồi sinh lại cú đó, không xuất bừa.

## 5. Kiểm thử khi sửa skill (không tốn GPU)

python3 scripts/workflow.py selftest
python3 scripts/kiem-anh.py --selftest

Selftest chỉ kiểm logic, không thay bằng chứng chạy thật. Xem references/00-checkpoint.md để tạo ca thiếu cảnh, thiếu ảnh, sai dây, sai payload và kiểm dừng ở đúng bước.
