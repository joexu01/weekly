import os

from flask_uploads import IMAGES

basedir = os.path.abspath(os.path.dirname(__file__))


# 正式上线时使用环境配置，从本地获取  e.g. CONFIG = os.environ.get('CONFIG_NAME')
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'  # 应用秘钥
    MAIL_SERVER = 'smtp.163.com'  # 邮件服务器配置
    MAIL_PORT = int(465)  # 邮件端口
    MAIL_USERNAME = 'tyxiaoxu'
    MAIL_PASSWORD = 'flasktest01'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    FLASK_MAIL_SUBJECT_PREFIX = '[周报系统]'  # 邮件标题前缀
    FLASK_MAIL_SENDER = 'Admin <tyxiaoxu@163.com>'  # 发送者名称
    FLASK_ADMIN = 'tyxiaoxu@163.com'  # FLASK 管理者邮箱
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:atk_2018@localhost:3306/weekly'  # 数据库URI
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    UPLOADED_AVATAR_DEST = 'D:/Web/weekly/app/static/avatar'  # 上传头像集  最好使用绝对路径  易于维护
    UPLOADED_ATTACHMENTS_DEST = 'D:/Web/weekly/app/static/attachments'  # 上传附件集
    # 关于这个的设置，参见
    # https://stackoverflow.com/questions/23650544/runtimeerror-cannot-access-configuration-outside-request
    IMG_UPLOAD_ALLOWED = IMAGES
    WEEKLY_USER_PER_PAGE = 10
    WEEKLY_GROUP_PER_PAGE = 10
    WEEKLY_WEEKLY_PER_PAGE = 10
    WEEKLY_COMMENT_PER_PAGE = 10
    WEEKLY_MISSION_PER_PAGE = 10

    @staticmethod
    def init_app(app):
        pass


# 开发环境数据库配置
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:atk_2018@localhost:3306/weekly'


# 测试环境数据库配置
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:atk_2018@localhost:3306/weekly'


# 运营环境数据库配置
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
