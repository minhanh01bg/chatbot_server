FROM python:3.10.6
# FROM ubuntu:22.04
# RUN apt update && apt install -y python3.10 python3-pip
# Path: /app
WORKDIR /app

COPY requirements.txt .
# RUN pip install pip==21.3.1
# A new release of pip available: 22.2.1 -> 23.2.1
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .
EXPOSE 7000

CMD ["python","manage.py","runserver","0.0.0.0:7000"]
# models/nlu-20230720-234950-molto-router.tar.gz k xóa stop words
# models/nlu-20230726-090621-shortest-valley.tar.gz xóa stop words