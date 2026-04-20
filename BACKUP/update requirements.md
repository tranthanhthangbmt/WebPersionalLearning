pip freeze > requirements.txt

dọn rác
sudo docker system prune -a --volumes -f
sudo apt-get clean
+++++++++++++++++++
Kết luận lại:
Vì Dockerfile của bạn đã chuẩn chỉnh về đường dẫn, nên thủ phạm duy nhất gây ra lỗi ModuleNotFoundError: No module named 'models' chắc chắn là do các thư mục của bạn đang thiếu file __init__.py (như mình đã giải thích ở Bước 1 của tin nhắn trước).

Bây giờ bạn hãy làm tiếp các bước sau để web hoạt động nhé:

Gõ 2 lệnh này trên PuTTY để báo cho Python biết đây là các thư mục module:

Bash
touch models/__init__.py
touch services/__init__.py
Xóa container bị lỗi cũ đi:

Bash
sudo docker rm myapp
Đóng gói (build) lại image mới để nó cập nhật các file bạn vừa tạo:

Bash
sudo docker build -t treeknowledge-app .
Chạy lại vùng chứa (container):

Bash
sudo docker run -d -p 80:8081 --name myapp treeknowledge-app
Bạn hãy thực hiện các lệnh trên và chạy lại sudo docker ps xem trạng thái đã hiện là Up chưa nhé?

+++++++++++++++++++
Nhìn vào kết quả lệnh docker ps trống trơn của bạn, điều này có nghĩa là container đã được tạo thành công (đó là lý do nó in ra một mã ID dài ngoằng a18ae69...), nhưng ứng dụng bên trong đã gặp lỗi và tự tắt (crash) ngay lập tức.

Trong Docker, nếu tiến trình chính (như web server của bạn) không chạy thành công, container sẽ tự động đóng lại.

Để biết chính xác nguyên nhân tại sao ứng dụng của bạn không khởi động được, bạn hãy chạy lệnh xem nhật ký (log) của container này:

Bash
sudo docker logs myapp
Lệnh này sẽ in ra những thông báo lỗi cuối cùng từ mã nguồn Python của bạn (ví dụ: thiếu thư viện, sai đường dẫn file, hoặc sai cổng port).

Lưu ý quan trọng cho lần chạy tiếp theo:
Vì container myapp hiện đang ở trạng thái "đã tắt" chứ chưa bị xóa, nếu bạn sửa lỗi xong và muốn chạy lại lệnh docker run ... --name myapp ... cũ, hệ thống sẽ báo lỗi trùng tên. Do đó, trước khi chạy lại, bạn cần xóa chiếc container bị lỗi này đi bằng lệnh:

Bash
sudo docker rm myapp

+++++++++++++++++
Cách 2: "Reset mềm" dọn sạch máy chủ hiện tại (Làm trực tiếp trên PuTTY)
Nếu bạn ngại lên web tạo máy chủ mới và muốn tận dụng lại đúng máy này, chúng ta sẽ xóa sạch toàn bộ code, file rác và giải phóng ổ cứng để lấy chỗ cài Docker.

Bạn hãy copy và dán lần lượt các lệnh sau vào PuTTY:

1. Di chuyển về thư mục gốc của user:

Bash
cd /home/ubuntu/
2. Xóa toàn bộ file và thư mục hiện có (Bao gồm cả đống file lộn xộn lúc nãy):

Bash
rm -rf *
3. Xóa các file ẩn và bộ nhớ đệm (Giải phóng dung lượng ổ cứng đã bị chiếm dụng):

Bash
rm -rf ~/.cache
rm -rf ~/.local
4. Dọn rác hệ điều hành:

Bash
sudo apt autoremove -y
sudo apt clean

++++++++++++++++++
Bước 1: Di chuyển đến đúng thư mục
Để chắc chắn bạn đang thao tác đúng vị trí chứa file, hãy nhập lệnh sau và nhấn Enter:

Bash
cd /home/ubuntu/
Bước 2: Giải nén file
Bạn sử dụng lệnh unzip để giải nén file WebPersionalLearning.zip ra ngay tại thư mục hiện tại:

Bash
unzip WebPersionalLearning.zip