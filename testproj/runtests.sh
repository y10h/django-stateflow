#!/bin/sh -e
python bootstrap.py
. ve/bin/activate
(cd .. && python setup.py develop)
python manage.py jenkins
