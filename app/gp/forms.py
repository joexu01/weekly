from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, \
    ValidationError, SelectField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Length
from ..models import User, Group, Relation
from .. import db


class AddGroupForm(FlaskForm):
    group_name = StringField('组名', validators=[DataRequired(), Length(1, 64)])
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
    introduction = TextAreaField('小组介绍')
    notice = TextAreaField('备注')
    submit = SubmitField('提交更改')

    def validate_group_name(self, field):
        if field.data != self.group.group_name and \
                Group.query.filter_by(group_name=field.data).first():
            raise ValidationError('该组名已存在')


class AdminEditGroupForm(FlaskForm):
    group_name = StringField('组名', validators=[DataRequired(), Length(1, 64)])
    group_leader = SelectField('组长', coerce=int)
    introduction = TextAreaField('小组介绍')
    notice = TextAreaField('备注')
    submit = SubmitField('提交更改')

    def __init__(self, group, *args, **kwargs):
        super(AdminEditGroupForm, self).__init__(*args, **kwargs)
        filter_array = [r.member_id for r in db.session.query(Relation).filter(
            Relation.group_id == group.id)]
        self.group_leader.choices = [(user.id, user.name)
                                     for user in User.query.filter(User.id.in_(filter_array))]
        self.group = group

    def validate_group_name(self, field):
        if field.data != self.group.group_name and \
                Group.query.filter_by(group_name=field.data).first():
            raise ValidationError('该组名已存在')


class SelectMembersForm(FlaskForm):
    group_members = SelectMultipleField('选择组员', coerce=int, validators=[DataRequired()])
    submit = SubmitField('添加组员')

    def __init__(self, group, *args, **kwargs):
        super(SelectMembersForm, self).__init__(*args, **kwargs)
        filter_array = [r.member_id for r in db.session.query(Relation).filter(
            Relation.group_id == group.id)]
        self.group_members.choices = [(user.id, user.name)
                                      for user in User.query.filter(~User.id.in_(filter_array))]
        self.group = group
        # 记录一下解决这个问题的过程：
        # 原本想用LEFT JOIN 连接User 和 筛选过后的Relation 表，但是无法解决，返回的查询
        # 只是该组组内成员，而需要的是结果在User内的补集
        # 因此，使用一个关键词过滤器filter(~User.id.in_(关键词数组))
        # 过滤掉已经在组内的成员, ~ 的意思就跟 not 差不多
