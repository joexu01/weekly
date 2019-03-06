from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length
from ..models import Group, Weekly


class SelectGroupForm(FlaskForm):
    group = SelectField('选择要布置任务的组', coerce=int, validators=[DataRequired()])
    submit = SubmitField('下一步')

    def __init__(self, *args, **kwargs):
        super(SelectGroupForm, self).__init__(*args, **kwargs)
        self.group.choices = [(group.id, group.group_name)
                              for group in Group.query.filter_by(group_leader=current_user.id).all()]


class NewMissionForm(FlaskForm):
    user = SelectField('选择要布置任务的成员', coerce=int, validators=[DataRequired()])
    title = StringField('任务名称', validators=[DataRequired(), Length(1, 128)])
    detail = TextAreaField('任务详情')
    year = SelectField('年', validators=[DataRequired()], coerce=str)
    month = SelectField('月', validators=[DataRequired()], coerce=str)
    day = SelectField('日', validators=[DataRequired()], coerce=str)
    hour = SelectField('时', validators=[DataRequired()], coerce=str)
    minute = SelectField('分', validators=[DataRequired()], coerce=str)

    # deadline = DateField('截止时间', validators=[DataRequired()], default=datetime.utcnow)
    # year = StringField(validators=[DataRequired(), Regexp('^[0-9]*$', 0, '请输入正确年份， 如“2019”')])
    # month = StringField(validators=[DataRequired(), Regexp('^[0-9]*$', 0, '请输入正确年份， 如“2019”')])
    # day = StringField(validators=[DataRequired(), Regexp('^[0-9]*$', 0, '请输入正确年份， 如“2019”')])
    # hour = StringField(validators=[DataRequired(), Regexp('^[0-9]*$', 0, '请输入正确时间， 如“12”')])
    submit = SubmitField('创建任务')

    def __init__(self, group, *args, **kwargs):
        super(NewMissionForm, self).__init__(*args, **kwargs)
        self.user.choices = [(user.member.id, user.member.name)
                             for user in group.members]
        years = []
        for i in range(2019, 2030):
            years.append((str(i), str(i)))
        self.year.choices = years
        months = []
        for i in range(1, 13):
            months.append((str(i), str(i)))
        self.month.choices = months
        days = []
        for i in range(1, 31):
            days.append((str(i), str(i)))
        self.day.choices = days
        hours = [('00', '00')]
        for i in range(1, 24):
            hours.append((str(i), str(i)))
        self.hour.choices = hours
        minutes = [('00', '00')]
        for i in range(1, 61):
            minutes.append((str(i), str(i)))
        self.minute.choices = minutes


class SelectWeeklyForm(FlaskForm):
    weekly = SelectField('选择要提交的周报', coerce=int, validators=[DataRequired()])
    submit = SubmitField('提交')

    def __init__(self, user, group_id, *args, **kwargs):
        super(SelectWeeklyForm, self).__init__(*args, **kwargs)
        self.weekly.choices = [(weekly.id, weekly.subject)
                               for weekly in user.my_weekly.filter(Weekly.group_id == group_id).all()]
