from django.urls import include, path

from core.admin_site import club_admin_site

urlpatterns = [
    path('admin/', club_admin_site.urls),
    path('', include('core.urls')),
]