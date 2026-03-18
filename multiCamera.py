import cv2

for i in range(5):
    cap = cv2.VideoCapture(i)
    
    if cap.isOpened():
        print("Camera found at index:", i)
        ret, frame = cap.read()
        
        if ret:
            cv2.imshow(f"Camera {i}", frame)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()
    
    cap.release()