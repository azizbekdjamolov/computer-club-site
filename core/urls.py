from django.contrib.auth import views as auth_views
from django.urls import path

from core import views

urlpatterns = [
    # Auth
    path('login/', auth_views.LoginView.as_view(
        template_name='core/auth/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('search/', views.search, name='search'),
    path('rooms/<int:room_pk>/computers/', views.room_computers, name='room_computers'),

    # Rooms
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<int:pk>/edit/', views.room_update, name='room_update'),
    path('rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),

    # Computers
    path('computers/', views.computer_list, name='computer_list'),
    path('computers/create/', views.computer_create, name='computer_create'),
    path('computers/<int:pk>/edit/', views.computer_update, name='computer_update'),
    path('computers/<int:pk>/delete/', views.computer_delete, name='computer_delete'),

    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Sessions
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/active/', views.active_sessions, name='active_sessions'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/quick/', views.quick_start, name='quick_start'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:pk>/edit/', views.session_update, name='session_update'),
    path('sessions/<int:pk>/stop/', views.session_stop, name='session_stop'),
    path('sessions/<int:pk>/cancel/', views.session_cancel, name='session_cancel'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('sessions/<int:session_pk>/payments/add/', views.payment_add, name='payment_add'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),

    # Reservations
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/create/', views.reservation_create, name='reservation_create'),
    path('reservations/<int:pk>/edit/', views.reservation_update, name='reservation_update'),
    path('reservations/<int:pk>/delete/', views.reservation_delete, name='reservation_delete'),

    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_update, name='expense_update'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),

    # Reports / Settings
    path('reports/', views.reports, name='reports'),
    path('settings/', views.settings_view, name='settings'),
]
