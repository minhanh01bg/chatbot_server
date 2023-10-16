FROM python:3.10.6

# Path: /app
WORKDIR /app

COPY requirements.txt .
RUN pip install pip==21.3.1
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5056
CMD ["rasa", "run", "--enable-api", "-m", "./models/nlu-20230823-154033-rectilinear-tritone.tar.gz", "-p", "5056"]
# models/nlu-20230720-234950-molto-router.tar.gz k xóa stop words
# models/nlu-20230726-090621-shortest-valley.tar.gz xóa stop words