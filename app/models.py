from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import bleach
from markdown import markdown

from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app

from . import db, login_manager


# 权限常量
class Permission:
    COMMENT = 1
    WRITE = 2
    GROUP = 4
    ADMIN = 8


# 用户角色
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)  # 角色id
    name = db.Column(db.String(64), unique=True)  # 角色名称
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.COMMENT, Permission.WRITE],
            # 'Group_leader': [Permission.COMMENT, Permission.WRITE, Permission.GROUP],
            'Administrator': [Permission.COMMENT, Permission.WRITE, Permission.GROUP, Permission.ADMIN]
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    @staticmethod  # 这是个危险的测试方法！
    def give_admin(stu_id):
        user = User.query.filter_by(stu_id=stu_id).first()
        user.role_id = 2
        db.session.add(user)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    # has_permission 方法用位与运算符检查组合权限是否包含指定的单独权限

    def __repr__(self):
        return '<Role %r>' % self.name


# 任务模型
class Mission(db.Model):
    __tablename__ = 'missions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    detail = db.Column(db.Text)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    weekly_id = db.Column(db.Integer, db.ForeignKey('weekly.id'))
    is_known = db.Column(db.Boolean, default=False)
    is_accomplished = db.Column(db.Boolean, default=False)
    is_terminated = db.Column(db.Boolean, default=False)
    assign_person_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, default=datetime.utcnow)


# 组-组员关系模型
class Relation(db.Model):
    __tablename__ = 'relations'
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'),
                         primary_key=True)  # 组id
    member_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                          primary_key=True)  # 成员id
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)


# 个人信息：邮箱，姓名，学号，生日，手机号，头像
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)  # 邮箱
    name = db.Column(db.String(64))  # 姓名
    stu_id = db.Column(db.String(13), unique=True)  # 学号
    birthday = db.Column(db.Date, default=datetime.utcnow)  # 生日
    phone = db.Column(db.String(11))  # 手机号码
    avatar = db.Column(db.String(128), default='default.jpg')  # 头像
    confirmed = db.Column(db.Boolean, default=False)  # 是否验证邮箱
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # 权限ID
    password_hash = db.Column(db.String(128))  # 密码哈希值
    group_leader = db.relationship('Group', backref='leader', lazy='dynamic')  # 返回用户作为组长的组的查询结果
    my_weekly = db.relationship('Weekly', backref='author', lazy='dynamic')  # 返回用户创建的周报
    groups = db.relationship('Relation',
                             foreign_keys=[Relation.member_id],
                             backref=db.backref('member', lazy='joined'),
                             lazy='dynamic', cascade='all, delete-orphan')  # 返回用户加入的所有组，包括作为组长的组
    comments = db.relationship('Comment', backref='author', lazy='dynamic')  # 返回用户的所有评论
    missions = db.relationship('Mission',
                               foreign_keys=[Mission.user_id],
                               backref=db.backref('user', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')
    # 返回用户的所有任务
    assigned_missions = db.relationship('Mission',
                                        foreign_keys=[Mission.assign_person_id],
                                        backref=db.backref('assign_person', lazy='joined'),
                                        lazy='dynamic', cascade='all, delete-orphan')

    # 返回用户布置的所有任务

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 生成确认邮箱token
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    # 确认邮箱token
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    # 生成重置token
    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    # 删除用户的还需要把relations 表中的相关记录删除
    def delete(self):
        if self.is_administrator():
            return False
        relations = Relation.query.filter_by(member_id=self.id).all()
        for r in relations:
            db.session.delete(r)
        db.session.delete(self)
        db.session.commit()

    # 权限确认方法
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    # 确认当前用户是否属于某组
    def is_in_group(self, group):
        if group.id is None:
            return False
        return self.groups.filter_by(group_id=group.id).first() is not None

    def __repr__(self):
        return '<User %r>' % self.name


# 组模型
class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(64), unique=True, index=True)  # 组名
    group_leader = db.Column(db.Integer, db.ForeignKey('users.id'))  # 组长
    introduction = db.Column(db.Text())  # 简介
    notice = db.Column(db.Text())  # 组内公告
    weekly = db.relationship('Weekly', backref='group', lazy='dynamic')  # 返回该组的所有周报
    members = db.relationship('Relation',
                              foreign_keys=[Relation.group_id],
                              backref=db.backref('group', lazy='joined'),
                              lazy='dynamic', cascade='all, delete-orphan')  # 返回该组在 relations 表中的所有记录
    missions = db.relationship('Mission', backref='group', lazy='dynamic')  # 返回该组的所有任务

    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)
        relation = Relation(group=self, member_id=self.group_leader)
        db.session.add(relation)
        db.session.commit()

    # 删除方法还需要把relations 表中的相关记录删除
    def delete(self):
        relations = Relation.query.filter_by(group_id=self.id).all()
        for r in relations:
            db.session.delete(r)
        db.session.delete(self)
        db.session.commit()

    # 判断该用户是否是当前组的成员
    def is_a_member(self, user):
        if user.id is None:
            return False
        return self.members.filter_by(member_id=user.id).first() is not None

    def __repr__(self):
        return '<Group %r>' % self.group_name


# 未登录用户模型
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


class WeeklyHtml(db.Model):
    __tablename__ = 'weekly_html'
    id = db.Column(db.Integer, db.ForeignKey('weekly.id'), primary_key=True)
    finished_work_html = db.Column(db.Text())
    summary_html = db.Column(db.Text())
    demands_html = db.Column(db.Text())
    plan_html = db.Column(db.Text())
    remarks_html = db.Column(db.Text())

    def __init__(self, weekly_id):
        super(WeeklyHtml, self).__init__()
        self.id = weekly_id


# 周报模型
class Weekly(db.Model):
    __tablename__ = 'weekly'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(128))  # 周报主题
    finished_work = db.Column(db.Text())  # 已经完成的工作
    summary = db.Column(db.Text())  # 总结
    demands = db.Column(db.Text())  # 协调请求和需要的帮助
    plan = db.Column(db.Text())  # 下周计划
    remarks = db.Column(db.Text())  # 备注
    attachment = db.Column(db.String(512))  # 附件名称
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 作者
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))  # 属于组
    visible = db.Column(db.Boolean, default=True)  # 默认全平台可见
    commentable = db.Column(db.Boolean, default=True)  # 默认可以评论
    comments = db.relationship('Comment', backref='weekly', lazy='dynamic', cascade='all, delete-orphan')  # 返回该周报所有评论
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # 时间戳
    mission = db.relationship('Mission', backref='weekly', lazy='dynamic', cascade='all, delete-orphan')  # 返回该组所有任务
    weekly_html = db.relationship('WeeklyHtml', backref='weekly', lazy='dynamic',
                                  cascade='all, delete-orphan')  # 返回该周报所有的html形式的属性

    def __init__(self, *args, **kwargs):
        super(Weekly, self).__init__(*args, **kwargs)

    def ping(self):
        self.timestamp = datetime.utcnow()
        db.session.add(self)
        db.session.commit()


# 评论模型
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    weekly_id = db.Column(db.Integer, db.ForeignKey('weekly.id'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
