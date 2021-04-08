from django.forms import ModelForm
from crm.models import FlightPlan, Flight


class FlightPlanForm(ModelForm):
    class Meta:
        model = FlightPlan
        fields = "__all__"


class FlightForm(ModelForm):
    class Meta:
        model = Flight
        fields = "__all__"

