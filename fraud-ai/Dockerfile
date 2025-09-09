FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -U pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY detect.py ./detect.py
COPY realtime_tx_gen.py ./realtime_tx_gen.py
COPY data ./data

RUN mkdir -p /app/output
CMD ["python", "detect.py", "--input", "data/transactions.csv", "--outdir", "output"]
