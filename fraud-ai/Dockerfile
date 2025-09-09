FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# dependențe la nivel de OS (dacă ar fi nevoie, aici e gol pentru slim)
RUN pip install --no-cache-dir -U pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY detect.py ./detect.py
COPY data ./data
# output va fi montat din afară; totuși îl creăm
RUN mkdir -p /app/output

# rulare by default
CMD ["python", "detect.py", "--input", "data/transactions.csv", "--outdir", "output"]
