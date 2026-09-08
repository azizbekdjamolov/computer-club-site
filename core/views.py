import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.calculations import calculate_price, format_duration
from core.forms import (
    ComputerForm,
    CustomerForm,
    ExpenseForm,
    PaymentForm,
    QuickSessionForm,
    ReservationForm,
    RoomForm,
    SessionDetailForm,
    SettingForm,
)
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


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _day_range(day=None):
    if day is None:
        day = timezone.localdate()
    start = timezone.make_aware(datetime.combine(day, time.min))
    end = start + timedelta(days=1)
    return start, end


def _sum(qs, field):
    return qs.aggregate(v=Coalesce(Sum(field), Decimal('0')))['v'] or 0


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _get_computers_for_room(room_id):
    return Computer.objects.filter(room_id=room_id, is_active=True)


# ----------------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------------

@login_required
def dashboard(request):
    settings = Setting.get_settings()
    today_start, today_end = _day_range()
    now = timezone.now()

    sessions_today = Session.objects.filter(
        start_time__gte=today_start, start_time__lt=today_end
    )
    completed_today = sessions_today.filter(status='completed')

    revenue_today = _sum(completed_today, 'total_price')
    paid_today = _sum(completed_today, 'paid_amount')
    expenses_today = _sum(
        Expense.objects.filter(created_at__gte=today_start, created_at__lt=today_end),
        'amount',
    )
    net_profit = revenue_today - expenses_today

    customers_today = sessions_today.values('customer').distinct().count()
    computers = Computer.objects.filter(is_active=True)
    total_computers = computers.count()
    # Active sessions fetched once with related objects
    active_sessions = Session.objects.filter(status='active').select_related('customer', 'computer')
    active_count = active_sessions.count()
    occupied_computers = computers.filter(status='occupied').count()
    free_computers = computers.filter(status='available').count()

    debtors = []
    active_map = {}
    for s in active_sessions:
        active_map[s.computer_id] = s
        if s.remaining_amount > 0:
            debtors.append({'session': s, 'remaining': s.remaining_amount})

    # Rooms grouped with computers
    rooms = Room.objects.filter(is_active=True).prefetch_related('computers')

    # Recent activity
    recent_sessions = Session.objects.select_related(
        'customer', 'computer', 'room'
    ).order_by('-created_at')[:8]

    # Upcoming reservations
    upcoming_res = Reservation.objects.filter(
        status='pending', start_time__gte=now
    ).order_by('start_time')[:8]

    context = {
        'settings': settings,
        'revenue_today': revenue_today,
        'paid_today': paid_today,
        'expenses_today': expenses_today,
        'net_profit': net_profit,
        'customers_today': customers_today,
        'total_computers': total_computers,
        'occupied_count': occupied_computers,
        'free_count': free_computers,
        'active_count': active_count,
        'debtors': debtors,
        'rooms': rooms,
        'active_session_map': active_map,
        'recent_sessions': recent_sessions,
        'upcoming_res': upcoming_res,
        'quick_form': QuickSessionForm(),
        'active_page': 'dashboard',
    }
    return render(request, 'core/dashboard.html', context)


# ----------------------------------------------------------------------------
# Rooms
# ----------------------------------------------------------------------------

@login_required
def room_list(request):
    rooms = Room.objects.all().prefetch_related('computers')
    return render(request, 'core/rooms/list.html', {'rooms': rooms, 'active_page': 'rooms'})


@login_required
def room_create(request):
    form = RoomForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Xona qo\'shildi')
        return redirect('room_list')
    return render(request, 'core/rooms/form.html', {'form': form, 'title': 'Yangi xona'})


@login_required
def room_update(request, pk):
    room = get_object_or_404(Room, pk=pk)
    form = RoomForm(request.POST or None, instance=room)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Xona yangilandi')
        return redirect('room_list')
    return render(request, 'core/rooms/form.html', {'form': form, 'title': 'Xonani tahrirlash'})


@login_required
@require_POST
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    room.delete()
    messages.success(request, 'Xona o\'chirildi')
    return redirect('room_list')


# ----------------------------------------------------------------------------
# Computers
# ----------------------------------------------------------------------------

@login_required
def computer_list(request):
    computers = Computer.objects.select_related('room').all()
    room_filter = request.GET.get('room')
    status_filter = request.GET.get('status')
    if room_filter:
        computers = computers.filter(room_id=room_filter)
    if status_filter:
        computers = computers.filter(status=status_filter)
    rooms = Room.objects.all()
    return render(request, 'core/computers/list.html', {
        'computers': computers, 'rooms': rooms, 'active_page': 'computers',
    })


@login_required
def computer_create(request):
    form = ComputerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Kompyuter qo\'shildi')
        return redirect('computer_list')
    return render(request, 'core/computers/form.html', {'form': form, 'title': 'Yangi kompyuter'})


@login_required
def computer_update(request, pk):
    computer = get_object_or_404(Computer, pk=pk)
    form = ComputerForm(request.POST or None, instance=computer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Kompyuter yangilandi')
        return redirect('computer_list')
    return render(request, 'core/computers/form.html', {'form': form, 'title': 'Kompyuterni tahrirlash'})


@login_required
@require_POST
def computer_delete(request, pk):
    computer = get_object_or_404(Computer, pk=pk)
    computer.delete()
    messages.success(request, 'Kompyuter o\'chirildi')
    return redirect('computer_list')


# ----------------------------------------------------------------------------
# Customers
# ----------------------------------------------------------------------------

@login_required
def customer_list(request):
    customers = Customer.objects.annotate(
        s_count=Count('sessions')
    ).order_by('-created_at')
    q = request.GET.get('q')
    if q:
        customers = customers.filter(full_name__icontains=q)
    paginator = Paginator(customers, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/customers/list.html', {
        'customers': page, 'active_page': 'customers', 'q': q,
    })


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sessions = customer.sessions.select_related('computer', 'room').order_by('-start_time')
    total_minutes = sum(
        s.duration_minutes for s in sessions if s.status == 'completed'
    )
    return render(request, 'core/customers/detail.html', {
        'customer': customer, 'sessions': sessions, 'total_minutes': total_minutes,
        'active_page': 'customers',
    })


@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Mijoz qo\'shildi')
        return redirect('customer_list')
    return render(request, 'core/customers/form.html', {'form': form, 'title': 'Yangi mijoz'})


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Mijoz yangilandi')
        return redirect('customer_detail', pk=customer.pk)
    return render(request, 'core/customers/form.html', {'form': form, 'title': 'Mijozni tahrirlash'})


@login_required
@require_POST
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    messages.success(request, 'Mijoz o\'chirildi')
    return redirect('customer_list')


# ----------------------------------------------------------------------------
# Sessions
# ----------------------------------------------------------------------------

@login_required
def session_list(request):
    sessions = Session.objects.select_related('customer', 'computer', 'room').all()
    status = request.GET.get('status')
    q = request.GET.get('q')
    if status:
        sessions = sessions.filter(status=status)
    if q:
        sessions = sessions.filter(customer__full_name__icontains=q)
    paginator = Paginator(sessions.order_by('-start_time'), 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/sessions/list.html', {
        'sessions': page, 'active_page': 'sessions',
        'current_status': status, 'q': q,
    })


@login_required
def active_sessions(request):
    sessions = Session.objects.filter(status='active').select_related(
        'customer', 'computer', 'room'
    ).order_by('start_time')
    return render(request, 'core/sessions/active.html', {
        'sessions': sessions, 'active_page': 'active-sessions',
        'now': timezone.now(),
    })


@login_required
def session_detail(request, pk):
    session = get_object_or_404(
        Session.objects.select_related('customer', 'computer', 'room', ), pk=pk
    )
    payments = session.payments.all()
    remaining = session.remaining_amount
    context = {
        'session': session,
        'payments': payments,
        'remaining': remaining,
        'change': session.change_amount,
        'active_page': 'sessions',
    }
    if session.status == 'active':
        context['payment_form'] = PaymentForm()
        context['detail_form'] = SessionDetailForm(instance=session)
    return render(request, 'core/sessions/detail.html', context)


@login_required
def session_create(request):
    """Oddiy sessiya yaratish (tanlangan mijoz/xona/kompyuter bilan)."""
    if request.method == 'POST':
        customer_pk = request.POST.get('customer')
        room_pk = request.POST.get('room')
        computer_pk = request.POST.get('computer')
        customer = Customer.objects.filter(pk=customer_pk).first()
        computer = Computer.objects.filter(pk=computer_pk).first()
        room = Room.objects.filter(pk=room_pk).first()
        if not customer or not computer or not room:
            messages.error(request, 'Mijoz, xona va kompyuterni to\'ldiring')
            return redirect('session_create')
        if computer.status == 'occupied':
            messages.error(request, 'Bu kompyuter band')
            return redirect('session_create')
        if computer.room_id != room.pk:
            messages.error(request, 'Kompyuter tanlangan xonaga tegishli emas')
            return redirect('session_create')

        start_str = request.POST.get('start_time')
        start = None
        if start_str:
            try:
                naive = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
                start = timezone.make_aware(naive)
            except ValueError:
                start = None
        if not start:
            start = timezone.now()

        duration = _to_int(request.POST.get('duration_minutes'))
        planned_str = request.POST.get('planned_end_time')
        planned = None
        if planned_str:
            try:
                planned = timezone.make_aware(datetime.strptime(planned_str, '%Y-%m-%dT%H:%M'))
            except ValueError:
                planned = None
        if not planned and duration:
            planned = start + timedelta(minutes=duration)

        settings = Setting.get_settings()
        method = request.POST.get('calculation_method', settings.default_calculation_method)
        session = Session.objects.create(
            customer=customer,
            room=room,
            computer=computer,
            start_time=start,
            planned_end_time=planned,
            duration_minutes=duration,
            calculation_method=method,
            hourly_price=room.hourly_price,
            status='active',
            note=request.POST.get('note', ''),
        )
        session.save()  # triggers signal -> computer occupied

        paid = request.POST.get('paid_amount')
        if paid:
            try:
                paid_dec = Decimal(paid)
                if paid_dec > 0:
                    Payment.objects.create(session=session, amount=paid_dec, payment_method='cash')
            except Exception:
                pass
        messages.success(request, 'Sessiya boshlandi')
        return redirect('active_sessions')

    customers = Customer.objects.all()
    rooms = Room.objects.filter(is_active=True)
    context = {
        'customers': customers,
        'rooms': rooms,
        'active_page': 'sessions',
    }
    return render(request, 'core/sessions/create.html', context)


@login_required
def quick_start(request):
    """Tezkor mijoz qo'shish + sessiya boshlash."""
    if request.method == 'POST':
        form = QuickSessionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            settings = Setting.get_settings()

            customer = None
            if data.get('customer_pk'):
                customer = Customer.objects.filter(pk=data['customer_pk']).first()
            if not customer:
                customer = Customer.objects.create(
                    full_name=data['customer_name'],
                    phone=data.get('phone') or '',
                )
                messages.success(request, f'Mijoz qo\'shildi: {customer.full_name}')

            computer = data['computer']
            room = data['room']
            if computer.status == 'occupied':
                messages.error(request, 'Bu kompyuter band')
                return redirect('active_sessions')

            start = data.get('start_time') or timezone.now()
            if timezone.is_naive(start):
                start = timezone.make_aware(start)

            duration = data.get('duration_minutes') or 0
            planned = data.get('planned_end_time')
            if planned and timezone.is_naive(planned):
                planned = timezone.make_aware(planned)
            if not planned and duration:
                planned = start + timedelta(minutes=duration)

            session = Session.objects.create(
                customer=customer,
                room=room,
                computer=computer,
                start_time=start,
                planned_end_time=planned,
                duration_minutes=duration,
                calculation_method=settings.default_calculation_method,
                hourly_price=room.hourly_price,
                status='active',
            )
            # signal sets computer occupied

            paid = data.get('paid_amount')
            if paid:
                try:
                    paid_dec = Decimal(paid)
                    if paid_dec > 0:
                        Payment.objects.create(session=session, amount=paid_dec, payment_method='cash')
                except Exception:
                    pass

            messages.success(request, f'Sessiya boshlandi: {customer.full_name} - {computer.name}')
            return redirect('active_sessions')
        else:
            for field, errors in form.errors.items():
                for e in errors:
                    messages.error(request, f'{e}')
            return redirect('dashboard')

    return redirect('dashboard')


@login_required
@require_POST
def session_stop(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if session.status != 'active':
        messages.info(request, 'Sessiya avval tugatilgan')
        return redirect('active_sessions')
    session.actual_end_time = timezone.now()
    session.status = 'completed'
    session.save()
    messages.success(request, f'Sessiya tugatildi: {session.computer.name}')
    return redirect('active_sessions')


@login_required
@require_POST
def session_cancel(request, pk):
    session = get_object_or_404(Session, pk=pk)
    session.status = 'cancelled'
    session.actual_end_time = session.actual_end_time or timezone.now()
    session.save()
    messages.warning(request, 'Sessiya bekor qilindi')
    return redirect('active_sessions')


@login_required
def session_update(request, pk):
    session = get_object_or_404(Session, pk=pk)
    form = SessionDetailForm(request.POST or None, instance=session)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sessiya yangilandi')
        return redirect('session_detail', pk=session.pk)
    return render(request, 'core/sessions/form.html', {
        'form': form, 'session': session, 'active_page': 'sessions',
    })


# ----------------------------------------------------------------------------
# Payments
# ----------------------------------------------------------------------------

@login_required
def payment_list(request):
    payments = Payment.objects.select_related(
        'session__customer', 'session__computer'
    ).all()
    q = request.GET.get('q')
    if q:
        payments = payments.filter(session__customer__full_name__icontains=q)
    paginator = Paginator(payments.order_by('-created_at'), 30)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/payments/list.html', {
        'payments': page, 'active_page': 'payments', 'q': q,
    })


@login_required
@require_POST
def payment_add(request, session_pk):
    session = get_object_or_404(Session, pk=session_pk)
    form = PaymentForm(request.POST, session=session)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.session = session
        payment.save()
        messages.success(request, 'To\'lov qo\'shildi')
    else:
        for e in form.errors.values():
            for msg in e:
                messages.error(request, msg)
    return redirect('session_detail', pk=session.pk)


@login_required
@require_POST
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    session_pk = payment.session_id
    payment.delete()
    messages.success(request, 'To\'lov o\'chirildi')
    return redirect('session_detail', pk=session_pk)


# ----------------------------------------------------------------------------
# Reservations
# ----------------------------------------------------------------------------

@login_required
def reservation_list(request):
    reservations = Reservation.objects.select_related('customer', 'computer', 'room').all()
    status = request.GET.get('status')
    if status:
        reservations = reservations.filter(status=status)
    return render(request, 'core/reservations/list.html', {
        'reservations': reservations.order_by('-start_time'),
        'active_page': 'reservations', 'current_status': status,
    })


@login_required
def reservation_create(request):
    form = ReservationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        res = form.save(commit=False)
        try:
            res.full_clean()
            res.save()
            messages.success(request, 'Rezervatsiya qo\'shildi')
            return redirect('reservation_list')
        except Exception as e:
            for msg in getattr(e, 'messages', [str(e)]):
                messages.error(request, msg)
    return render(request, 'core/reservations/form.html', {
        'form': form, 'title': 'Yangi rezervatsiya', 'active_page': 'reservations',
    })


@login_required
def reservation_update(request, pk):
    res = get_object_or_404(Reservation, pk=pk)
    form = ReservationForm(request.POST or None, instance=res)
    if request.method == 'POST' and form.is_valid():
        try:
            obj = form.save(commit=False)
            obj.full_clean()
            obj.save()
            messages.success(request, 'Rezervatsiya yangilandi')
            return redirect('reservation_list')
        except Exception as e:
            for msg in getattr(e, 'messages', [str(e)]):
                messages.error(request, msg)
    return render(request, 'core/reservations/form.html', {
        'form': form, 'title': 'Rezervatsiyani tahrirlash', 'active_page': 'reservations',
    })


@login_required
@require_POST
def reservation_delete(request, pk):
    res = get_object_or_404(Reservation, pk=pk)
    res.delete()
    messages.success(request, 'Rezervatsiya o\'chirildi')
    return redirect('reservation_list')


# ----------------------------------------------------------------------------
# Expenses
# ----------------------------------------------------------------------------

@login_required
def expense_list(request):
    expenses = Expense.objects.all()
    category = request.GET.get('category')
    if category:
        expenses = expenses.filter(category=category)
    total = _sum(expenses, 'amount')
    paginator = Paginator(expenses.order_by('-created_at'), 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/expenses/list.html', {
        'expenses': page, 'active_page': 'expenses', 'total': total,
        'current_category': category,
    })


@login_required
def expense_create(request):
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Xarajat qo\'shildi')
        return redirect('expense_list')
    return render(request, 'core/expenses/form.html', {
        'form': form, 'title': 'Yangi xarajat', 'active_page': 'expenses',
    })


@login_required
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    form = ExpenseForm(request.POST or None, instance=expense)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Xarajat yangilandi')
        return redirect('expense_list')
    return render(request, 'core/expenses/form.html', {
        'form': form, 'title': 'Xarajatni tahrirlash', 'active_page': 'expenses',
    })


@login_required
@require_POST
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    messages.success(request, 'Xarajat o\'chirildi')
    return redirect('expense_list')


# ----------------------------------------------------------------------------
# Reports
# ----------------------------------------------------------------------------

@login_required
def reports(request):
    filter_key = request.GET.get('filter', 'today')
    now = timezone.now()
    today_start, today_end = _day_range()

    ranges = {
        'today': (today_start, today_end),
        'yesterday': (today_start - timedelta(days=1), today_start),
        'week': (today_start - timedelta(days=today_start.weekday()), timezone.now()),
        'month': (today_start.replace(day=1), timezone.now()),
    }

    custom_start = custom_end = None
    if filter_key == 'custom':
        cs = request.GET.get('start')
        ce = request.GET.get('end')
        if cs:
            try:
                start_d = date.fromisoformat(cs)
                custom_start = timezone.make_aware(datetime.combine(start_d, time.min))
            except ValueError:
                custom_start = today_start
        if ce:
            try:
                end_d = date.fromisoformat(ce)
                custom_end = timezone.make_aware(datetime.combine(end_d, time.max))
            except ValueError:
                custom_end = timezone.now()

    start, end = ranges.get(filter_key, (today_start, today_end))
    if filter_key == 'custom':
        start = custom_start or today_start
        end = custom_end or (custom_start + timedelta(days=1) if custom_start else timezone.now())

    sessions = Session.objects.filter(
        start_time__gte=start, start_time__lte=end
    )
    completed = sessions.filter(status='completed')

    total_sessions = sessions.count()
    total_customers = sessions.values('customer').distinct().count()
    total_revenue = _sum(completed, 'total_price')
    total_paid = _sum(completed, 'paid_amount')
    total_debt = total_revenue - total_paid

    total_minutes = completed.aggregate(v=Coalesce(Sum('duration_minutes'), 0))['v'] or 0

    top_room = (
        completed.values('room__name')
        .annotate(total=Coalesce(Sum('total_price'), Decimal('0')))
        .order_by('-total').first()
    )
    top_computer = (
        Session.objects.filter(status='completed', start_time__gte=start, start_time__lte=end)
        .values('computer__name')
        .annotate(count=Count('id'))
        .order_by('-count').first()
    )

    # Daily revenue chart (last 14 days) - single grouped query
    from django.db.models.functions import TruncDate

    fourteen_ago = now - timedelta(days=13)
    start_of_range, _ = _day_range(fourteen_ago.date())
    daily_qs = (
        Session.objects.filter(
            status='completed',
            start_time__gte=start_of_range,
        )
        .annotate(day=TruncDate('start_time'))
        .values('day')
        .annotate(rev=Coalesce(Sum('total_price'), Decimal('0')))
    )
    daily_map = {row['day']: float(row['rev']) for row in daily_qs}

    daily_revenue = []
    daily_labels = []
    for i in range(13, -1, -1):
        d = (now - timedelta(days=i)).date()
        daily_labels.append(d.strftime('%d.%m'))
        daily_revenue.append(daily_map.get(d, 0.0))

    # Revenue by room
    room_rev_qs = (
        completed.values('room__name')
        .annotate(rev=Coalesce(Sum('total_price'), Decimal('0')))
        .order_by('-rev')
    )
    room_revenue = list(room_rev_qs)

    # Usage by computer
    computer_usage = list(
        Session.objects.filter(status='completed', start_time__gte=start, start_time__lte=end)
        .values('computer__name', 'room__name')
        .annotate(count=Count('id'), minutes=Coalesce(Sum('duration_minutes'), 0))
        .order_by('-count')
    )

    # Expenses in range
    expenses = Expense.objects.filter(created_at__gte=start, created_at__lte=end)
    total_expenses = _sum(expenses, 'amount')

    context = {
        'filter': filter_key,
        'range_label': _range_label(filter_key, start, end),
        'total_sessions': total_sessions,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'total_paid': total_paid,
        'total_debt': total_debt,
        'total_minutes': total_minutes,
        'total_expenses': total_expenses,
        'net_profit': total_revenue - total_expenses,
        'top_room': top_room,
        'top_computer': top_computer,
        'daily_labels': json.dumps(daily_labels),
        'daily_revenue': json.dumps(daily_revenue),
        'room_revenue': json.dumps(room_revenue),
        'computer_usage': computer_usage,
        'custom_start': custom_start.strftime('%Y-%m-%d') if custom_start else '',
        'custom_end': custom_end.strftime('%Y-%m-%d') if custom_end else '',
        'active_page': 'reports',
    }
    return render(request, 'core/reports.html', context)


def _range_label(filter_key, start, end):
    fmt = '%d.%m.%Y'
    return {
        'today': 'Bugun',
        'yesterday': 'Kecha',
        'week': 'Bu hafta',
        'month': 'Bu oy',
    }.get(filter_key, f'{start.strftime(fmt)} - {end.strftime(fmt)}')


# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------

@login_required
def settings_view(request):
    settings = Setting.get_settings()
    form = SettingForm(request.POST or None, instance=settings)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sozlamalar saqlandi')
        return redirect('settings')
    return render(request, 'core/settings.html', {
        'form': form, 'active_page': 'settings',
    })


# ----------------------------------------------------------------------------
# Global search
# ----------------------------------------------------------------------------

@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    results = {
        'customers': [], 'computers': [], 'rooms': [], 'sessions': [],
    }
    if q:
        results['customers'] = Customer.objects.filter(
            full_name__icontains=q
        ) | Customer.objects.filter(phone__icontains=q)
        results['computers'] = Computer.objects.filter(name__icontains=q).select_related('room')
        results['rooms'] = Room.objects.filter(name__icontains=q)
        results['sessions'] = Session.objects.filter(
            customer__full_name__icontains=q
        ).select_related('customer', 'computer')[:10]
    return render(request, 'core/search.html', {
        'q': q, 'results': results, 'active_page': None,
    })


# AJAX endpoint: computers for a room (for quick session form)
@login_required
def room_computers(request, room_pk):
    from django.http import JsonResponse
    room = get_object_or_404(Room, pk=room_pk)
    computers = list(
        _get_computers_for_room(room.pk).values('id', 'name', 'status')
    )
    return JsonResponse({'computers': computers})
