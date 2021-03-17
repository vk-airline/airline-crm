from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse


# Create your views here.
from django.shortcuts import render


@login_required
def index(request):
    return render(request, "index.html")


@permission_required('crm.view_aircraft')
def aircrafts_view(request):
    return HttpResponse("Aircrafts list")


@permission_required('crm.view_aircraftdevicelife')
def aircrafts_devices(request):
    return HttpResponse("Aircrafts devices list")
