#!/usr/bin/env bash

dir=/opt/FasterRunner-master
prog=FasterRunner

# start nginx service
#service nginx restart


start() {
    echo -n $"Starting $prog "
# start nginx service
    service nginx restart
# start celery worker
    celery multi start w1 -A FasterRunner -l info --logfile=./logs/worker.log
# start celery beat
    nohup python3 manage.py celery beat -l info > ./logs/beat.log 2>&1 &
# start fastrunner
    nohup uwsgi --ini ./uwsgi.ini > ./logs/uwsgi.log 2>&1 &
# start flower
#    echo "start flower....."
    nohup celery flower --broker=amqp://guest:guest@127.0.0.1:5672// --address=0.0.0.0 --port=5555 > ./logs/flower.log 2>&1 &
}
 
stop() {
    echo -n $"Stopping $proag "
    pid=$(cat $dir/w1.pid)
    kill $pid
    killall -s INT /usr/local/python/bin/python3
    killall -s INT /usr/local/python/bin/uwsgi
    net=$(netstat -ntulp |grep 5555)
    p=$(echo $net |awk -F'LISTEN' '{print$2}' |awk -F'/' '{print $1}')
    kill -9 $p
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

