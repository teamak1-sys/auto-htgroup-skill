# Sổ chạy HT-Group — hướng dẫn dùng checkpoint

Đọc khi bắt đầu hoặc tiếp tục run. Không phải tài liệu thay thế SKILL.md.
Mọi lệnh chạy trên máy điều khiển (không phải server GPU). Chỗ dự án để công cụ tự dò; chỉ đặt biến `HT_PROJECT_ROOT` khi máy có nhiều dự án. Dùng Python 3.10+.

## 1. Thiết lập biến mỗi lượt

```bash
SKILL="<chỗ gói kỹ năng>"            # do bộ nạp kỹ năng cấp
RUN="<ma-run-da-chon>"
W="$SKILL/scripts/workflow.py"
python3 "$W" status --run "$RUN"     # công cụ tự dò chỗ dự án và chỗ sổ chạy
```
Không thấy dự án: công cụ báo lỗi kèm cách chỉ; đặt `HT_PROJECT_ROOT` rồi chạy lại. Không tự dạo đĩa, không tự tạo chỗ rỗng. Sổ chạy của run do công cụ giữ; không tự mở, không tự sửa.
Nếu là phim mới: `python3 "$W" init --run "$RUN"`. Nếu tiếp tục, không init.
state.json được script ghi nguyên tử. Không tạo/sửa bằng tay, không xóa để đi tắt.
Ghi mã run sau mỗi lượt để lần sau không mất tiến độ.
Chỉ một tiến trình thao tác trên cùng run; không chạy submit đồng thời.
`advance --run "$RUN"` chỉ chuyển bước hiện tại đến bước kế tiếp khi điều kiện đạt.
Nếu cần sửa ảnh/bảng trước khi có task video: `rewind --run "$RUN" --value "lý do"`.
Rewind trở về assets, xóa sự đồng ý GPU; không dùng khi đã có task video.

## 2. Phỏng vấn và lưu từng đáp án

```bash
python3 "$W" advance --run "$RUN" --value "đã đọc BAI-HOC.md; áp dụng các lỗi..."
python3 "$W" advance --run "$RUN" # kiểm health
python3 "$W" answer --run "$RUN" --field theme --value "..."
python3 "$W" answer --run "$RUN" --field title --value "..."
python3 "$W" answer --run "$RUN" --field duration_minutes --value "3"
python3 "$W" answer --run "$RUN" --field language --value "Tiếng Anh–Mỹ"
python3 "$W" answer --run "$RUN" --field characters --value '["Lena","Milo"]'
```
Đây là minh họa năm lượt, không tự nộp các giá trị ví dụ. Trường characters giữ tên đúng của phương án đã chọn; ghi mô tả chi tiết ở phần kịch bản. Có thể là [] chỉ khi operator thực sự chọn phim không nhân vật.
Không hỏi lại câu đã có dữ liệu; script chỉ nhận đúng mục tiếp theo.

## 3. Ba tệp kế hoạch

Lưu trong DIR trước checkpoint plan. Dưới đây là mẫu cấu trúc tối giản, KHÔNG đủ cú cho phim 3 phút. Phim thật phải viết đủ cú khác nhau (3 phút cần ít nhất 35 cú H3 124/24 giây).

brief.json:
```json
{
  "title":"Tên phim đã chốt",
  "idea":"Ý tưởng đúng chủ đề đã chốt",
  "duration_seconds":180,
  "language":"Tiếng Anh–Mỹ",
  "aspect":"16:9",
  "characters":["Lena","Milo"],
  "project_id":"ma-project-co-that",
  "scenes":[
    {"title":"Cảnh 1","summary":"Hai nhân vật đến phòng thí nghiệm","shots":["Cú 1: toàn cảnh lối vào","Cú 2: cận cảnh Lena nhìn Milo"]}
  ]
}
```

script.md: kịch bản đầy đủ theo từng hồi/cảnh/cú: nội dung, hành động, điểm bắt đầu/kết thúc, lời thoại đúng ngôn ngữ, âm thanh, liên tục nhân vật và bối cảnh. Không lấy prompt mẫu lặp vòng. Xem lại mỗi chuyển cảnh; nếu cần nối động tác, mô tả khung đầu/kết thúc của hai cú liền nhau.

manifest.json:
```json
{
  "canvas_id":"",
  "assets":[
    {"name":"Lena","kind":"character","node_id":""},
    {"name":"Milo","kind":"character","node_id":""},
    {"name":"Phòng thí nghiệm","kind":"environment","node_id":""}
  ],
  "shots":[
    {"id":"1.1","assets":["Lena","Milo","Phòng thí nghiệm"],"node_id":""},
    {"id":"1.2","assets":["Lena","Milo","Phòng thí nghiệm"],"node_id":""}
  ]
}
```
Tên tài sản phải duy nhất và khớp tiêu đề thẻ (có thể có phần mô tả sau dấu gạch dài cách khoảng trắng). 1.1 = cảnh 1 cú 1; 1.2 = cảnh 1 cú 2. Tất cả ID đúng thứ tự brief. Không tự invent mã node. Khi ở assets: tạo canvas, gán canvas_id, ghi node_id của từng tài sản. Khi ở scenes: gán node_id của từng thẻ cảnh. Không khai ID giả. Mỗi lần tạo thành công phải cập nhật manifest ngay để dễ tiếp tục; đối chiếu canvas trước khi tạo lại.

## 4. Kiểm ảnh, nối dây

Dùng MCP tools/list để lấy schema thật: canvas_list, canvas_create, canvas_state_get, canvas_node_create_asset, canvas_node_create_scene, canvas_node_details. Cảnh trỏ đúng tài sản qua reference_node_ids (create-only, không thể patch); scene_number là số thứ tự toàn phim 1,2,3... (khác ID 1.1,1.2,2.1 dùng trong manifest). Mỗi cú có thẻ cảnh riêng, không chỉ thẻ cảnh lớn. Gắn ảnh vào chính node bằng autofill. Không tạo ảnh rời rồi tính đã đủ.

Mỗi lô ảnh dùng POST http://127.0.0.1:8001/api/v1/images/autofill (scope assets hoặc storyboards, limit 12, node_ids nếu cần sửa, overwrite=true chỉ khi thực sự thay ảnh). Cặp tài sản trước, storyboard sau. Đọc kết quả generated/failed/skipped; nếu failed không nộp video. Đến hết danh sách, kiểm lại ảnh; script kiểm media_ref/storyboard_media_ref, object_key và tệp trong kho media của dự án bằng ffprobe. Kho media do máy chủ khai; khác chỗ mặc định thì đặt biến `HT_STORAGE_DIR` trỏ đúng kho (không mở tệp cấu hình bí mật). Không tạo file giả trong kho để qua cổng.

```bash
python3 "$SKILL/scripts/kiem-anh.py" --canvas-id "$CANVAS" --brief "$DIR/brief.json"
python3 "$W" advance --run "$RUN" # chỉ khi cổng trên thành công
```
Mã 0, dòng ĐỦ ẢNH và CHECKPOINT=approval mới được hỏi GPU. Không lấy selftest làm bằng chứng thật.

## 5. Sau lời đồng ý GPU

```bash
python3 "$W" approve --run "$RUN" --value "có"
python3 "$W" preflight --run "$RUN"
```
Chỉ chạy approve sau phản hồi thật, không tự tạo câu trả lời. Nếu bị chặn, đọc lỗi. Preflight kiểm lại snapshot và ảnh. Khi trước đó chưa có task, rewind nếu cần sửa ảnh; kiểm lại cả ba bước assets/scenes/storyboards và xin phép lại. Nếu có task cũ, không xóa lịch sử; dừng an toàn và báo cần đối chiếu thủ công.

Sau preflight, deploy GPU theo references/03-chay-gpu-xuat.md và kiểm system_stats. Lấy version/model/parameters thật bằng generation_capabilities của server. Không dùng phiên bản ví dụ. Nộp payload của từng cú (JSON dưới là mẫu, không chạy nguyên xi):

```json
{
  "canvas_id":"CANVAS_THAT",
  "scene_node_id":"NODE_STORYBOARD_CUA_CU",
  "capability_version":"VERSION_THAT",
  "media_type":"video",
  "task_type":"image_to_video",
  "model":"minimax_h3",
  "prompt":"Mô tả cú hoàn chỉnh từ kịch bản, gồm thoại và âm thanh",
  "parameters":{"resolution":480},
  "inputs":[{"role":"start_frame","source":{"kind":"canvas_node","node_id":"NODE_STORYBOARD_CUA_CU"}}]
}
```
Đọc schema và mode thật trước khi điền parameters, capability_version. Cổng nộp tự cấp command_id ổn định; không điền mã khác để lặp task. image_to_video chỉ có một start_frame; có thể thêm end_frame nếu dùng ảnh phù hợp trong tập asset của cú và capability hỗ trợ. ref2v cần model minimax_h3_ref, role reference_image và đúng checkpoint. Không đẩy ảnh asset nguyên mẫu thay storyboard, không gửi text_to_video. Các ảnh phải thuộc đúng manifest của cú.

```bash
python3 "$W" submit --run "$RUN" --shot 1.1 --payload "$DIR/payload-1.1.json"
python3 "$W" refresh --run "$RUN" --shot 1.1
```
Polling mỗi lần dùng mã mới. Không chuyển cú khi queued/running. Không nộp lần hai khi response mạng chưa rõ; kiểm status, retry payload y hệt để giữ command_id. Khi fail đã xác nhận, tối đa một lần sửa:
```bash
python3 "$W" repair --run "$RUN" --shot 1.1 --value "nguyên nhân và cách sửa"
# sửa payload theo lỗi rồi chạy submit của cùng cú
```
Khi tất cả clip thật đủ hình và tiếng: advance chuyển export.

## 6. Ghép và xuất

Lấy node_id trong state.tasks theo thứ tự manifest, đối chiếu object_key state.clips.
timeline_get để lấy etag; timeline_append tối đa 50 clip mỗi lô, lấy etag mới cho lô tiếp theo. Dùng duration_ms thực (5167 nếu đúng clip 124/24 giây); start_ms cumulative. Cổng export kiểm track hình đúng toàn bộ cú, đúng object_key, không hở/chồng, đủ thời lượng. Nếu cần thêm nhạc/thoại hoặc chỉnh track, làm trước khi export (không thay clip nguồn bằng tệp không xác minh). Cổng xuất giới hạn chính xác thời lượng đặt trong brief, không xuất cả phim ngắn hơn rồi gọi hoàn chỉnh.

```bash
python3 "$W" export --run "$RUN"
python3 "$W" finish --run "$RUN" --file "<chỗ bàn giao>/ten-phim.mp4"
```
finish chỉ tải output thật của task đã ghi; nếu queued/running gọi lại finish, không xuất lại. Không ghi đè tệp sẵn; chọn tên mới. Kiểm lại trong trình phát. Ghi bài học rồi advance để đến done.

## 7. Ca thử khi sửa

1. Operator yêu cầu chạy nhanh từ đầu, thiếu phỏng vấn: status phải interview, không tạo video.
2. Canvas chỉ có ảnh nhân vật, thiếu 1+ storyboard hoặc thiếu thẻ cảnh: gate phải chặn.
3. Mọi thẻ có ảnh nhưng sai dây reference_node_ids: gate phải chặn.
4. Ảnh đầy đủ nhưng chưa đồng ý GPU: preflight/submit bị chặn.
5. Sau đồng ý GPU, payload text_to_video hay sai storyboard: không nộp.
6. GPU trả queued hoặc clip thiếu tiếng: không chuyển export.
7. Phim đủ clip nhưng timeline sai thứ tự, thiếu clip: không xuất.
8. Xuất chưa thành công hoặc tệp thiếu hình/tiếng/thời lượng: không done.

Tự kiểm hai script không tạo task, không sinh ảnh, không bật GPU. Kiểm tích hợp thật chỉ khi được operator yêu cầu và có đủ điều kiện.
