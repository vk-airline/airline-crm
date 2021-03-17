.PHONY: up check migrate create

up:
	docker-compose up -d

migrate:
	docker-compose run web python manage.py migrate

create: up migrate

check: up
	docker-compose run web pre-commit run --all-files
