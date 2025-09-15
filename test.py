from advance_face_recognition import verify_user_image, enroll_user_from_folder

info = enroll_user_from_folder(
    user="Omar Awad",
    folder_path=r"C:\Users\aashq\Downloads\omar FDM",
    out_dir="user_templates",
    k_max=5,
    min_per_cluster=8,
    overwrite=False,
    verbose=True
)
print(info)

res = verify_user_image(
    claimed_user="Omar Awad",
    image_path=r"C:\Users\aashq\Downloads\omar FDM\WhatsApp Image 2025-09-15 at 1.31.25 PM.jpeg",
    out_dir="user_templates",
    model="hog",
    threshold=0.948
)
print(res)