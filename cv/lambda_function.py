import os
import time
import json
from threading import Thread
from datetime import datetime
import cv2
import numpy as np
import onnxruntime as rt
import boto3

STDDEV_THRESHOLD = 10
MAX_ATTEMPTS = 10

s3 = boto3.client('s3')
ssm = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('dduwash') # type: ignore

def handler(event, context):
    # Set log level
    os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
    os.environ['OPENCV_FFMPEG_LOGLEVEL'] = "-8"

    # Load onnx model
    response = s3.get_object(Bucket="dduwash-cv", Key="best.onnx")
    session = rt.InferenceSession(response['Body'].read(), providers=['CPUExecutionProvider'])
    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape
    input_size = input_shape[2], input_shape[3]

    # Read secrets
    response = ssm.get_parameter(Name='dduwash-cameras', WithDecryption=True)
    rtsp_urls = json.loads(response['Parameter']['Value'])
    
    results = {}
    errors = []
    for bay_id, rtsp_url in rtsp_urls.items():
        stream = None
        try:
            stream = VideoStream(src=rtsp_url, name=bay_id).start()
            for i in range(1, MAX_ATTEMPTS):
                frame = stream.read()
                if frame is None:
                    continue
                if np.std(frame) < STDDEV_THRESHOLD:
                    # This means the frame is likely all gray or
                    # pixelated and needs time to buffer.
                    time.sleep(0.1)
                    continue
                # Process frame
                img = preprocess_frame(frame, input_size)
                outputs = session.run(None, {input_name: img})
                res = outputs[0][0]
                now = datetime.now()
                results[bay_id] = {
                    'status': int(np.argmax(res)),
                    'timestamp': int(now.timestamp())
                }
                break
            else:
                # If we get here, we've reached MAX_ATTEMPTS
                errors.append({
                    'bay_id': bay_id,
                    'error': 'max attempts'
                })
        except Exception as e:
            errors.append({
                'bay_id': bay_id,
                'error': str(e)
            })
        finally:
            if stream is not None:
                stream.stop()

    for bay_id, res in results.items():
        table.put_item(Item={
            'bay_id': bay_id,
            'status': res['status'],
            'timestamp': res['timestamp'],
            'ttl': res['timestamp'] + 86400 # One day
        })
    
    if errors:
        return {
            'statusCode': 500,
            'body': json.dumps(errors)
        }
    else:
        return {
            'statusCode': 200
        }

def preprocess_frame(frame: cv2.typing.MatLike, input_size):
    img = cv2.resize(frame, input_size)
    img = img.transpose(2, 0, 1)  # Change from HWC to CHW format
    img = img.astype(np.float32) / 255.0  # Normalize
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img

# Simple threaded video stream client
# SOURCE: https://github.com/PyImageSearch/imutils/blob/master/imutils/video/webcamvideostream.py
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
