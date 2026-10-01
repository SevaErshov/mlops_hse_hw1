FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY scripts scripts
COPY models models
COPY data/demo.csv data/demo.csv
COPY tests tests
CMD ["python", "-m", "app.worker"]
