import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'plaster_pastedeploy',
    'pyramid >= 1.9a',
    'pyramid_debugtoolbar',
    'pyramid_jinja2',
    'pyramid_retry',
    'pyramid_tm',
    'SQLAlchemy',
    'transaction',
    'zope.sqlalchemy',
    'waitress',
    'click',
    'psycopg2-binary',
    'requests',
    'celery[auth,msgpack]',
    'marshmallow-sqlalchemy',
    'marshmallow-jsonapi',
    'marshmallow',
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',
    'pytest-cov',
]

setup(
    name='taskmanager',
    version='0.1',
    description='taskmanager',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='',
    author_email='',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = taskmanager:main',
        ],
        'console_scripts': [
            'initialize_taskmanager_db = taskmanager.scripts.initializedb:main',
            'state_updater = taskmanager.scripts.state_updater:main',
            'task_scheduler = taskmanager.scripts.task_scheduler:main',
            'tasky = taskmanager.scripts.cli:main',
            'test_run = taskmanager.scripts.test_script_1:main',
            'create_test_data = taskmanager.scripts.create_testdata:main',
            'start_local = taskmanager.client.application:task_app',
        ],
    },
)
