from database import get_user_by_username
from pkt_engine import StudentState

user = get_user_by_username("thanhthangbmt")
if user:
    state = StudentState(user.id)
    print("Testing sync_to_json...")
    try:
        state.sync_to_json()
        print("Done sync_to_json.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("User not found.")
