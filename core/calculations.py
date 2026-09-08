from decimal import ROUND_HALF_UP, Decimal


def calculate_price(minutes, hourly_price, method='hourly', fixed_minutes=0):
    """
    Narxni hisoblash.
    method: 'hourly' -> real vaqtdan, 'per_minute' -> daqiqalik, 'fixed' -> belgilangan muddat.
    Returns Decimal.
    """
    hourly_price = Decimal(hourly_price if hourly_price is not None else 0)
    minutes = int(minutes or 0)

    if method == 'per_minute':
        per_minute = hourly_price / Decimal(60)
        return (per_minute * Decimal(minutes)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    if method == 'fixed':
        fixed_minutes = int(fixed_minutes or 0)
        if fixed_minutes <= 0:
            return Decimal(0)
        per_minute = hourly_price / Decimal(60)
        return (per_minute * Decimal(fixed_minutes)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    # default: hourly, ceil to hour? No - use exact minutes * per-minute rate
    if minutes <= 0:
        return Decimal(0)
    per_minute = hourly_price / Decimal(60)
    amount = (per_minute * Decimal(minutes)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    # 1 soatdan kam bo'lsa ham bitta to'liq soat deb hisoblash (typical policy)
    if minutes < 60 and amount < hourly_price:
        # Charge full first hour
        return hourly_price
    return amount


def format_duration(minutes):
    """Daqiqani soat-u daqiqa formatiga o'tkazish."""
    minutes = int(minutes or 0)
    h, m = divmod(minutes, 60)
    if h and m:
        return f'{h} s {m} daq'
    if h:
        return f'{h} s'
    return f'{m} daq'


def format_duration_hms(seconds):
    """Sekundni HH:MM:SS formatiga o'tkazish."""
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f'{h:02d}:{m:02d}:{s:02d}'


def humanize_amount(amount, currency='UZS'):
    amount = Decimal(amount or 0)
    formatted = f'{amount:,.0f}'.replace(',', ' ')
    return f'{formatted} {currency}'
