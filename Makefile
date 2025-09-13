APP_NAME = cctv_ai

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart: down up

clean:
	docker system prune -f
	docker volume prune -f

exec:
	docker exec -it $(APP_NAME) /bin/bash