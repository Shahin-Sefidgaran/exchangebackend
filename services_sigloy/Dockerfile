FROM python:3.8
ENV PYTHONUNBUFFERED=1

RUN mkdir app
WORKDIR /app

RUN mkdir logs
RUN touch logs/celery.log
COPY . ./

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# CMD python exec.py migrate --seed
