from decimal import ROUND_HALF_UP, Decimal


def calculate_price(minutes, hourly_price, method='hourly', fixed_minutes=0,
                    increase_after_minutes=0, increased_hourly_price=0):
    """
    Narxni hisoblash.
    method: 'hourly' -> real vaqtdan, 'per_minute' -> daqiqalik, 'fixed' -> belgilangan muddat.
    increase_after_minutes: necha daqiqadan keyin narx oshadi (0 = oshmaydi).
    increased_hourly_price: shu vaqtdan keyingi soatlik narx.
    Returns Decimal.
    """
    hourly_price = Decimal(hourly_price if hourly_price is not None else 0)
    minutes = int(minutes or 0)
    increased_hourly_price = Decimal(increased_hourly_price or 0)
    increase_after_minutes = int(increase_after_minutes or 0)

    if increase_after_minutes <= 0 or increased_hourly_price <= 0:
        increase_after_minutes = 0
        increased_hourly_price = Decimal(0)

    if method == 'per_minute':
        per_minute = hourly_price / Decimal(60)
        return (per_minute * Decimal(minutes)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    if method == 'fixed':
        fixed_minutes = int(fixed_minutes or 0)
        if fixed_minutes <= 0:
            return Decimal(0)
        return _calc_hourly(fixed_minutes, hourly_price,
                            increase_after_minutes, increased_hourly_price)

    # default: hourly
    return _calc_hourly(minutes, hourly_price,
                        increase_after_minutes, increased_hourly_price)


def calculate_used_price(minutes, hourly_price,
                         increase_after_minutes=0, increased_hourly_price=0):
    """
    Amalda ishlatilgan vaqt narxi (1-soat minimumisiz, daqiqabay).
    Erta ketishda qaytimni aniq hisoblash uchun ishlatiladi.
    Returns Decimal.
    """
    minutes = int(minutes or 0)
    if minutes <= 0:
        return Decimal(0)
    increase_after_minutes = int(increase_after_minutes or 0)
    increased_hourly_price = Decimal(increased_hourly_price or 0)
    if increase_after_minutes <= 0 or increased_hourly_price <= 0:
        increase_after_minutes = 0
        increased_hourly_price = Decimal(0)

    base_rate = Decimal(hourly_price)
    per_minute_base = base_rate / Decimal(60)
    if not increase_after_minutes:
        return (per_minute_base * Decimal(minutes)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    t1 = min(minutes, increase_after_minutes)
    extra = minutes - t1
    seg1 = per_minute_base * Decimal(t1)
    seg2 = Decimal(0)
    if extra > 0:
        seg2 = (increased_hourly_price / Decimal(60)) * Decimal(extra)
    return (seg1 + seg2).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def _calc_hourly(minutes, base_rate, increase_after_minutes, increased_rate):
    """Soatlik hisob: 1 soatdan kam -> to'liq birinchi soat. Qolgani darajali."""
    base_rate = Decimal(base_rate)
    minutes = int(minutes)
    increase_after_minutes = int(increase_after_minutes or 0)
    increased_rate = Decimal(increased_rate or 0)

    if minutes <= 0:
        return Decimal(0)

    # 1 soatdan kam -> bitta to'liq soat narxi
    if minutes < 60:
        return base_rate

    per_minute_base = base_rate / Decimal(60)
    if not increase_after_minutes or not increased_rate:
        return (per_minute_base * Decimal(minutes)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    t1 = min(minutes, increase_after_minutes)
    extra = minutes - t1
    seg1 = per_minute_base * Decimal(t1)
    seg2 = Decimal(0)
    if extra > 0:
        seg2 = (increased_rate / Decimal(60)) * Decimal(extra)
    return (seg1 + seg2).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


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