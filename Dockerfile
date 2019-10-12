FROM python:3.6

WORKDIR /app

COPY requirements.txt ./
COPY ./grayws ./grayws
RUN pip3 install -r requirements.txt
ENV FLASK_APP=grayws

CMD gunicorn -w 4 grayws:app --bind=0.0.0.0