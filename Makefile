dev: venv
	venv/bin/python manage.py runserver

test: venv
	venv/bin/coverage run --source='howsmytrack' manage.py test
	venv/bin/coverage report --fail-under=100
	venv/bin/pre-commit run --all-files

travis: test
	venv/bin/coveralls

venv:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt
	venv/bin/pre-commit install
	venv/bin/python manage.py migrate

clean:
	rm -rf venv
