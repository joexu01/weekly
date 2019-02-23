from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, DateField, PasswordField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from flask_uploads import IMAGES
from ..models import User


class EditProfileForm(FlaskForm):
    avatar = FileField('头像', validators=[FileAllowed(IMAGES, message='仅支持上传图片')])
    name = StringField('姓名', validators=[DataRequired(), Length(1, 64)])
    stu_id = StringField('学号', validators=[DataRequired(), Length(1, 13),
                                           Regexp('[0-9]', 0, '学号只能使用数字')])
    birthday = DateField('生日')
    phone = StringField('电话号码', validators=[DataRequired(), Length(11),
                                            Regexp('[0-9]', 0, '电话号码只能使用数字')])
    submit = SubmitField('提交')


class AddUserForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
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
