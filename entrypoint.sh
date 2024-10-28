#!/bin/bash
# Run Django server using Gunicorn
nohup gunicorn autograding_project.wsgi:application --bind 0.0.0.0:8007 \
    --access-logfile "/app/logs/gunicorn_access.log" \
    --access-logformat "%(h)s %({X-Real-IP}i)s %(D)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s" \
    --error-logfile "/app/logs/gunicorn_error.log" \
    --log-file "/app/logs/gunicorn_logs.log" \
    --log-level=info \ > "/app/logs/nohup_gunicorn.log" &
nohup celery -A autograding_project worker --loglevel=debug --pool=solo --logfile /app/logs/celery_logs.log > "/app/logs/nohup_celery.log"
