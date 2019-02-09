# weekly

周报系统
后端：FLask(Python) + Jinjia2
测试用前端：Bootstrap

## 目前完成的功能

用户登陆，注册（邮箱验证），忘记密码，修改密码，修改个人信息，用户管理（管理员）

## 在本地运行Demo

### 配置config.py
```
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:atk_2018@localhost:3306/weekly'  # 数据库（所有运行选项都覆盖为测试用的DB）
UPLOADED_AVATAR_DEST = 'D:/Web/weekly/app/static/avatar'  #上传头像的文件夹
```

### 创建虚拟Python环境

### 在终端设置flask_app
`(venv)$set FLASK_APP=weekly.py`

### 数据库迁移
`(venv)$flask db upgrade`

### 运行
`(venv)$flask run



email:joexu01@yahoo.com   or   tyxiaoxu@163.com 