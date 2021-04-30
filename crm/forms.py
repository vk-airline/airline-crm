from django.forms import ModelForm
from crm.models import FlightPlan, Flight
from django import forms
from multiselectfield import MultiSelectFormField


class FlightPlanForm(ModelForm):
    class Meta:
        model = FlightPlan
        fields = "__all__"
        widgets = {
            'planning_departure_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'HH:MM:SS',
                'required': True,
            }),
            'planning_arrival_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'HH:MM:SS',
                'required': True,
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD',
                'required': True,
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD',
                'required': True,
            }),
            'flight_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '**-***',
                'required': True,
            }),
            'passanger_capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'days_of_week': forms.CheckboxSelectMultiple(attrs={}),
            "description": forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'readonly': ''}),
            'source': forms.Select(attrs={'class': 'form-control'}),
            'destination': forms.Select(attrs={'class': 'form-control'}),

        }


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
