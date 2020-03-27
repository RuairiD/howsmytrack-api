dev:
	python manage.py runserver

test:
	coverage run --source='howsmytrack' manage.py test
	coverage report --fail-under=100
	flake8 howsmytrack/ --ignore=E501 --exclude=howsmytrack/core/migrations/
