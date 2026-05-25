from django.urls import path, include
from rest_framework import routers
from .views import GoogleLogin

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from clinic.views import SpecializationViewSet

app_name = 'user'
router = routers.DefaultRouter()
# router.register(r'specializations', SpecializationViewSet, basename='specialization')
# router.register(r'doctors', DoctorViewSet, basename='doctor')



urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    #path('me/', ######, name='me'),
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('auth/', include('dj_rest_auth.urls')), # Стандартні ендпоінти (logout, user)

]
urlpatterns += router.urls
"""
 POST: users/ - register a new user
 POST: users/token/ - get JWT tokens
 POST: users/token/refresh/ - refresh JWT token
 GET: users/me/ - get my profile info
 PUT/PATCH: users/me/ - update profile info
"""
