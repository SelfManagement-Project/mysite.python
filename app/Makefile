run:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

format:
    black .

lint:
    flake8 .

docker-build:
    docker-compose up --build -d

migrate:
    alembic upgrade head
