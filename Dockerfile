FROM python:3.9.19-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Comando per eseguire il bot
CMD ["python", "main.py"]