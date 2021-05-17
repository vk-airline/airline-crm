from django.utils import timezone


def time_now(request):
    return {'now': timezone.now()}
