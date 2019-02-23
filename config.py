import os
from flask_uploads import IMAGES
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = int(465)
    MAIL_USERNAME = 'tyxiaoxu'
    MAIL_PASSWORD = 'flasktest01'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[周报系统]'
    FLASKY_MAIL_SENDER = 'Admin <tyxiaoxu@163.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:atk_2018@localhost:3306/wk'
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    UPLOADED_AVATAR_DEST = 'D:/Web/weekly/app/static/avatar'
    UPLOADED_ATTACHMENTS_DEST = 'D:/Web/weekly/app/static/attachments'
    # 关于这个的设置，参见
    # https://stackoverflow.com/questions/23650544/runtimeerror-cannot-access-configuration-outside-request
    IMG_UPLOAD_ALLOWED = IMAGES
    WEEKLY_USER_PER_PAGE = 10
    WEEKLY_GROUP_PER_PAGE = 10
    WEEKLY_WEEKLY_PER_PAGE = 10
    WEEKLY_COMMENT_PER_PAGE = 10

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:atk_2018@localhost:3306/weekly'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:atk_2018@localhost:3306/weekly'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:atk_2018@localhost:3306/weekly'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
