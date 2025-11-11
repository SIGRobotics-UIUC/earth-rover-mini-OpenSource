import cv2
'''
rtsp://<Earth Rover Mini IP>/live/0  Front camera main-stream
rtsp://<Earth Rover Mini IP>/live/1  Front camera sub-stream
rtsp://<Earth Rover Mini IP>/live/2  Rear camera main-stream
rtsp://<Earth Rover Mini IP>/live/3  Rear camera sub-stream
'''
cap0 = cv2.VideoCapture("rtsp://192.168.11.1/live/0")
# cap1 = cv2.VideoCapture("rtsp://192.168.11.1/live/1")
cap2 = cv2.VideoCapture("rtsp://192.168.11.1/live/2")
# cap3 = cv2.VideoCapture("rtsp://192.168.11.1/live/3")
if not cap0.isOpened():
    print("Failed to open RTSP stream cap0")
    exit()
# if not cap1.isOpened():
#     print("Failed to open RTSP stream cap1")
#     exit()
if not cap2.isOpened():
    print("Failed to open RTSP stream cap2")
    exit()
# if not cap3.isOpened():
#     print("Failed to open RTSP stream cap3")
#     exit()
while True:
    ret0, frame0 = cap0.read()
    if not ret0:
        print("Failed to read frame0")
        break
    # ret1, frame1 = cap1.read()
    # if not ret1:
    #     print("Failed to read frame1")
    #     break
    ret2, frame2 = cap2.read()
    if not ret2:
        print("Failed to read frame2")
        break
    # ret3, frame3 = cap3.read()
    # if not ret3:
    #     print("Failed to read frame3")
    #     break
    cv2.imshow("RTSP Stream 0", frame0)
    # cv2.imshow("RTSP Stream 1", frame1)
    cv2.imshow("RTSP Stream 2", frame2)
    # cv2.imshow("RTSP Stream 3", frame3)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap0.release()
# cap1.release()
cap2.release()
# cap3.release()
cv2.destroyAllWindows()