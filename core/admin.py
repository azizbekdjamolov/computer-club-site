from django.contrib import admin
from django.db.models import Count, Q, Sum
from django.utils import timezone

from core.admin_site import club_admin_site

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


@admin.register(Room, site=club_admin_site)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'number', 'hourly_price', 'computers_count', 'occupied_count', 'is_active']
    list_editable = ['is_active']
    search_fields = ['name', 'number']
    list_filter = ['is_active']
    ordering = ['id']
    list_per_page = 25


@admin.register(Computer, site=club_admin_site)
class ComputerAdmin(admin.ModelAdmin):
    list_display = ['name', 'room', 'status', 'is_active']
    list_editable = ['status', 'is_active']
    list_filter = ['room', 'status', 'is_active']
    search_fields = ['name', 'room__name']
    ordering = ['room', 'id']
    list_per_page = 50


@admin.register(Customer, site=club_admin_site)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'sessions_count', 'total_spent', 'created_at']
    search_fields = ['full_name', 'phone']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _sessions=Count('sessions', distinct=True),
            _spent=Sum(
                'sessions__total_price',
                filter=Q(sessions__status='completed'),
                distinct=True,
            ),
        )

    @admin.display(description='Tashriflar', ordering='_sessions')
    def sessions_count(self, obj):
        return obj._sessions

    @admin.display(description='Jami sarf', ordering='_spent')
    def total_spent(self, obj):
        return obj._spent or 0


@admin.register(Session, site=club_admin_site)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'computer', 'room', 'start_time', 'total_price',
                    'paid_amount', 'remaining_amount', 'status']
    readonly_fields = ['total_price', 'paid_amount', 'remaining_amount', 'change_amount',
                       'current_duration']
    list_filter = ['status', 'calculation_method', 'room', 'created_at']
    search_fields = ['customer__full_name', 'computer__name', 'room__name']
    ordering = ['-start_time']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['customer', 'room', 'computer']
    list_per_page = 50

    @admin.display(description='Qolgan', ordering='total_price')
    def remaining_amount(self, obj):
        return max(obj.total_price - obj.paid_amount, 0)

    @admin.display(description='Qaytim')
    def change_amount(self, obj):
        return max(obj.paid_amount - obj.total_price, 0)

    @admin.display(description='O\'tgan vaqt')
    def current_duration(self, obj):
        return obj.current_duration_minutes()


@admin.register(Payment, site=club_admin_site)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['amount', 'payment_method', 'session', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['session__customer__full_name', 'session__computer__name']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50


@admin.register(Reservation, site=club_admin_site)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['customer', 'computer', 'room', 'start_time', 'end_time', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['customer__full_name', 'computer__name']
    ordering = ['-start_time']
    date_hierarchy = 'created_at'
    list_per_page = 50
    autocomplete_fields = ['customer', 'room', 'computer']


@admin.register(Expense, site=club_admin_site)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50


@admin.register(Setting, site=club_admin_site)
class SettingAdmin(admin.ModelAdmin):
    list_display = ['club_name', 'currency', 'default_hourly_price', 'dark_mode',
                    'auto_refresh_interval']