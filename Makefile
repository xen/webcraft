release:
	rm -rf dist
	`pipenv --py` setup.py sdist bdist_wheel && pipenv run twine upload dist/*
