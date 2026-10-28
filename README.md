# Todo app

## Запуск

В корне проекта запустите существующую базу PostgreSQL:

```sh
docker start pg-container
```

В первом терминале запустите Python API:

```sh
source .venv/bin/activate
uvicorn app.main:app --port 8080 --reload
```

Во втором терминале запустите интерфейс:

```sh
cd frontend
npm start
```

Откройте http://localhost:3000. Оба терминала должны оставаться запущенными.
Docker обслуживает базу, npm — интерфейс, Uvicorn — API.
Также поддерживается прежняя команда `uvicorn main:app --port 8080 --reload`.

## Структура

- `app/main.py` — создание приложения, подключение маршрутов и CORS.
- `app/api/dependencies.py` — получение сервисов через Depends.
- `app/api/router.py` — общий роутер приложения.
- `app/api/routers/` — HTTP-маршруты задач и категорий.
- `app/schemas/` — форматы запросов и ответов.
- `app/services/` — операции приложения, транзакции и обработка отсутствующих записей.
- `app/repositories/` — запросы к базе данных.
- `app/models/` — SQLAlchemy-модели существующих таблиц.
- `app/db/` — подключение и сессии базы данных.
- `app/core/config.py` — загрузка `DATABASE_URL` и `CORS_ORIGINS` из `.env` и переменных окружения.
- `.env.example` — образец настроек; для нового окружения скопируйте в `.env` и укажите пароль базы. Сам `.env` исключён из Git.
- `main.py` — совместимость с прежней командой запуска.
- `frontend/` — React-интерфейс.

Адреса API: `/tasks`, `/tasks/{task_id}`, `/categories`, `/categories/{category_id}`.
Маршрут `/book` удалён.

## Проверка API

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Проверки используют отдельную временную SQLite-базу и не меняют данные PostgreSQL.

Зависимости сервера: `pip install -r requirements.txt`.
