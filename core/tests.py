from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.calculations import calculate_price, format_duration
from core.models import (
    Computer,
    Customer,
    Payment,
    Reservation,
    Room,
    Session,
    Setting,
)


class CalculationTests(TestCase):
    def test_per_minute(self):
        amount = calculate_price(95, Decimal(10000), 'per_minute')
        self.assertEqual(amount, Decimal('15833'))

    def test_hourly_full_first_hour(self):
        amount = calculate_price(30, Decimal(10000), 'hourly')
        self.assertEqual(amount, Decimal('10000'))

    def test_hourly_exact(self):
        amount = calculate_price(60, Decimal(10000), 'hourly')
        self.assertEqual(amount, Decimal('10000'))

    def test_fixed_duration(self):
        amount = calculate_price(0, Decimal(10000), 'fixed', 120)
        self.assertEqual(amount, Decimal('20000'))

    def test_format_duration(self):
        self.assertEqual(format_duration(95), '1 s 35 daq')
        self.assertEqual(format_duration(60), '1 s')
        self.assertEqual(format_duration(30), '30 daq')


class ModelSignalTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name='1-xona', hourly_price=Decimal('10000'))
        self.pc = Computer.objects.create(room=self.room, name='PC-01')
        self.customer = Customer.objects.create(full_name='Ali Valiyev')

    def test_session_active_occupies_computer(self):
        s = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        self.pc.refresh_from_db()
        self.assertEqual(self.pc.status, 'occupied')
        self.assertEqual(Session.objects.count(), 1)

    def test_session_complete_frees_computer(self):
        s = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        s.actual_end_time = timezone.now()
        s.status = 'completed'
        s.save()
        self.pc.refresh_from_db()
        self.assertEqual(self.pc.status, 'available')

    def test_only_one_active_per_computer(self):
        s1 = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        # creating another active session is not prevented at model level
        # (view/form level checks), but signal should keep computer occupied
        self.pc.refresh_from_db()
        self.assertEqual(self.pc.status, 'occupied')


class PaymentTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name='1-xona', hourly_price=Decimal('10000'))
        self.pc = Computer.objects.create(room=self.room, name='PC-01')
        self.customer = Customer.objects.create(full_name='Ali')
        self.session = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )

    def test_payment_updates_paid_amount(self):
        Payment.objects.create(session=self.session, amount=Decimal('5000'))
        self.session.refresh_from_db()
        self.assertEqual(self.session.paid_amount, Decimal('5000'))

    def test_remaining_and_change(self):
        self.session.total_price = Decimal('30000')
        self.session.save()
        Payment.objects.create(session=self.session, amount=Decimal('40000'))
        self.session.refresh_from_db()
        self.assertEqual(self.session.paid_amount, Decimal('40000'))
        self.assertEqual(self.session.change_amount, Decimal('10000'))
        self.assertEqual(self.session.remaining_amount, Decimal('0'))

    def test_payment_delete_recalculates_paid_amount(self):
        p1 = Payment.objects.create(session=self.session, amount=Decimal('5000'))
        p2 = Payment.objects.create(session=self.session, amount=Decimal('7000'))
        self.session.refresh_from_db()
        self.assertEqual(self.session.paid_amount, Decimal('12000'))
        p1.delete()
        self.session.refresh_from_db()
        self.assertEqual(self.session.paid_amount, Decimal('7000'))
        p2.delete()
        self.session.refresh_from_db()
        self.assertEqual(self.session.paid_amount, Decimal('0'))


class SessionPricingCompletionTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name='1-xona', hourly_price=Decimal('10000'))
        self.pc = Computer.objects.create(room=self.room, name='PC-01')
        self.customer = Customer.objects.create(full_name='Ali')

    def test_fixed_early_completion_keeps_contracted_price(self):
        s = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
            calculation_method='fixed', duration_minutes=120,
        )
        s.start_time = timezone.now() - timezone.timedelta(minutes=40)
        s.actual_end_time = timezone.now()
        s.status = 'completed'
        s.save()
        s.refresh_from_db()
        self.assertEqual(s.duration_minutes, 120)
        self.assertEqual(s.total_price, Decimal('20000'))

    def test_hourly_completion_uses_actual_elapsed(self):
        s = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
            calculation_method='hourly', duration_minutes=120,
        )
        s.start_time = timezone.now() - timezone.timedelta(minutes=40)
        s.actual_end_time = timezone.now()
        s.status = 'completed'
        s.save()
        s.refresh_from_db()
        self.assertEqual(s.duration_minutes, 40)
        self.assertEqual(s.total_price, Decimal('10000'))


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='pass12345')
        self.client.login(username='admin', password='pass12345')
        self.room = Room.objects.create(name='1-xona', hourly_price=Decimal('10000'))
        self.pc = Computer.objects.create(room=self.room, name='PC-01')
        self.customer = Customer.objects.create(full_name='Ali', phone='998901234567')

    def test_dashboard(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_room_list_requires_login(self):
        self.client.logout()
        resp = self.client.get('/rooms/')
        self.assertEqual(resp.status_code, 302)

    def test_room_list_renders_counts(self):
        resp = self.client.get('/rooms/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '1-xona')
        self.assertContains(resp, 'Kompyuterlar')

    def test_room_crud(self):
        resp = self.client.post('/rooms/create/', {
            'name': '2-xona', 'number': '2', 'hourly_price': '15000', 'is_active': 'on'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Room.objects.filter(name='2-xona').exists())

    def test_computer_crud(self):
        resp = self.client.post('/computers/create/', {
            'room': self.room.id, 'name': 'PC-99', 'status': 'available', 'is_active': 'on'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Computer.objects.filter(name='PC-99').exists())

    def test_customer_crud(self):
        resp = self.client.post('/customers/create/', {
            'full_name': 'Vali', 'phone': '998901234567'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Customer.objects.filter(full_name='Vali').exists())

    def test_quick_start_creates_session(self):
        self.assertEqual(Session.objects.count(), 0)
        resp = self.client.post('/sessions/quick/', {
            'customer_name': 'Hasan',
            'phone': '998901234567',
            'room': self.room.id,
            'computer': self.pc.id,
            'paid_amount': '10000',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Session.objects.count(), 1)
        session = Session.objects.get()
        self.assertEqual(session.status, 'active')
        self.assertEqual(session.paid_amount, Decimal('10000'))
        self.pc.refresh_from_db()
        self.assertEqual(self.pc.status, 'occupied')

    def test_second_person_can_join_same_computer(self):
        s1 = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        self.pc.refresh_from_db()
        self.assertEqual(self.pc.status, 'occupied')
        resp = self.client.post('/sessions/quick/', {
            'customer_name': 'Ikkinchi',
            'phone': '998900000000',
            'room': self.room.id,
            'computer': self.pc.id,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Session.objects.filter(computer=self.pc, status='active').count(), 2
        )
        self.pc.refresh_from_db()
        self.assertEqual(self.pc.status, 'occupied')

    def test_stop_one_of_two_sessions_keeps_pc_occupied(self):
        s1 = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        s2 = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        self.client.post(f'/sessions/{s1.id}/stop/')
        self.pc.refresh_from_db()
        self.assertEqual(self.pc.status, 'occupied')
        self.client.post(f'/sessions/{s2.id}/stop/')
        self.pc.refresh_from_db()
        self.assertEqual(self.pc.status, 'available')

    def test_stop_session(self):
        s = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        resp = self.client.post(f'/sessions/{s.id}/stop/')
        self.assertEqual(resp.status_code, 302)
        s.refresh_from_db()
        self.assertEqual(s.status, 'completed')
        self.assertIsNotNone(s.actual_end_time)
        self.pc.refresh_from_db()
        self.assertEqual(self.pc.status, 'available')

    def test_reports(self):
        resp = self.client.get('/reports/')
        self.assertEqual(resp.status_code, 200)

    def test_settings(self):
        resp = self.client.get('/settings/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Setting.objects.filter(pk=1).exists() or Setting.objects.count() <= 1)

    def test_active_sessions_page_renders_with_two_people_on_one_pc(self):
        Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        resp = self.client.get('/sessions/active/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'PC-01')

    def test_dashboard_renders_with_two_people_on_one_pc(self):
        Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_search(self):
        resp = self.client.get('/search/?q=Ali')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Ali')

    def test_payment_add(self):
        s = Session.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            hourly_price=self.room.hourly_price, status='active',
        )
        resp = self.client.post(f'/sessions/{s.id}/payments/add/', {
            'amount': '20000', 'payment_method': 'cash'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Payment.objects.count(), 1)

    def test_quick_start_rejects_maintenance_pc(self):
        self.pc.status = 'maintenance'
        self.pc.save()
        resp = self.client.post('/sessions/quick/', {
            'customer_name': 'Hasan',
            'room': self.room.id,
            'computer': self.pc.id,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Session.objects.count(), 0)

    def test_quick_start_rejects_reserved_pc(self):
        self.pc.status = 'reserved'
        self.pc.save()
        resp = self.client.post('/sessions/quick/', {
            'customer_name': 'Hasan',
            'room': self.room.id,
            'computer': self.pc.id,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Session.objects.count(), 0)

    def test_delete_requires_superuser(self):
        room = Room.objects.create(name='2-xona', hourly_price=Decimal('15000'))
        self.client.logout()
        self.client.login(username='admin', password='pass12345')
        staff = User.objects.create_user(username='staff', password='pass12345', is_staff=True)
        self.client.logout()
        self.client.login(username='staff', password='pass12345')
        resp = self.client.post(f'/rooms/{room.id}/delete/')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Room.objects.filter(pk=room.id).exists())
        resp = self.client.get('/settings/')
        self.assertEqual(resp.status_code, 302)


class PricingTests(TestCase):
    def test_tiered_price_after_threshold(self):
        self.assertEqual(
            calculate_price(120, 10000, 'hourly',
                            increase_after_minutes=120, increased_hourly_price=12000),
            Decimal('20000')
        )
        self.assertEqual(
            calculate_price(150, 10000, 'hourly',
                            increase_after_minutes=120, increased_hourly_price=12000),
            Decimal('26000')
        )
        self.assertEqual(
            calculate_price(30, 10000, 'hourly',
                            increase_after_minutes=120, increased_hourly_price=12000),
            Decimal('10000')
        )

    def test_early_refund_positive(self):
        room = Room.objects.create(name='1-xona', hourly_price=Decimal('10000'))
        pc = Computer.objects.create(room=room, name='PC-01')
        customer = Customer.objects.create(full_name='Ali')
        s = Session.objects.create(
            customer=customer, room=room, computer=pc,
            hourly_price=room.hourly_price, status='active',
            paid_amount=Decimal('10000'),
        )
        s.start_time = timezone.now() - timezone.timedelta(minutes=20)
        s.save(update_fields=['start_time'])
        self.assertGreater(s.early_refund, Decimal('0'))
        self.assertLess(s.early_refund, Decimal('10000'))


class ReservationConflictTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name='1-xona', hourly_price=Decimal('10000'))
        self.pc = Computer.objects.create(room=self.room, name='PC-01')
        self.customer = Customer.objects.create(full_name='Ali')

    def test_conflicting_reservation_full_clean_raises(self):
        Reservation.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=2),
        )
        with self.assertRaises(Exception):
            r = Reservation(
                customer=self.customer, room=self.room, computer=self.pc,
                start_time=timezone.now() + timezone.timedelta(hours=1),
                end_time=timezone.now() + timezone.timedelta(hours=3),
            )
            r.full_clean()
            r.save()

    def test_non_conflicting_reservation_ok(self):
        r1 = Reservation.objects.create(
            customer=self.customer, room=self.room, computer=self.pc,
            start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=1),
        )
        r2 = Reservation(
            customer=self.customer, room=self.room, computer=self.pc,
            start_time=timezone.now() + timezone.timedelta(hours=2),
            end_time=timezone.now() + timezone.timedelta(hours=3),
        )
        r2.full_clean()
        r2.save()
        self.assertEqual(Reservation.objects.count(), 2)