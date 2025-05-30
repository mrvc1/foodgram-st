# Foodgram
### Репозиторий проекта, клонируйте на локальный компьютер:
``` https://github.com/mrvc1/foodgram-st.git ```


### Для ревьюера:
Создать файл .env в папке foodgram-st/
```
POSTGRES_DB=foodgram
POSTGRES_USER=timur
POSTGRES_PASSWORD=tT01052004t
DB_HOST=db
DB_PORT=5432
SECRET_KEY=50 character random string
ALLOWED_HOSTS=localhost,127.0.0.1
DEBUG=False
```
# Обязательно выполнить следующие команды (без них не загрузятся ингредиенты, а без них не пройдут тесты коллекции postman_collection):
### Перейти в папку infra/ и запустить команду:
```
docker compose up --build
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend ls /backend_static/static
docker compose exec backend python manage.py load_ingredients
docker compose exec backend python manage.py createsuperuser
```

## Проект доступен локально по адресу : 
http://localhost:8000/


