from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.calculations import calculate_price, format_duration


class Room(models.Model):
    name = models.CharField(max_length=100, verbose_name='Xona nomi')
    number = models.CharField(max_length=20, blank=True, verbose_name='Raqam')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    hourly_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=10000, verbose_name='Soatlik narx'
    )
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan')

    class Meta:
        ordering = ['id']
        verbose_name = 'Xona'
        verbose_name_plural = 'Xonalar'

    def __str__(self):
        number = f' {self.number}' if self.number else ''
        return f'{self.name}{number}'

    def computers_count(self):
        return self.computers.count()

    def occupied_count(self):
        return self.computers.filter(status='occupied').count()

    computers_count.short_description = 'Kompyuterlar'
    occupied_count.short_description = 'Band'


class Computer(models.Model):
    STATUS_CHOICES = [
        ('available', 'Bo\'sh'),
        ('occupied', 'Band'),
        ('reserved', 'Rezerv'),
        ('maintenance', 'Nosoz'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='computers')
    name = models.CharField(max_length=50, verbose_name='Nomi')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='Holat'
    )
    description = models.TextField(blank=True, verbose_name='Tavsif')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['room', 'id']
        unique_together = [['room', 'name']]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['room', 'status']),
        ]
        verbose_name = 'Kompyuter'
        verbose_name_plural = 'Kompyuterlar'

    def __str__(self):
        return f'{self.name} ({self.room})'

    def get_status_display_color(self):
        return {
            'available': 'green',
            'occupied': 'red',
            'reserved': 'yellow',
            'maintenance': 'gray',
        }.get(self.status, 'gray')


class Customer(models.Model):
    full_name = models.CharField(max_length=200, verbose_name='Ism familiya')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Telefon')
    note = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mijoz'
        verbose_name_plural = 'Mijozlar'

    def __str__(self):
        return self.full_name

    def total_spent(self):
        return sum(
            s.total_price for s in self.sessions.filter(status='completed')
        )

    def total_paid(self):
        return sum(
            s.paid_amount for s in self.sessions.filter(status='completed')
        )

    def total_debt(self):
        return sum(
            s.remaining_amount for s in self.sessions.filter(status='completed')
        )

    def sessions_count(self):
        return self.sessions.count()

    total_spent.short_description = 'Jami sarf'
    sessions_count.short_description = 'Tashriflar'


class Session(models.Model):
    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('completed', 'Tugagan'),
        ('cancelled', 'Bekor qilingan'),
    ]

    CALCULATION_METHOD_CHOICES = [
        ('hourly', "Soatlik (real vaqt)"),
        ('per_minute', 'Har daqiqada'),
        ('fixed', 'Belgilangan muddat'),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='sessions'
    )
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='sessions')
    computer = models.ForeignKey(
        Computer, on_delete=models.PROTECT, related_name='sessions'
    )
    start_time = models.DateTimeField(default=timezone.now, verbose_name='Boshlanish')
    planned_end_time = models.DateTimeField(
        null=True, blank=True, verbose_name='Rejalashtirilgan tugash'
    )
    actual_end_time = models.DateTimeField(
        null=True, blank=True, verbose_name='Amalda tugash'
    )
    paused_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Pauza (boshlangan)'
    )
    duration_minutes = models.IntegerField(
        default=0, verbose_name='Vaqt (daqiqa)'
    )
    calculation_method = models.CharField(
        max_length=20, choices=CALCULATION_METHOD_CHOICES,
        default='hourly', verbose_name='Hisoblash usuli'
    )
    hourly_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Soatlik narx"
    )
    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name='Jami narx'
    )
    paid_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name='To\'langan'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Holat'
    )
    note = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_time']),
            models.Index(fields=['computer', 'status']),
            models.Index(fields=['customer']),
        ]
        verbose_name = 'Sessiya'
        verbose_name_plural = 'Sessiyalar'

    def __str__(self):
        return f'{self.customer} - {self.computer} ({self.start_time:%d.%m %H:%M})'

    @property
    def remaining_amount(self):
        return max(self.total_price - self.paid_amount, 0)

    @property
    def change_amount(self):
        """Ortiqcha to'lov (qaytim)"""
        if self.paid_amount > self.total_price:
            return self.paid_amount - self.total_price
        return 0

    @property
    def is_overpaid(self):
        return self.paid_amount > self.total_price

    @property
    def is_paused(self):
        return self.status == 'active' and self.paused_at is not None

    def toggle_pause(self):
        """Pauza berish / davom ettirish. Davom ettirilganda start_time shifflashadi."""
        now = timezone.now()
        if self.paused_at:
            paused_duration = now - self.paused_at
            self.start_time = self.start_time + paused_duration
            self.paused_at = None
        else:
            self.paused_at = now
        self.save()

    def current_duration_minutes(self):
        if self.status == 'active':
            return int((timezone.now() - self.start_time).total_seconds() // 60)
        if self.actual_end_time and self.start_time:
            return int((self.actual_end_time - self.start_time).total_seconds() // 60)
        return 0

    def current_total_price(self):
        minutes = self.current_duration_minutes()
        return calculate_price(
            minutes, self.hourly_price, self.calculation_method, self.duration_minutes
        )

    def update_from_payments(self):
        total_paid = sum(p.amount for p in self.payments.all())
        self.paid_amount = total_paid
        self.save(update_fields=['paid_amount'])

    def calculate_price(self, minutes=None):
        if minutes is None:
            minutes = self.current_duration_minutes()
        return calculate_price(
            minutes, self.hourly_price, self.calculation_method, self.duration_minutes
        )

    def save(self, *args, **kwargs):
        if not self.hourly_price and self.room:
            self.hourly_price = self.room.hourly_price
        if self.status == 'completed' and self.actual_end_time:
            minutes = int(
                (self.actual_end_time - self.start_time).total_seconds() // 60
            )
            self.duration_minutes = minutes
            self.total_price = self.calculate_price(minutes)
        super().save(*args, **kwargs)


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('click', 'Click'),
        ('payme', 'Payme'),
        ('uzcard', 'UzCard'),
        ('humo', 'Humo'),
    ]

    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Summa'
    )
    payment_method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, default='cash',
        verbose_name='To\'lov usuli'
    )
    note = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'

    def __str__(self):
        return f'{self.amount} - {self.session}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.session.update_from_payments()


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('active', 'Faol'),
        ('completed', 'Tugagan'),
        ('cancelled', 'Bekor qilingan'),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='reservations'
    )
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='reservations')
    computer = models.ForeignKey(
        Computer, on_delete=models.PROTECT, related_name='reservations'
    )
    start_time = models.DateTimeField(verbose_name='Boshlanish')
    end_time = models.DateTimeField(verbose_name='Tugash')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Holat'
    )
    note = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['computer', 'status']),
        ]
        verbose_name = 'Rezervatsiya'
        verbose_name_plural = 'Rezervatsiyalar'

    def __str__(self):
        return f'{self.customer} - {self.computer} ({self.start_time:%d.%m %H:%M})'

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('Tugash vaqti boshlanish vaqtidan keyin bo\'lishi kerak')
        conflicts = Reservation.objects.filter(
            computer=self.computer,
            status__in=['pending', 'active'],
        ).exclude(pk=self.pk)
        for r in conflicts:
            if not (self.end_time <= r.start_time or self.start_time >= r.end_time):
                raise ValidationError(
                    f'Bu vaqt uchun kompyuter allaqachon rezerv qilingan '
                    f'({r.customer}) {r.start_time:%H:%M} - {r.end_time:%H:%M}'
                )


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('electricity', 'Elektr'),
        ('internet', 'Internet'),
        ('repair', 'Ta\'mirlash'),
        ('salary', 'Ish haqi'),
        ('rent', 'Ijara'),
        ('other', 'Boshqa'),
    ]

    title = models.CharField(max_length=200, verbose_name='Sarlavha')
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Summa'
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default='other',
        verbose_name='Kategoriya'
    )
    description = models.TextField(blank=True, verbose_name='Tavsif')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['category']),
        ]
        verbose_name = 'Xarajat'
        verbose_name_plural = 'Xarajatlar'

    def __str__(self):
        return f'{self.title} - {self.amount}'

    def get_category_display_color(self):
        return {
            'electricity': 'warning',
            'internet': 'info',
            'repair': 'danger',
            'salary': 'primary',
            'rent': 'secondary',
            'other': 'dark',
        }.get(self.category, 'dark')


class Setting(models.Model):
    club_name = models.CharField(max_length=200, default='Cyber Club', verbose_name='Klub nomi')
    currency = models.CharField(max_length=20, default='UZS', verbose_name='Valyuta')
    default_hourly_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=10000, verbose_name='Standart soatlik narx'
    )
    late_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Kechikish uchun qo\'shimcha to\'lov'
    )
    dark_mode = models.BooleanField(default=True, verbose_name='Dark mode')
    auto_refresh_interval = models.IntegerField(
        default=15, verbose_name='Avto yangilash (sekund)'
    )
    default_calculation_method = models.CharField(
        max_length=20, choices=Session.CALCULATION_METHOD_CHOICES,
        default='hourly', verbose_name='Standart hisoblash usuli'
    )
    notification_minutes_before_end = models.IntegerField(
        default=10, verbose_name='Tugashga necha daqiqa qolganda ogohlantirish'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sozlama'
        verbose_name_plural = 'Sozlamalar'

    def __str__(self):
        return self.club_name

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
