FROM python:3.11

WORKDIR /app/foodgram

COPY requirements.txt /app/foodgram/

RUN pip install -r requirements.txt --no-cache-dir

COPY . /app/

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV DJANGO_SETTINGS_MODULE=foodgram.settings

ENTRYPOINT ["/entrypoint.sh"]
