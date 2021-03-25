import time

from celery import shared_task

@shared_task
def sleep(duration):
    time.sleep(duration)
    return None
