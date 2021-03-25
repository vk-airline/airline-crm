.PHONY: check

check:
	docker-compose run --no-deps app pre-commit run --all-files
