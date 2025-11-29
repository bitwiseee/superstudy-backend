"""
URL configuration for superstudy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="SuperStudy API",
        default_version='v1',
        description="""
        # SuperStudy Platform API Documentation
        
        AI-powered learning platform for African students with gamification features.
        
        ## Features
        - 📄 Document upload and processing (PDF, PPTX, TXT)
        - 📝 AI-powered summaries with key points
        - 🃏 Flashcard generation for study
        - 📝 Interactive quizzes with scoring
        - 💬 Q&A chat with documents
        - 🔊 Text-to-speech in multiple languages
        - 🌍 Multi-language support (English, Yoruba, Igbo, Hausa)
        - 🏆 Gamification (points, levels, badges, leaderboard)
        
        ## Authentication
        All endpoints (except leaderboard) require authentication using:
        - Basic Authentication
        - Session Authentication (via Django admin login)
        
        ## Getting Started
        1. Create an account via Django admin
        2. Click "Authorize" button below
        3. Enter your username and password
        4. Try out the endpoints!
        
        ## Support
        - Base URL: `http://localhost:8000/api/`
        - Admin Panel: `http://localhost:8000/admin/`
        """
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core_app.urls')),
    
    # OpenAPI/Swagger URLs
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    re_path(r'^api/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site headers
admin.site.site_header = "SuperStudy Administration"
admin.site.site_title = "SuperStudy Admin"
admin.site.index_title = "Welcome to SuperStudy Admin Panel"