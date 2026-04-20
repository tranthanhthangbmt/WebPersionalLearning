import streamlit_authenticator as stauth
import sys

# Danh sách mật khẩu bạn muốn mã hóa
passwords_to_hash = ['abc123', 'abc']  # Sửa lại mật khẩu của bạn ở đây nếu muốn

hashed_passwords = []

print("Đang mã hóa mật khẩu (Lần thử 3)...")

try:
    # 1. Khởi tạo Hasher (sửa lỗi đầu tiên)
    # Chúng ta tạo một thực thể (instance)
    hasher = stauth.Hasher()
    
    # 2. Gọi phương thức .hash() trên thực thể đó (sửa lỗi thứ hai)
    for password in passwords_to_hash:
        hashed_passwords.append(hasher.hash(password))
        
except Exception as e:
    print(f"Lỗi khi mã hóa: {e}", file=sys.stderr)
    print("Có vẻ như API đã thay đổi. Vui lòng kiểm tra tài liệu của 'streamlit-authenticator'.", file=sys.stderr)
    sys.exit(1)

print("\n--- SAO CHÉP DANH SÁCH DƯỚI ĐÂY ---")
print(hashed_passwords)
print("------------------------------------")
print("\n-> Dán danh sách này vào file 'config.yaml' để thay thế cho mật khẩu '???'")