
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin  # Ensure you import admin
from llmpredictor.views import home  # Import the home view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('llmpredictor/', include('llmpredictor.urls')),
    path('', home),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
