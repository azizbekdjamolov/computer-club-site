from django.contrib.admin import AdminSite
from django.shortcuts import redirect


class ClubAdminSite(AdminSite):
    site_header = 'Cyber Club — Boshqaruv paneli'
    site_title = 'Cyber Club Admin'
    index_title = 'Boshqaruv paneli'

    def index(self, request, extra_context=None):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().index(request, extra_context)


club_admin_site = ClubAdminSite(name='admin')