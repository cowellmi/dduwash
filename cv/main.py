import os
import time
import cv2
import numpy as np
import onnxruntime as rt
import psycopg2
from psycopg2.extensions import connection
from datetime import datetime, timezone, timedelta
from stream import VideoStream


BAYS = ["washbay1", "washbay2", "washbay3", "washbay4", "washbay5", "washbay6"]
SHUTDOWN_FLAG = False
STDDEV_THRESHOLD = 10
MAX_ATTEMPTS = 10
BUFFER_DELAY = 5  # seconds
MAIN_DELAY = 10  # seconds
STATUS_CACHE = {}  # bay_id -> (status_code, timestamp)


def handle_exit_signal(signum, frame):
    global SHUTDOWN_FLAG
    SHUTDOWN_FLAG = True


def open_streams(hostname, port):
    vs_dict: dict[str, VideoStream] = {}
    for bay_id in BAYS:
        rtsp_url = f"rtsp://{hostname}:{port}/{bay_id}"
        vs_dict[bay_id] = VideoStream(rtsp_url, bay_id).start()
    
    return vs_dict


def preprocess_frame(frame: cv2.typing.MatLike, input_size):
    img = cv2.resize(frame, input_size)
    img = img.transpose(2, 0, 1)  # Change from HWC to CHW format
    img = img.astype(np.float32) / 255.0  # Normalize
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img


def db_connect(dsn):
    try:
        return psycopg2.connect(dsn)
    except (psycopg2.DatabaseError, Exception) as error:
        print("unable to connect to db:", error)
        exit(1)


def db_get_last_status(conn: connection, bay_id):
    # Check cache first
    if bay_id in STATUS_CACHE:
        return STATUS_CACHE[bay_id][0]

    query = """
        SELECT status_code
        FROM bay_status 
        WHERE bay_id = %s
        ORDER BY time DESC
        LIMIT 1;
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (bay_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    

def db_get_last_time(conn: connection, bay_id):
    # Check cache first
    if bay_id in STATUS_CACHE:
        return STATUS_CACHE[bay_id][1]

    query = """
        SELECT time
        FROM bay_status 
        WHERE bay_id = %s
        ORDER BY time DESC
        LIMIT 1;
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (bay_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    

def db_insert_bay_status(conn: connection, bay_id, status):
    query = """
        INSERT INTO bay_status (bay_id, status_code)
        VALUES (%s, %s)
        RETURNING time;
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (bay_id, status))
        time = cursor.fetchone()[0]
        conn.commit()
    
    # Update cache
    STATUS_CACHE[bay_id] = (status, time)


def main():
    # Set log level
    os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
    os.environ['OPENCV_FFMPEG_LOGLEVEL'] = "-8"

    # Read environment
    dsn =  os.getenv("DATABASE_URL")
    mtx_hostname = os.getenv("MEDIAMTX_HOSTNAME")
    mtx_port = os.getenv("MEDIAMTX_PORT")
    if not dsn or not mtx_hostname or not mtx_port:
        print("error: missing environment")
        exit(1)
    
    # Open database connection
    conn = db_connect(dsn)

    # Open streams
    vs_dict = open_streams(mtx_hostname, mtx_port)

    # Create inference session from model
    model = "best.onnx"
    session = rt.InferenceSession(
        model, providers=['CPUExecutionProvider']
    )
    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape
    input_size = input_shape[2], input_shape[3]

    while not SHUTDOWN_FLAG:
        for bay_id, vs in vs_dict.items():
            for i in range(1, MAX_ATTEMPTS):
                frame = vs.read()
                if frame is None:
                    print(f"{bay_id} ({i}): error reading stream")
                    continue

                # Check if standard deviation is sufficiently complex.
                # Sometimes, the  initial frames will be all gray
                # (or slighly pixelated) because the stream is buffering.
                if np.std(frame) > STDDEV_THRESHOLD:
                    img = preprocess_frame(frame, input_size)
                    outputs = session.run(None, {input_name: img})
                    results = outputs[0][0]

                    # Get the result with the highest score
                    cur_status = int(np.argmax(results))
                    last_status = db_get_last_status(conn, bay_id)

                    # Update status if there was a change
                    if last_status is None or last_status != cur_status:
                        # If last status was occupied, make sure we wait
                        # 3 minutes before changing it to empty.
                        if last_status == 1:
                            last_time = db_get_last_time(conn, bay_id)
                            if last_time is not None:
                                now = datetime.now(timezone.utc)
                                elapsed_time = now - last_time
                                if elapsed_time < timedelta(minutes=3):
                                    break

                        db_insert_bay_status(conn, bay_id, cur_status)

                    break

                print(f"{bay_id} ({i}): buffering")
                time.sleep(BUFFER_DELAY)
            else:
                print(f"{bay_id}: unable to process stream")
        
        time.sleep(MAIN_DELAY)

    # Cleanup
    for cap in vs_dict.values():
        cap.stop()

    conn.close()
    
    time.sleep(2) # wait a sec to let streams close


if __name__ == "__main__":
    main()
