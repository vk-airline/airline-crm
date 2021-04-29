from django.forms import ModelForm
from crm.models import FlightPlan, Flight
from django import forms


class FlightPlanForm(ModelForm):
    class Meta:
        model = FlightPlan
        fields = "__all__"


class FlightForm(ModelForm):
    class Meta:
        model = Flight
        fields = "__all__"
        widgets = {
            'planning_departure_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD HH:MM:SS',
                'required': True,
            }),
            'planning_arrival_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD HH:MM:SS',
                'required': True,
            }),
            'actual_departure_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD HH:MM:SS',
            }),
            'actual_arrival_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD HH:MM:SS',
            }),
            'flight_plan': forms.Select(attrs={'class': 'form-control'}),
            'aircraft': forms.Select(attrs={'class': 'form-control'}),
            'actual_destination': forms.Select(attrs={'class': 'form-control'}),
            'employees': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'}),
        }
