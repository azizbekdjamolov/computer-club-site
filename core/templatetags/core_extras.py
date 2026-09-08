from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key, '')


@register.filter
def status_label(status):
    labels = {
        'available': "Bo'sh",
        'occupied': 'Band',
        'reserved': 'Rezerv',
        'maintenance': 'Nosoz',
        'active': 'Faol',
        'completed': 'Tugagan',
        'cancelled': 'Bekor qilingan',
        'pending': 'Kutilmoqda',
    }
    return labels.get(status, status)


@register.filter
def method_label(method):
    labels = {
        'hourly': 'Soatlik',
        'per_minute': 'Har daqiqada',
        'fixed': 'Belgilangan muddat',
    }
    return labels.get(method, method)


@register.filter
def payment_method_label(m):
    labels = {
        'cash': 'Naqd', 'card': 'Karta', 'click': 'Click',
        'payme': 'Payme', 'uzcard': 'UzCard', 'humo': 'Humo',
    }
    return labels.get(m, m)


@register.filter
def money(value):
    try:
        return f'{value:,.0f}'.replace(',', ' ')
    except (TypeError, ValueError):
        return value