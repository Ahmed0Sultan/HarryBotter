#!/usr/bin/env python
from migrate.versioning import api
import os
basedir = os.path.abspath(os.path.dirname(__file__))
api.upgrade(os.environ['DATABASE_URL'], basedir)
v = api.db_version(os.environ['DATABASE_URL'], basedir)
print('Current database version: ' + str(v))
