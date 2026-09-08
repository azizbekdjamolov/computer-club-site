from django.contrib.admin import AdminSite


class ClubAdminSite(AdminSite):
    site_header = 'Cyber Club — Boshqaruv paneli'
    site_title = 'Cyber Club Admin'
    index_title = 'Boshqaruv paneli'


club_admin_site = ClubAdminSite(name='admin')