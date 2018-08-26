from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = ('aiohttp', 'SQLAlchemy', )
extras = {
    'admin': [
        'aiohttp_jinja2',
        'aiohttp_session',
        'WTForms',
        'WTForms-Alchemy',
        'WTForms-Components'
    ]
}

setup(
    name='webcraft',
    version='0.2.0',
    description=(
        'Async python framework for creating '
        'beautiful REST APIs using aiohttp.'
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='http://github.com/xen/webcraft',
    author='Mikhail Kashkin',
    author_email='m@xen.ru',
    license='BSD 3',
    packages=find_packages(),
    setup_requires=requirements,
    install_requires=requirements,
    extras_require=extras,
    zip_safe=False,
    keywords=['webcraft', 'admin', 'rest',
              'framework', 'api', 'api-framework'],
    classifiers=[
        'Framework :: AsyncIO',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ]
)
