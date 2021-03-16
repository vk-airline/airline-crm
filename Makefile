.PHONY: up check

up:
	docker-compose up -d

check: up
	docker-compose run web pre-commit run --all-files
