from django.contrib import admin
from django.contrib.flatpages.views import flatpage
from django.urls import include, path
from django.conf.urls import handler404, handler500
from django.conf import settings
from django.conf.urls.static import static

# noinspection PyRedeclaration
handler404 = "posts.views.page_not_found"
# noinspection PyRedeclaration
handler500 = "posts.views.server_error"

urlpatterns = [
    path("panel/admin/", admin.site.urls),
    path("auth/", include("users.urls")),
    path("auth/", include("django.contrib.auth.urls")),
]

urlpatterns += [
    path('about-author/', flatpage, {'url': '/about-author/'}, name='about_author'),
    path('about-spec/', flatpage, {'url': '/about-spec/'}, name='about_spec'),
    path("", include("posts.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
