from django.utils import timezone

from core.models import Computer, Customer, Reservation, Session, Setting


def site_settings(request):
    settings = Setting.get_settings()
    data = {
        'site_settings': settings,
        'active_sessions_count': None,
        'notifications': [],
    }
    if request.path.startswith('/admin'):
        return data

    data['active_sessions_count'] = Session.objects.filter(status='active').count()
    data['notifications'] = build_notifications(settings)
    return data


def build_notifications(settings):
    """Muhim holatlar uchun notificationlar qurish."""
    notifications = []
    now = timezone.now()

    # Sessiya tugashiga X daqiqa qoldi (planned end yaqinlashganlar)
    threshold = settings.notification_minutes_before_end
    active_sessions = Session.objects.filter(status='active')
    for s in active_sessions:
        if s.planned_end_time:
            diff = s.planned_end_time - now
            seconds = diff.total_seconds()
            if 0 < seconds <= threshold * 60:
                notifications.append({
                    'type': 'info',
                    'icon': 'clock',
                    'message': (
                        f'{s.computer.name} sessiyasi tugashiga '
                        f'{int(seconds // 60)} daqiqa qoldi ({s.customer.full_name})'
                    ),
                    'link': f'/sessions/{s.pk}/',
                })
        # To'lov yetarli emas
        if s.paid_amount < s.total_price:
            notifications.append({
                'type': 'warning',
                'icon': 'alert',
                'message': (
                    f'{s.computer.name}: {s.customer.full_name} qarzdor '
                    f'({s.remaining_amount} {settings.currency})'
                ),
                'link': f'/sessions/{s.pk}/',
            })

    # Ertangi rezervatsiyalar
    upcoming = Reservation.objects.filter(
        status='pending',
        start_time__gte=now,
        start_time__lte=now + timezone.timedelta(hours=1),
    )
    for r in upcoming:
        notifications.append({
            'type': 'success',
            'icon': 'calendar',
            'message': (
                f'Rezervatsiya vaqti keldi: {r.computer.name} - {r.customer.full_name} '
                f'({r.start_time:%H:%M})'
            ),
            'link': f'/reservations/',
        })

    return notifications[:15]
