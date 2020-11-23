# RENDERBUS



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

##### 其他注意点
- windows 本地开发
- 数据库启动：           net start mysql                       （管理员cmd输入启动）
- MQ服务异步启动： RabbitMQ Service - start  （启动栏管理员右键启动）
- node启动：          npm run dev  前端服务
- 后台启动：           python manage.py runserver  #python manage.py runserver 192.168.3.27:8080
- 异步处理启动：     celery -A FasterRunner worker -l info  > ./logs/beat.log
- 日志监控启动：     python manage.py celery beat -l info  > ./logs/worker.log








 