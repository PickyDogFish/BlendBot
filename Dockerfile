FROM python:3.9-alpine

RUN mkdir /app

ADD requirements.txt /app
ADD launcher.py /app
ADD fonts /app/fonts
ADD img /app/img
ADD lib /app/lib

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "launcher.py"]