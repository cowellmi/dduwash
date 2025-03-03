FROM python:3.11-slim  

WORKDIR /app

COPY main.py stream.py best.onnx requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
