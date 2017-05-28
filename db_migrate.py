#!/usr/bin/env python
# import imp
# from migrate.versioning import api
# from HarryBotter import db
#
# import os
# basedir = os.path.abspath(os.path.dirname(__file__))
# print 'Helllllllo'
# print os.environ['DATABASE_URL']
# v = api.db_version(os.environ['DATABASE_URL'], basedir)
# migration = os.path.join(basedir, 'db_repository') + ('/versions/%03d_migration.py' % (v+1))
# tmp_module = imp.new_module('old_model')
# old_model = api.create_model(os.environ['DATABASE_URL'], basedir)
# exec(old_model, tmp_module.__dict__)
# script = api.make_update_script_for_model(os.environ['DATABASE_URL'],
#                                           basedir,
#                                           tmp_module.meta, db.metadata)
# open(migration, "wt").write(script)
# api.upgrade(os.environ['DATABASE_URL'], basedir)
# v = api.db_version(os.environ['DATABASE_URL'], basedir)
# print('New migration saved as ' + migration)
# print('Current database version: ' + str(v))

from HarryBotter import manager
manager.run()
