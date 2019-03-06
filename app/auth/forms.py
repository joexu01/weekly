from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError

from flask_wtf import FlaskForm

from ..models import User


# 登录表单
class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('保持登录状态')
    submit = SubmitField('登录')


# 注册表单
class RegistrationForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1,64), Email()])
    name = StringField('姓名', validators=[DataRequired(), Length(1, 64)])
    stu_id = StringField('学号', validators=[DataRequired(), Length(1, 13),
                                           Regexp('[0-9]', 0, '学号只能使用数字')])
    phone = StringField('电话号码', validators=[DataRequired(), Length(11),
                                            Regexp('[0-9]', 0, '电话号码只能使用数字')])
    password = PasswordField('密码', validators=[DataRequired(),
                                               EqualTo('password2', message='输入密码必须一致')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('确认注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已经被注册')

    def validate_username(self, field):
        if User.query.filter_by(stu_id=field.data).first():
            raise ValidationError('该学号已经被其他人注册')


# 更改密码
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[DataRequired(),
                                                EqualTo('password2', message='输入密码必须一致')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('确认更换密码')


# 密码重置--提交邮箱
class PasswordResetRequestForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                          Email()])
    submit = SubmitField('提交')


# 密码重置
class PasswordResetForm(FlaskForm):
    password = PasswordField('新密码', validators=[DataRequired(),
                                                EqualTo('password2', message='两次输入密码必须一致')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('重设密码')

# 更换邮箱
class ChangeEmailForm(FlaskForm):
    email = StringField('新邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('更新邮箱地址')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱地址已经被注册')
