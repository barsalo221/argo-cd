FROM python:3.12 AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt
#
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

CMD [ "python", "WEB/app.py" ]