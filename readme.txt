-------------------
1. Cài đặt virtualenv qua pip
Mở Terminal (trong VS Code hoặc CMD/PowerShell) và chạy lệnh sau để cài đặt virtualenv vào hệ thống Python toàn cục của bạn:

Windows:
pip install virtualenv

2. Kiểm tra cài đặt
Sau khi cài đặt xong, hãy kiểm tra xem nó đã sẵn sàng chưa bằng lệnh:

virtualenv --version
Nếu hiện ra số phiên bản (ví dụ: virtualenv 20.x.x) là bạn đã cài thành công.

3. Cách sử dụng virtualenv để tạo môi trường ảo
Cách dùng của nó hơi khác so với module venv mặc định một chút:

Tạo môi trường ảo: Thay vì dùng python -m venv, bạn chỉ cần gõ lệnh trực tiếp:

virtualenv .venv
(Trong đó .venv là tên thư mục môi trường ảo bạn muốn đặt).

Kích hoạt môi trường (Activate): Bước này hoàn toàn giống như cách cũ:

Windows: .\.venv\Scripts\activate

==============================
Cài đặt thư viện OpenCV
Phần 1: Cài đặt thư viện OpenCV
Trước tiên, hãy chắc chắn rằng bạn đã kích hoạt môi trường ảo .venv trong Terminal của VS Code (bạn sẽ thấy chữ (.venv) ở đầu dòng lệnh).

Sau đó, chạy lệnh sau để cài đặt gói OpenCV dành cho Python:

pip install opencv-python numpy matplotlib

++++++++++++++++++++++++++++++

2. Cập nhật file .env trên Server AWS:
Đừng quên thay đổi dòng GOOGLE_REDIRECT_URI trong file .env trên server AWS của bạn để nó khớp với tên miền mới:

bash
GOOGLE_REDIRECT_URI=https://treeknowledge.online/auth/google/callback
3. Lưu ý quan trọng về SSL (HTTPS):
Vì bạn dùng tên miền có https, hãy đảm bảo server AWS của bạn đã được cài đặt chứng chỉ SSL (như Let's Encrypt). Google OAuth không cho phép dùng http (không có s) cho các tên miền công cộng, chỉ duy nhất localhost là được dùng http.

Nếu bạn chưa cài SSL cho tên miền, Google sẽ báo lỗi ngay khi bạn nhấn đăng nhập đấy!

++++++++++++++++++++++++++++++++++++++++
Đưa lên Google Cloud:
Dự án của bạn đã có sẵn file Dockerfile, đây là một lợi thế cực kỳ lớn! Cách tốt nhất, miễn phí và hiện đại nhất để đưa trang web này lên Google Cloud là sử dụng Google Cloud Run.

Cloud Run cung cấp gói miễn phí hàng tháng (Free Tier) rất rộng rãi (tặng hàng triệu lượt truy cập miễn phí) và tự động cấp sẵn chứng chỉ bảo mật https:// cho bạn.

Dưới đây là hướng dẫn từng bước để đưa trang web của bạn lên Cloud Run hoàn toàn miễn phí:

Bước 1: Chuẩn bị tài khoản và dự án trên Google Cloud
Truy cập Google Cloud Console và đăng nhập bằng tài khoản Google của bạn.
Nếu bạn chưa từng dùng Google Cloud, hệ thống sẽ yêu cầu bạn nhập thẻ Visa/Mastercard (chỉ để xác minh bạn không phải robot, Google sẽ không trừ tiền bạn trừ khi bạn tự tay nâng cấp lên tài khoản trả phí). Bạn thường sẽ được tặng kèm 300$ miễn phí trong 90 ngày.
Ở góc trên cùng bên trái (cạnh logo Google Cloud), nhấn vào nút chọn dự án và tạo một Project mới (ví dụ tên là web-personal-learning). Nhớ lưu lại ID của Project.
Bước 2: Cài đặt công cụ Google Cloud CLI trên máy tính của bạn
Để đưa code từ máy tính lên Google Cloud, bạn cần cài đặt công cụ dòng lệnh của họ:

Tải và cài đặt Google Cloud CLI tại đây: Tải GCloud CLI cho Windows
Sau khi cài xong, mở Terminal (hoặc PowerShell/CMD) trên máy tính của bạn và gõ lệnh sau để đăng nhập:
powershell
gcloud auth login
(Trình duyệt sẽ mở ra để bạn đăng nhập bằng tài khoản Google, hãy nhấn Allow/Cho phép).
Kế tiếp, kết nối Terminal với Project bạn vừa tạo (thay PROJECT_ID bằng ID project của bạn):
powershell
gcloud config set project PROJECT_ID
Bước 3: Đưa trang web lên Cloud (Deploy)
Trong file Dockerfile của bạn, mình thấy web đang được chạy ở port 8081. Hơn nữa, vì dự án của bạn có dùng tới PyTorch và AI, nó sẽ cần một lượng RAM nhất định để khởi động.

Hãy mở Terminal tại đúng thư mục code của bạn (i:\MY_CODE\WebPersionalLearning).
Gõ lệnh sau để đẩy code lên và triển khai (bạn có thể copy nguyên dòng này):
powershell
gcloud run deploy web-app --source . --port 8081 --memory 2Gi --region us-central1 --allow-unauthenticated
Giải thích lệnh trên:

web-app: Tên dịch vụ của bạn trên Cloud.
--source .: Đóng gói code ngay tại thư mục hiện tại dựa trên Dockerfile.
--port 8081: Chỉ định port web đang chạy.
--memory 2Gi: Cấp cho ứng dụng 2GB RAM để đủ chạy PyTorch.
--region us-central1: Chọn máy chủ ở Mỹ (vùng này thuộc gói miễn phí của Google).
--allow-unauthenticated: Cho phép tất cả mọi người trên mạng truy cập (Public).
Bước 4: Chờ đợi và nhận kết quả
Hệ thống sẽ hỏi bạn có muốn bật một vài API cần thiết (như Artifact Registry, Cloud Build) không, bạn cứ gõ y (Yes) rồi nhấn Enter.
Quá trình này sẽ mất khoảng 10 - 20 phút (do Google phải tải PyTorch và các thư viện trong requirements.txt của bạn để đóng gói).
Khi hoàn tất thành công, Terminal sẽ in ra một đường link HTTPS màu xanh lá. Đó chính là trang web của bạn đã được đưa lên mạng! Mọi người có thể vào ngay đường link đó để sử dụng.
💡 Lưu ý nhỏ: Nếu web của bạn cần kết nối đến các API của Google hoặc có file .env, hãy nhớ rằng Cloud Run sẽ không lấy file .env từ máy tính lên. Bạn sẽ phải vào giao diện điều khiển của Google Cloud Run trên web -> Chọn Edit & Deploy New Revision -> Chuyển qua tab Variables & Secrets để cấu hình lại các biến môi trường nhé!

+++++++++++++++++++++
Viewed Dockerfile:1-31

Dự án của bạn đã có sẵn file `Dockerfile`, đây là một lợi thế cực kỳ lớn! Cách tốt nhất, miễn phí và hiện đại nhất để đưa trang web này lên Google Cloud là sử dụng **Google Cloud Run**.

Cloud Run cung cấp gói miễn phí hàng tháng (Free Tier) rất rộng rãi (tặng hàng triệu lượt truy cập miễn phí) và tự động cấp sẵn chứng chỉ bảo mật `https://` cho bạn. 

Dưới đây là hướng dẫn từng bước để đưa trang web của bạn lên Cloud Run hoàn toàn miễn phí:

### Bước 1: Chuẩn bị tài khoản và dự án trên Google Cloud
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/) và đăng nhập bằng tài khoản Google của bạn.
2. Nếu bạn chưa từng dùng Google Cloud, hệ thống sẽ yêu cầu bạn nhập thẻ Visa/Mastercard (chỉ để xác minh bạn không phải robot, Google sẽ **không trừ tiền** bạn trừ khi bạn tự tay nâng cấp lên tài khoản trả phí). Bạn thường sẽ được tặng kèm 300$ miễn phí trong 90 ngày.
3. Ở góc trên cùng bên trái (cạnh logo Google Cloud), nhấn vào nút chọn dự án và tạo một **Project mới** (ví dụ tên là `web-personal-learning`). Nhớ lưu lại ID của Project.

### Bước 2: Cài đặt công cụ Google Cloud CLI trên máy tính của bạn
Để đưa code từ máy tính lên Google Cloud, bạn cần cài đặt công cụ dòng lệnh của họ:
1. Tải và cài đặt Google Cloud CLI tại đây: [Tải GCloud CLI cho Windows](https://cloud.google.com/sdk/docs/install#windows)
2. Sau khi cài xong, mở **Terminal** (hoặc PowerShell/CMD) trên máy tính của bạn và gõ lệnh sau để đăng nhập:
   ```powershell
   gcloud auth login
   ```
   *(Trình duyệt sẽ mở ra để bạn đăng nhập bằng tài khoản Google, hãy nhấn Allow/Cho phép).*
3. Kế tiếp, kết nối Terminal với Project bạn vừa tạo (thay `PROJECT_ID` bằng ID project của bạn):
   ```powershell
   gcloud config set project PROJECT_ID
   ```

### Bước 3: Đưa trang web lên Cloud (Deploy)
Trong file `Dockerfile` của bạn, mình thấy web đang được chạy ở port `8081`. Hơn nữa, vì dự án của bạn có dùng tới PyTorch và AI, nó sẽ cần một lượng RAM nhất định để khởi động.

1. Hãy mở Terminal tại đúng thư mục code của bạn (`i:\MY_CODE\WebPersionalLearning`).
2. Gõ lệnh sau để đẩy code lên và triển khai (bạn có thể copy nguyên dòng này):
   ```powershell
   gcloud run deploy web-app --source . --port 8081 --memory 2Gi --region us-central1 --allow-unauthenticated
   ```

**Giải thích lệnh trên:**
- `web-app`: Tên dịch vụ của bạn trên Cloud.
- `--source .`: Đóng gói code ngay tại thư mục hiện tại dựa trên `Dockerfile`.
- `--port 8081`: Chỉ định port web đang chạy.
- `--memory 2Gi`: Cấp cho ứng dụng 2GB RAM để đủ chạy PyTorch.
- `--region us-central1`: Chọn máy chủ ở Mỹ (vùng này thuộc gói miễn phí của Google).
- `--allow-unauthenticated`: Cho phép tất cả mọi người trên mạng truy cập (Public).

### Bước 4: Chờ đợi và nhận kết quả
- Hệ thống sẽ hỏi bạn có muốn bật một vài API cần thiết (như Artifact Registry, Cloud Build) không, bạn cứ gõ `y` (Yes) rồi nhấn Enter.
- Quá trình này sẽ mất khoảng 10 - 20 phút (do Google phải tải PyTorch và các thư viện trong `requirements.txt` của bạn để đóng gói).
- Khi hoàn tất thành công, Terminal sẽ in ra một **đường link HTTPS màu xanh lá**. Đó chính là trang web của bạn đã được đưa lên mạng! Mọi người có thể vào ngay đường link đó để sử dụng.

> 💡 **Lưu ý nhỏ:** Nếu web của bạn cần kết nối đến các API của Google hoặc có file `.env`, hãy nhớ rằng Cloud Run sẽ không lấy file `.env` từ máy tính lên. Bạn sẽ phải vào giao diện điều khiển của Google Cloud Run trên web -> Chọn `Edit & Deploy New Revision` -> Chuyển qua tab `Variables & Secrets` để cấu hình lại các biến môi trường nhé!
+++++++++++++++++++++++++++++++


gcloud cli
C:\Users\thanh\AppData\Local\Google\Cloud SDK
+++++++++++++++++++++++
AWS server info
IP Address: 56.10.131.44
++++++++++++++++++++++++

git clone https://github.com/tranthanhthangbmt/WebPersionalLearning.git
cd WebPersionalLearning/