import cv2

# Try different indexes: 0, 1, 2, etc.
cap = cv2.VideoCapture(0)  # Start with 0

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        cv2.imshow("📷 Iriun Webcam Feed", frame)
    else:
        print("⚠️ Failed to grab frame.")
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
