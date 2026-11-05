# PhimNgan CS3

Cổng cài đặt 8 addon phim ngắn cho CloudStream và các ứng dụng đọc repo CloudStream.

## Cài đặt

Mở **Extensions / Add repository** trong ứng dụng và nhập URL của `repo.json`:

`https://raw.githubusercontent.com/taigametaiwan/phimngan-cs3/main/repo.json`

Có thể tải riêng từng `.cs3` từ thư mục `addons/`.

## Addon

DramaBox, Gamo, NetShort, PhimNgan, PhimNganHDC, VietShort, YiniTV và AllShorts.

`repo.json` là điểm nhập repo; `plugins.json` chứa danh sách plugin và URL tải trực tiếp. Mỗi mục được tạo từ `manifest.json` nằm trong gói `.cs3`, cùng dung lượng và SHA-256 của chính file. Các gói là mã thực thi biên dịch sẵn; repo không bao gồm mã nguồn và chưa xác nhận khả năng phát trên từng ứng dụng.

## Thêm hoặc cập nhật addon

1. Đặt file mới hoặc bản cập nhật vào `addons/` với tên duy nhất, đuôi `.cs3`.
2. Commit và push lên nhánh `main`. GitHub Actions sẽ đọc manifest, kiểm tra gói và tự cập nhật `plugins.json`, `repo.json` nếu cần.
3. Chờ workflow **Update plugin catalog** chạy xong. Nếu muốn tạo metadata trước khi push, chạy `python scripts/generate_catalog.py --repository taigametaiwan/phimngan-cs3`.

Không sửa metadata bằng tay. File `.cs3` phải có `manifest.json` hợp lệ và `classes.dex`; phiên bản trong manifest cần tăng khi phát hành bản mới để ứng dụng nhận cập nhật.

Định dạng repo và plugin dựa trên [ví dụ CloudStream đang dùng](https://github.com/codegeasse1/codegeasse-cloudstream-repos/tree/builds).
