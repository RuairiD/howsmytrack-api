dev: venv
	python manage.py runserver

test: venv
	coverage run --source='howsmytrack' manage.py test
	coverage report --fail-under=100
	pre-commit run --all-files

travis: test
	coveralls

venv:
	virtualenv -p python3 venv
	. venv/bin/activate
	pip install -r requirements.txt
	pre-commit install
	python manage.py migrate

clean:
	rm -rf venv
