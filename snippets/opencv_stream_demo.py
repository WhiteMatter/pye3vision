# Note: this code snippet is relevant for use under the development API in 
# e3vision watchtower v0.3.0 https://www.white-matter.com/e3vision
# Please be aware that api endpoints are subject to change
# prior to api version /v1/

# Requires OpenCV for accessing the camera stream
import cv2 as cv

# what watchtower url to control
watchtowerurl = 'https://localhost:4343'
cameraname = 'e3v8100'

cap = cv.VideoCapture(watchtowerurl + '/api/stream/http?c=' + cameraname + '&rate=15&allowdrops=true')
if not cap.isOpened():
    print("Cannot connect to camera")
    exit()
while True:
    ret, frame = cap.read()
    if not ret:
        print("Cannot read from camera")
        break
    cv.imshow('frame', frame)
    if cv.waitKey(1) == ord('q'):
        break
cap.release()
cv.destroyAllWindows()

