from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, DateField, PasswordField, \
    ValidationError, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from flask_uploads import IMAGES
from ..models import User, Group


class AddGroupForm(FlaskForm):
    group_name = StringField('组名', validators=[DataRequired(), Length(1, 64)])
    # leader_stu_id = StringField('组长学号', validators=[DataRequired(), Length(1, 13),
    #                                        Regexp('[0-9]', 0, '学号只能使用数字')])
    group_leader = SelectField('组长', coerce=int)
    submit = SubmitField('创建组')

    def __init__(self, *args, **kwargs):
        super(AddGroupForm, self).__init__(*args, **kwargs)
        self.group_leader.choices = [(user.id, user.name)
                                     for user in User.query.order_by(User.id).all()]

    def validate_group_name(self, field):
        if Group.query.filter_by(group_name=field.data).first():
            raise ValidationError('该组名已存在')


class EditGroupForm(FlaskForm):
    group_name = StringField('组名', validators=[DataRequired(), Length(1, 64)])
    group_leader = SelectField('组长', coerce=int)
    introduction = TextAreaField('小组介绍')
    notice = TextAreaField('备注')
    submit = SubmitField('提交更改')

    def __init__(self, group, *args, **kwargs):
        super(EditGroupForm, self).__init__(*args, **kwargs)
        self.group_leader.choices = [(user.id, user.name)
                                     for user in User.query.order_by(User.id).all()]
        self.group = group

    def validate_group_name(self, field):
        if field.data != self.group.group_name and \
                Group.query.filter_by(group_name=field.data).first():
            raise ValidationError('该组名已存在')
