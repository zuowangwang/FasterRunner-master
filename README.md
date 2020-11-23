#### FasterRunner 后端部署

**一、安装python3**

```
安装包：Python-3.6.0.tgz
yum install gcc gcc-c++ zlib* openssl-devel-y
wget https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tgz
tar -zxvf Python-3.6.0.tgz -C /usr/local
mkdir /usr/local/python
cd /usr/local/Python-3.6.0
./configure --prefix=/usr/local/python --with-ssl
make && make install

#添加环境变量
echo PATH='/usr/local/python/bin/:$PATH' >> /etc/profile 
source /etc/profile
```


**二、mysql创建库及授权**

```
#创建数据库
create database FasterRunner1 default charset utf8 collate utf8_general_ci;

#授权
grant all privileges on FasterRunner1.* to 'faster'@'%' identified by 'faster@login';
flush privileges;

```

**三、安装和配置FasterRunner**

```
1. 解压安装包
unzip -d FasterRunner-master.zip /opt


2. 配置settings.py
vim /opt/FasterRunner-master/FasterRunner/settings.py #查看FasterRunner的配置文件
# 然后找到数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'FasterRunner1',
        'USER': 'faster',
        'PASSWORD': 'faster@login',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

3. 生成迁移表
python manage.py makemigrations  
4. 执行迁移数据
python manage.py migrate 
5. 按提示创建一个超级用户
python manage.py createsuperuser

6. FasterRunner 的后台静态文件
cp -r /opt/FasterRunner-master/static/xadmin /opt/FasterRunner-master/static/

注：后台访问http://127.0.0.1:8000/xadmin

7. 安装nginx（nginx 安装步骤此处不赘述）

配置文件如下：/opt/nginx/conf/conf.d/runner.conf

server {
    listen      8000;
    server_name 127.0.0.1;
    charset     utf-8;

    keepalive_timeout      1800s;
    client_header_timeout  1800s;
    client_body_timeout    1800s;
    proxy_connect_timeout  1800s;
    proxy_read_timeout     1800s;
    proxy_send_timeout     1800s;
    send_timeout           1800s;
    uwsgi_send_timeout     1800s;
    uwsgi_read_timeout     1800s;

    client_max_body_size 100M;
    location /media  {
        alias /opt/FasterRunner-master/media;
    }
    location /static {
        alias /opt/FasterRunner-master/static;

    }

    location / {
        include         uwsgi_params;
        uwsgi_pass      unix:/opt/FasterRunner-master/FasterRunner.sock;
    }
}


8. 修改 /opt/FasterRunner-master/uwsgi.ini 配置文件
# myweb_uwsgi.ini file
[uwsgi]

# Django-related settings
project = FasterRunner
base = /opt/FasterRunner-master


chdir = %(base)
module = %(project).wsgi:application


master = true
processes = 4


socket = %(base)/%(project).sock
chmod-socket = 666
vacuum = true


9. FasterRunner的启动与停止

脚本: /opt/FasterRunner-master/runner.sh

#!/usr/bin/env bash

dir=/opt/FasterRunner-master
prog=FasterRunner

# start nginx service
#service nginx restart

start() {
    echo -n $"Starting $prog "
# start celery worker
    celery multi start w1 -A FasterRunner -l info --logfile=./logs/worker.log
# start celery beat
    nohup python3 manage.py celery beat -l info > ./logs/beat.log 2>&1 &
# start fastrunner
    nohup uwsgi --ini ./uwsgi.ini 2>&1 &
}
 
stop() {
    echo -n $"Stopping $prog "
    pid=$(cat $dir/w1.pid)
    kill $pid
    killall -s INT /usr/local/python/bin/python3
    killall -s INT /usr/local/python/bin/uwsgi
    retval=$?
    echo
    [ $retval -eq 0 ]
    return $retval
}
 
restart() {
    stop
    sleep 3
    start
}
 
 
case "$1" in
    start)
        $1
        ;;
    stop)
        $1
        ;;
    restart)
        $1
        ;;
    *)
        echo $"Usage: $0 {start|stop|restart}"
        exit 2
esac



```

**四、FasterRunner 的启动与停止**
```
/opt/FasterRunner-master/

启动： /opt/FasterRunner-master/runner.sh start

停止： /opt/FasterRunner-master/runner.sh stop
```


#### FasterWeb 前端部署

**一、安装和配置node，pm2**
```
1.下载node文件
wget https://nodejs.org/dist/v9.8.0/node-v9.8.0-linux-x64.tar.xz

2. 解压安装包
xz -d node-v9.8.0-linux-x64.tar.xz
tar -xvf node-v9.8.0-linux-x64.tar -C /opt

3. 进入解压后的目录
cd /opt/node-v9.8.0-linux-x64

4. 创建node 软链
ln -s /opt/node-v9.8.0-linux-x64/bin/node /usr/local/bin/node 
ln -s /opt/node-v9.8.0-linux-x64/bin/npm /usr/local/bin/npm

5. 安装配置pm2
npm install -g pm2
ln -s /opt/node-v9.8.0-linux-x64/bin/pm2 /usr/sbin/pm2
```

**二、安装和配置 FasterWeb**

```
1. 解压安装包
tar xf FasterRunner-master.tar.gz -C /opt

2. 配置Django访问信息
# 设置baseUrl(用来访问Django后端,所以端口号需要和Django所在的ip和端口号一致)
# 编辑配置文件
vim /opt/FasterWeb-master/src/restful/api.js

#export const baseUrl = '"http://ip:端口号";'
export const baseUrl = 'http://127.0.0.1:8000';


3. 配置前端访问ip
vim  /opt/FasterWeb-master/config/index.js
#host : 本机公网ip或者内网ip
host: '127.0.0.1',

4. 安装依赖
# 进入FastWeb根目录
cd FasterWeb-master
# 安装依赖
npm instal

5. 启动服务
# pm2启动node服务 需要在FasterWeb-master 根目录下执行
pm2 start npm --watch --name fasterweb -- run start

# 查看pm2运行服务的状态
pm2 list

┌─────┬──────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
│ id  │ name         │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
├─────┼──────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
│ 0   │ fasterweb    │ default     │ N/A     │ fork    │ 24102    │ 4D     │ 11   │ online    │ 0.2%     │ 42.4mb   │ root     │ enabled  │
└─────┴──────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┴──────────┴──────────┴──────────┘


6. 重启服务命令
pm2 restart fasterweb
```

**windows 本地开发**

```
数据库启动：           net start mysql                       （管理员cmd输入启动）
MQ服务异步启动： RabbitMQ Service - start  （启动栏管理员右键启动）
node启动：          npm run dev  前端服务
后台启动：           python manage.py runserver  
异步处理启动：     celery -A FasterRunner worker -l info  > ./logs/beat.log
日志监控启动：     python manage.py celery beat -l info  > ./logs/worker.log
```

**访问：http://127.0.0.1:8080/fastrunner/login  localhost:8000/admin**

