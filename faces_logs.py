import images_space
import logs_db


# save log
rid= logs_db.log_face_event("alice", "203.0.113.42", False)

# save image
local_path = r"C:\Users\aashq\Desktop\FR py\FRDS2\Bill Gates\Bill Gates49_582.jpg"

info = images_space.upload_to_spaces(
    local_path,
    key=f"{rid}.jpg",
)

print(info['url'])