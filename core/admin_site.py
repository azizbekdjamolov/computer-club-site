from django.contrib.admin import AdminSite


class ClubAdminSite(AdminSite):
    site_header = 'Cyber Club — Boshqaruv paneli'
    site_title = 'Cyber Club Admin'
    index_title = 'Boshqaruv paneli'

    def has_permission(self, request):
        """Faqat superuserlar admin panelga kirishi mumkin."""
        return request.user.is_active and request.user.is_superuser


club_admin_site = ClubAdminSite(name='admin')