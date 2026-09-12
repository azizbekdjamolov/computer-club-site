from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import (
    Computer,
    Customer,
    Expense,
    Payment,
    Reservation,
    Room,
    Session,
    Setting,
)


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'number', 'description', 'hourly_price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1-xona'}),
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hourly_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not kwargs.get('data'):
            self.fields['hourly_price'].initial = Setting.get_settings().default_hourly_price


class ComputerForm(forms.ModelForm):
    class Meta:
        model = Computer
        fields = ['room', 'name', 'status', 'description', 'is_active']
        widgets = {
            'room': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PC-01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'phone', 'note']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ali Valiyev'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '998901234567'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'description', 'created_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'created_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_at'].initial = timezone.localtime().strftime('%Y-%m-%dT%H:%M')


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'note']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount is None or amount <= 0:
            raise ValidationError('Summa musbat son bo\'lishi kerak')
        return amount


class QuickSessionForm(forms.Form):
    customer_name = forms.CharField(
        max_length=200, widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Mijoz ismi'}
        ), label='Mijoz ismi'
    )
    phone = forms.CharField(
        max_length=30, required=False, widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': '998901234567'}
        ), label='Telefon'
    )
    # Optional existing customer pk
    customer_pk = forms.IntegerField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'] = forms.ModelChoiceField(
            queryset=Room.objects.filter(is_active=True),
            widget=forms.Select(attrs={'class': 'form-control'}),
            label='Xona',
        )
        self.fields['computer'] = forms.ModelChoiceField(
            queryset=Computer.objects.filter(is_active=True),
            widget=forms.Select(attrs={'class': 'form-control'}),
            label='Kompyuter',
        )
        self.fields['start_time'] = forms.DateTimeField(
            required=False,
            widget=forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            label='Boshlanish vaqti',
        )
        self.fields['duration_minutes'] = forms.IntegerField(
            min_value=1, required=False,
            widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120'}),
            label='Davomiylik (daqiqa)',
        )
        self.fields['planned_end_time'] = forms.DateTimeField(
            required=False,
            widget=forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            label='Tugash vaqti',
        )
        self.fields['paid_amount'] = forms.DecimalField(
            min_value=0, required=False,
            widget=forms.NumberInput(attrs={'class': 'form-control'}),
            label='To\'lov',
        )

    def clean(self):
        cleaned = super().clean()
        room = cleaned.get('room')
        computer = cleaned.get('computer')
        if room and computer and computer.room_id != room.pk:
            self.add_error('computer', 'Tanlangan kompyuter bu xonaga tegishli emas')
        return cleaned


class SessionDetailForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['start_time', 'planned_end_time', 'actual_end_time', 'duration_minutes',
                  'calculation_method', 'note']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'planned_end_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'actual_end_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'calculation_method': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['customer', 'room', 'computer', 'start_time', 'end_time', 'status', 'note']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'computer': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['computer'].queryset = Computer.objects.filter(is_active=True)


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['club_name', 'currency', 'default_hourly_price', 'late_fee',
                  'dark_mode', 'auto_refresh_interval', 'default_calculation_method',
                  'notification_minutes_before_end', 'price_increase_after_minutes',
                  'increased_hourly_price']
        widgets = {
            'club_name': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'default_hourly_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'late_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_refresh_interval': forms.NumberInput(attrs={'class': 'form-control'}),
            'default_calculation_method': forms.Select(attrs={'class': 'form-control'}),
            'notification_minutes_before_end': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_increase_after_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'increased_hourly_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }
