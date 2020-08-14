# FasterRunner

[![LICENSE](https://img.shields.io/github/license/HttpRunner/FasterRunner.svg)](https://github.com/HttpRunner/FasterRunner/blob/master/LICENSE) [![travis-ci](https://travis-ci.org/HttpRunner/FasterRunner.svg?branch=master)](https://travis-ci.org/HttpRunner/FasterRunner) ![pyversions](https://img.shields.io/pypi/pyversions/Django.svg)

> FasterRunner that depends FasterWeb

## 注意
如果在20190828日期之前，已经部署过我的FasterRunner,此次更新时，需要一些手动操作：
1. 拉取新代码后, 先将 apps/users/models.py 中 belong_project 这一行注释掉
2. python manage.py makemigrations，生成 0001_initial 文件
3. python manage.py dbshell 进入数据库 或者手动修改数据库
  - INSERT INTO django_migrations (app, name, applied) VALUES ('users', '0001_initial', CURRENT_TIMESTAMP);
  - UPDATE django_content_type SET app_label = 'users' WHERE app_label = 'auth' and model = 'user';
4. python manage.py migrate
5. 去除 1 中的注释，再次执行 python manage.py makemigrations ，python manage.py migrate


### 简介
在上一位作者的基础上，完善并且丰富了平台的功能，支持全部的httprunner特性重要更新如下：
- 增加测试数据页面：文件上传与下载，上传的文件可直接在py文件里引用，并且文件可锁定，锁定后无法更新/删除,保证测试数据在使用时的安全稳定。测试用例页面也可快速上传文件。
- 增加了自己的配置文件，在setting.py中引用，便于管理开发与本地调试，模板见文件：config.conf,自己创建myconfig.conf
- 驱动代码页面支持多python文件在线编辑
- 批量api模板上传（ 支持httprunner -V 1.X/2.X），根据自己的项目情况更改db_tools/import_api_data.py中 “MY_API_FILEPATH PROJECT_ID” 后，在根目录下执行命令 python db_tools\import_api_data.py, 然后刷新页面即可。
- 支持skipIf机制。编辑testcase时可编辑api中skipIf一栏。
- 支持testcase运行时指定failfast参数。 在配置信息中控制failfast开关。
- 重构了域名管理功能，用于配置环境相关信息，相当于配置管理的一个拆分，便于单个调试api以及快速切换环境，这样组合配置信息与环境信息可减少重复配置信息，减少维护量。而对于base_url字段，域名管理的权限高于配置管理，若域名管理里base_url不为空，则会覆盖配置管理的base_url。例如可以只将登录所需信息放在域名管理里。
- 重构了用户认证，使用了drf-jwt应用，移除了注册功能，直接从后台分配账号（出于安全考虑）
- api/testcase运行时可以填写测试数据两个字段，此字段在后台运行时会生成系统环境变量“excelName”/“excelsheet”。此字段在驱动代码里可以os.environ["excelsheet"]方式获取，并进一步做自己的处理。这里我主要想法是，测试用例读取数据时，不再从固定的表里读取数据，而是只要有对应的表头，就可以返回测试数据，这样一条测试用例可以被很方便的调用。
- 增加了简易的excel报告，提取了简要的报错信息，便于大批量运行测试用例时查看
- 同步运行时抓取httprunner错误返回到前端。
- 配置管理里新加了output参数，output将写入报告里，output参数来自于整个用例运行时variables/extract等。
- 更新了api与testcase的关系。沿用httprunner作者的思想，测试用例中的request/headers/method/url内容直接调用相应api中的内容；更新api中的request/header/method/url时，不会自动更新测试用例中的api信息，提供了同步操作，手动更新（这里主要是考虑到在项目周期中，可能有生产环境的任务需要执行，而在测试环境还没发布到生产的时候，更新了api基本信息会导致生产环境任务不兼容而失败。如果项目中有这种情况的话，推荐复制case，并通过复制的case进行测试环境测试，保证生产环境case的稳定）。
- 支持异步运行测试用例。
- 增加了xadmin后台管理系统，通过后台管理系统可以方便的完成分配账号以及api层权限控制以及数据增删改查操作
- 书写了在服务器上的docker-compose部署方式，参考docker-compose.yml文件。networks参数是内网，需要先在后台创建。
- 定时任务模块可以单独运行且发送邮件。定时任务里的每一条用例互不相干。
- 定时任务 邮件策略增加了监控邮件策略，当同样的错误多次发生时，将不再发送邮件（通过报警次数控制），直至报错发生改变或者没有错时发送一份恢复邮件，没有错误则不发送邮件；且可以对报错进行关键字过滤，若api返回报错包含关键字，则临时将该api返回的报错视为空值。
- 定时任务模块发送出的邮件，增加了在线查看报告功能,通过配置myconfig.conf即可;并且可以自行配置过滤敏感字段（如登录帐号密码/cookies），防止被恶意爬虫等。
- 增加了查看异步任务执行状态的页面，方便查看异步任务（目前没有做到按项目区分）
- 增加用户所属项目权限控制以及数据显示



```bash
## Docker-compose 部署 (FasterRunner/FasterWeb/mysql 放在宿主机同一目录下)
1. git pull/clone https://github.com/weirdohaibo/FasterRunner.git  # 拉取后端代码
2. docker build -t fastrunner:latest .  # 进入FasterRunner目录下构建fastrunner镜像
3. 修改 FasterRunner/settings.py env = 'prod'; rabbitMQ 的BROKER_URL参数
4. 删除 FasterRunner/*.pid 文件
5. 根据 FasterRunner/config.conf 文件新建 FasterRunner/myconfig.conf 并配置参数
6. git pull/clone https://github.com/weirdohaibo/FasterWeb.git  # 拉取前端代码
7. 根据自己需要更改 FasterWeb/default.conf 以及 FasterWeb/src/restful/api.js 的请求路径
8. FasterWeb目录下执行npm install, npm run build  # 生成生产环境包
9. docker build -t fastweb:latest .  # 进入FasterWeb目录下构建fastweb镜像
10. 将FasterRunner/docker-compose.yml 文件放置在根目录下,并修改配置
11. docker-compose up -d  # 后台启动
12. docker exec -it fastrunner-lts bash  # 进入后端容器
13. python3 manage.py makemigrations  # 生成迁移表
14. python3 manage.py migrate  # 执行迁移数据
15. python3 manage.py createsuperuser  # 按提示创建一个超级用户
16. 访问生产地址
17. 之后更新版本时,如果依赖包没有变化,只需执行步骤1/3/4/6/7/8,然后 docker-compose restart 即可;如果依赖包有变化则需要重新打镜像;如果数据库有变化则需要12/13/14

```


```
## Docker 部署 uwsgi+nginx模式
1. docker pull docker.io/mysql:5.7 # 拉取mysql5.7镜像
2. sudo docker run --name mysql -p3306:3306 -d --restart always -v /home/ebao/fastRunner/mysql:/var/lib/mysql
-e  MYSQL_ROOT_PASSWORD=xhb123456 docker.io/mysql:5.7 --character-set-server=utf8 --collation-server=utf8_general_ci  # 运行mysql容器
3. docker exec -it (container_id) bash / mysql -P3306 -h127.0.0.1 -uroot -pxhb123456 连接数据库, 新建一个db，与setting中数据库信息保持一致。
4. 修改settings.py 中使用的配置环境信息dev/prod，复制或者重命名config.conf为myconfig.conf，更新信息
5. 启动rabbitmq docker run -d --name --net=host --restart always rabbitmq -e RABBITMQ_DEFAULT_USER=user -e RABBITMQ_DEFAULT_PASS=password rabbitmq:3-management
6. 修改settings.py BROKER_URL(配置rabbittmq的IP，username,password)
7. 根目录下新建空文件夹tempWorkDir,media,logs 
8. docker build -t fastrunner:latest .    # 构建docker镜像
9. docker run -d --name fastrunner -p8000:5000 --restart always fastrunner:latest  # 后台运行docker容器,默认后台端口5000
10. docker exec -it fastrunner /bin/sh  #进入容器内部
    python3 manage.py makemigrations 
    python3 manage.py migrate 
11. 直接访问后台接口查看是否部署成功
``` 

```

## 本地开发环境部署
##### 命令均在FastRunner根目录下执行
``` bash
1. pip install -r requirements.txt 安装依赖库
2. 建立自己所需的myconfig.conf文件，参数见FasterRunner/setting.py文件
3. 若在本地用mysql，则需要安装mysql server，并创建NAME指定的database
4. python manage.py makemigrations 生成数据库迁移文件
5. python manage.py migrate 应用生成的库文件
6. python3 manage.py createsuperuser  # 按提示创建一个超级用户
7. python manage.py runserver 开发环境启动服务
8. 安装rabbmitMQ中间件，并配置setting中的BROKER_URL（默认一般不用修改）
9. celery -A FasterRunner worker -l info 启动异步worker
10. python manage.py celery beat -l info  启动beat监听定时任务
```

##### 其他注意点
- Windows环境安装mysqlclient可能需要先安装Microsoft Visual c++ 14.0,然后在 https://www.lfd.uci.edu/~gohlke/pythonlibs/ 此链接下找自己需要的windows安装包
- 如果提示：No module named 'djcelery' ，再执行一遍 pip install django-celery==3.2.2
- 如果提示： ValueError: Unable to configure handler 'default': [Errno 2] No such file or directory: 'mypath\\FasterRunner\\logs\\debug.log' , 手动创建FasterRunner\\logs\\debug.log
- 下载rabbmitMQ所需的erlang时，在官网下载很慢，可以访问 https://www.erlang-solutions.com/resources/download.html，windows配置参考：https://blog.csdn.net/qq_31634461/article/details/79377256
- ubuntu 安装py3.6缺少包参考：https://blog.csdn.net/kunagisatomo_i/article/details/81177558
- xadmin后台添加小组件报错，注释掉python包里的：/site-packages/django/forms/boundfield.py中的大概93行  ```#renderer=self.form.renderer```
- 如果测试用例运行结果数据比较大的话，更改mysql配置文件[mysqld]：max_allowed_packet=1073741824; 这是1G的大小。
- 项目中途更新用户表：https://www.caktusgroup.com/blog/2019/04/26/how-switch-custom-django-user-model-mid-project/