# base image
FROM python:3.8

ENV DockerHome=/home/app/wall

RUN mkdir -p $DockerHome
WORKDIR $DockerHOME
COPY WallAPI $DockerHOME
COPY requirements.txt $DockerHOME

ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD python manage.py runserver 0.0.0.0:8000
