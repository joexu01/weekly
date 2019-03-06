# 标准库
import os

# FLASK 及与 FLASk 有关的第三方库
from flask_migrate import Migrate

# 本地FLASK
from app import create_app, db
from app.models import User, Role, Group, Weekly, Relation, Mission

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    """ Shell 字典"""
    return dict(db=db, User=User, Role=Role, Group=Group, Weekly=Weekly,
                Relation=Relation, Mission=Mission)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
