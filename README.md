# B-roll Finder — Tool tìm & tải B-roll tự động

Nhận danh sách từ khóa B-roll (ví dụ bảng từ khóa mà skill `tinviet` xuất ra ở Bước 6),
tự động search và tải ảnh/video liên quan từ **Pexels** và **Pixabay** (API chính thức, miễn phí),
đồng thời tạo sẵn **link tìm Google Hình ảnh** cho từng từ khóa để tự chọn ảnh tư liệu thật (báo chí,
sự kiện cụ thể) mà 2 kho stock trên không có.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Lấy API key (miễn phí)

- Pexels: https://www.pexels.com/api/ → đăng ký, lấy API key.
- Pixabay: https://pixabay.com/api/docs/ → đăng ký, lấy API key.

Copy `.env.example` thành `.env` rồi điền key (hoặc export biến môi trường trực tiếp):

```bash
cp .env.example .env
# sửa .env:
# PEXELS_API_KEY=xxxxx
# PIXABAY_API_KEY=xxxxx
```

## Input hỗ trợ (tự động nhận diện)

1. **Bảng markdown từ skill `tinviet`** (Bước 6 — Gợi ý từ khóa B-roll theo khối):
   ```
   | Khối | Nội dung khối (tóm tắt) | Từ khóa VN (...) | Loại tư liệu gợi ý |
   |------|--------------------------|-------------------|-----------------------|
   | 1    | Hook mở đầu              | họp báo, lừa đảo  | stock footage         |
   ```
   Cột "Loại tư liệu gợi ý" được dùng để quyết định tìm video hay ảnh cho từng khối
   (chứa "video"/"footage" → tìm video; "photo"/"ảnh" → tìm ảnh; không rõ → tìm cả hai).

2. **Heading + bullet**:
   ```
   ## Khối 1: Hook mở đầu
   - họp báo doanh nhân
   - lừa đảo
   ```

3. **JSON**: `[{"block": 1, "title": "Hook", "keywords": ["kw1", "kw2"], "media_type": "video"}]`

4. **Danh sách phẳng**: mỗi dòng một từ khóa, không chia khối.

## Chạy

```bash
python -m broll_finder.cli --input keywords.md --output-dir ./broll_output
```

Chỉ tìm kiếm, chưa tải (kiểm tra xem có ra kết quả không):

```bash
python -m broll_finder.cli --input keywords.md --dry-run -v
```

### Các tùy chọn chính

| Flag | Mặc định | Ý nghĩa |
|------|----------|---------|
| `--source` | `both` | `pexels`, `pixabay`, hoặc `both` |
| `--media-type` | theo gợi ý input | Ép `video`/`photo`/`both`, bỏ qua gợi ý trong input |
| `--per-keyword` | `2` | Số file tải về cho mỗi (từ khóa × loại tư liệu) |
| `--orientation` | `landscape` | `landscape` (16:9, phù hợp YouTube), `portrait`, `square`, `any` |
| `--max-keywords-per-block` | không giới hạn | Giới hạn số từ khóa xử lý mỗi khối (tiết kiệm quota API) |
| `--dry-run` | tắt | Chỉ tìm + ghi manifest, không tải file |
| `--no-google-links` | tắt (tức mặc định có tạo) | Bỏ qua việc tạo file `google_links.md` |

## Output

```
broll_output/
  google_links.md          # link Google Hình ảnh cho từng từ khóa — tự bấm, tự chọn, tự kiểm tra bản quyền
  block_01_hook_mo_dau/
    hop_bao_doanh_nhan/
      pexels_video_123456_1.mp4
      pixabay_video_789_1.mp4
    credits.txt          # ghi công tác giả/nguồn cho từng file trong khối
  block_02_boi_canh/
    ...
  manifest.json           # toàn bộ kết quả tìm + tải (kèm link Google Hình ảnh mỗi từ khóa)
```

### Vì sao Google Hình ảnh chỉ ra link chứ không tự tải?

Google không có API miễn phí chính thức để tự động tải ảnh tùy ý cho việc tái sử dụng — khác với
Pexels/Pixabay (thư viện ảnh/video có giấy phép miễn phí rõ ràng), ảnh trên Google Hình ảnh thường
thuộc bản quyền của website gốc (báo chí, blog...). Với các khối cần ảnh tư liệu sự kiện thật (ví
dụ ảnh đúng địa điểm/vụ việc trong bản tin), tool tạo sẵn link tìm kiếm để bạn tự mở, tự chọn và tự
kiểm tra quyền sử dụng từng ảnh trước khi đưa vào video — tránh rủi ro vi phạm bản quyền khi tự động
tải hàng loạt.

## Lưu ý

- Từ khóa tiếng Việt vẫn search được trên cả 2 API, nhưng vì kho ảnh/video chủ yếu gắn tag
  tiếng Anh nên tỉ lệ ra kết quả đúng sẽ thấp hơn từ khóa tiếng Anh. Nếu một từ khóa không ra
  kết quả, thử đổi sang mô tả cảnh quay chung chung bằng tiếng Anh.
- Pexels/Pixabay đều miễn phí cho mục đích thương mại, không bắt buộc ghi công — nhưng file
  `credits.txt` vẫn được tạo tự động để tiện truy vết nguồn nếu cần.
- Cả hai API đều có rate limit (Pexels: 200 request/giờ trên gói free). Dùng `--sleep` để giãn
  cách nếu bị chặn 429, hoặc `--max-keywords-per-block` để giảm số lượng request mỗi lần chạy.
- Tool không tự dịch từ khóa hay tự động scrape ngoài 2 API trên — chỉ dùng API chính thức để
  tránh vi phạm điều khoản dịch vụ của các nền tảng ảnh/video khác.

## Test

```bash
python tests/test_parser.py
python tests/test_google_links.py
```

---

# Voice Clone — Clone giọng của chính bạn

Dùng Coqui XTTS v2 (chạy local, miễn phí, tiếng Việt qua checkpoint viXTTS, cộng đồng fine-tune từ XTTS v2) để đọc văn bản bằng giọng từ file mẫu của bạn.

```bash
pip install -r voice_clone/requirements.txt   # cần ffmpeg để tiền xử lý file mẫu
python -m voice_clone.cli --voice giong_cua_toi.wav --text-file kich_ban.txt --lang vi -o voice_output/out.wav
```

- File mẫu: 10–30 giây, giọng sạch, không nhạc nền/tiếng ồn, nói tự nhiên.
- Văn bản dài được tự chia theo câu rồi ghép lại; chỉnh `--pause`, `--speed`, `--temperature`.
- Có GPU (CUDA) sẽ nhanh hơn nhiều; CPU vẫn chạy được nhưng chậm.
- Chỉ clone giọng của chính bạn hoặc giọng bạn có quyền sử dụng.

## Google Colab (GPU)

Mở `voice_clone/voice_clone_colab.ipynb` trên Colab, chọn Runtime T4 GPU, chạy lần lượt các ô. Chạy lại được khi bị ngắt: đoạn đã đọc xong lưu trong `voice_output/*.chunks`.
