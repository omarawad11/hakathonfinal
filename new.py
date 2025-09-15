import cv2
import time

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def capture_good_face(save_path="captured_face.jpg", timeout=15):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # DirectShow works for you
    if not cap.isOpened():
        print("Error: Could not open camera")
        return None

    start_time = time.time()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from camera")
            continue

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Looser parameters for easier detection
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(20, 20)
        )

        print(f"Frame {frame_count}: Found {len(faces)} faces")

        # Draw rectangles for debug
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Save debug frame so you can inspect it
        cv2.imwrite(f"debug_frame_{frame_count}.jpg", frame)

        if len(faces) > 0:
            # pick the largest face
            x, y, w, h = max(faces, key=lambda b: b[2]*b[3])
            best_face = frame[y:y+h, x:x+w]

            cv2.imwrite(save_path, best_face)
            print(f"Face saved at {save_path}")

            cap.release()
            return save_path

        if time.time() - start_time > timeout:
            print("Face capture timed out")
            break

    cap.release()
    return None


if __name__ == "__main__":
    result = capture_good_face()
    print("Result:", result)
