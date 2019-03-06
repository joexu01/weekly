from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from flask_pagedown.fields import PageDownField


class WeeklyForm(FlaskForm):
    subject = StringField('主题', validators=[DataRequired()])
    finished_work = PageDownField('本周完成工作')
    summary = PageDownField('本周总结')
    demands = PageDownField('协调及帮助请求')
    plan = PageDownField('下周工作任务')
    remarks = PageDownField('备注')
    attachment = FileField('附件')  # 附件的文件类型可以通过 flask_uploads 指定
    visible = BooleanField('周报全平台可见')
    commentable = BooleanField('允许他人评论周报')
    submit = SubmitField('发布周报')


class CommentForm(FlaskForm):
    body = PageDownField('评论', validators=[DataRequired()])
    submit = SubmitField('发布评论')
