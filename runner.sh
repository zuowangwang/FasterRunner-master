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
    nohup uwsgi --ini ./uwsgi.ini > ./logs/uwsgi.log 2>&1 &
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

