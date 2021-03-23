.PHONY: up check migrate create tests

up:
	docker-compose up -d

migrate:
	docker-compose run web python manage.py migrate

create: up migrate

check: up
	docker-compose run --rm web pre-commit run --all-files

tests: up
	docker-compose run --rm python manage.py test
