FROM python:3.11

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip wheel -r requirements.txt pymysql

COPY *.py /app/

CMD ["python", "main.py", "-c", "config"]
