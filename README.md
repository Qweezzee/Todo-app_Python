# Todo app

## Запуск

В корне проекта запустите существующую базу PostgreSQL:

```sh
docker start pg-container
```

Примените миграции базы данных (при первом запуске и после добавления миграций):

```sh
.venv/bin/python -m alembic upgrade head
```

Миграции создают таблицы задач и категорий. Таблицы больше не создаются
автоматически при старте API.

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

## Проверки перед коммитом

Для macOS/Linux используйте Python 3.14 и виртуальное окружение `.venv`
в корне проекта. Установка инструментов и Git-хука:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/pre-commit install
```

Хук запускает Ruff (линтер и проверку форматирования) и mypy для бэкенда,
тестов и миграций. Он использует `.venv` напрямую, поэтому активация окружения
перед коммитом не обязательна. После клонирования хук нужно установить заново.
Версии инструментов закреплены в `requirements-dev.txt`, настройки — в
`pyproject.toml` и `.pre-commit-config.yaml`.

```sh
.venv/bin/pre-commit run --all-files
.venv/bin/python -m unittest discover -s tests -v
```

Хук не меняет файлы автоматически. Для исправления стиля:

```sh
.venv/bin/ruff check . --fix
.venv/bin/ruff format .
```

Для проверки блокировки коммита можно временно добавить файл
`app/precommit_demo.py`:

```python
import os

request_count: int = "wrong type"
```

После `git add app/precommit_demo.py` и `git commit -m "Test hooks"`
Ruff сообщит о неиспользуемом импорте (`F401`), а mypy — о несовместимом
типе (`assignment`). Коммит не будет создан. Затем удалите демонстрационный
файл и выполните `git add -u`, прежде чем коммитить рабочие изменения.
