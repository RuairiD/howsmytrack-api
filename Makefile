dev:
	python manage.py runserver

test:
	coverage run --source='howsmytrack' manage.py test
	coverage report --fail-under=100
	pre-commit run --all-files
