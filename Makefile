mig:
	python3 manage.py makemigrations
	python3 manage.py migrate

user:
	python3 manage.py createsuperuser

load:
	python3 manage.py loaddata categories announcements categories