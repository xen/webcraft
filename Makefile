release:
	`pipenv --py` setup.py sdist bdist_wheel && twine upload dist/*
	rm -r dist