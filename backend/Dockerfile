FROM python:3.11

WORKDIR /app/foodgram

COPY requirements.txt /app/foodgram/

RUN pip install -r requirements.txt --no-cache-dir

COPY . /app/

ENV DJANGO_SETTINGS_MODULE=foodgram.settings

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
