# B-roll Finder — Tool tìm & tải B-roll tự động

Nhận danh sách từ khóa B-roll (ví dụ bảng từ khóa mà skill `tinviet` xuất ra ở Bước 6),
tự động search và tải ảnh/video liên quan từ **Pexels** và **Pixabay** (API chính thức, miễn phí).

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

## Output

```
broll_output/
  block_01_hook_mo_dau/
    hop_bao_doanh_nhan/
      pexels_video_123456_1.mp4
      pixabay_video_789_1.mp4
    credits.txt          # ghi công tác giả/nguồn cho từng file trong khối
  block_02_boi_canh/
    ...
  manifest.json           # toàn bộ kết quả tìm + tải, dùng để đối chiếu/dựng lại
```

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
```
