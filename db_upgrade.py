#!flask/bin/python
from migrate.versioning import api
import os
basedir = os.path.abspath(os.path.dirname(__file__))
api.upgrade(os.environ['DATABASE_URL'], os.path.join(basedir, 'db_repository'))
v = api.db_version(os.environ['DATABASE_URL'], os.path.join(basedir, 'db_repository'))
print('Current database version: ' + str(v))
