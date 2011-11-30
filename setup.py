from setuptools import setup, find_packages

setup(
    name = 'django-stateflow',
    url='https://github.com/jellycrystal/django-stateflow',
    version = '0.4.0',
    description = 'Workflow engine for Django',
    packages = find_packages(),
    maintainer='Yury Yurevich',
    maintainer_email='yyurevich@jellycrystal.com',
    # Get more strings from http://www.python.org/pypi?:action=list_classifiers
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)

