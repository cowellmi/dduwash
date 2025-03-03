from threading import Thread
import cv2

# Pretty much a direct copy of imutils WebcamVideoStream
# https://github.com/PyImageSearch/imutils/blob/master/imutils/video/webcamvideostream.py

class VideoStream:
    cap: cv2.VideoCapture
    ret: bool
    frame: cv2.typing.MatLike
    name: str
    stopped: bool

    def __init__(self, src, name):
        self.cap = cv2.VideoCapture(src)
        (self.ret, self.frame) = self.cap.read()
        self.name = name
        self.stopped = False

    def start(self):
        t = Thread(target=self.update, name=self.name, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return

            # otherwise, read the next frame from the stream
            (self.ret, self.frame) = self.cap.read()

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
