from django.urls import path
from rest_framework import routers
from user.views import


app_name = 'user'
router = routers.DefaultRouter()
# router.register(r'specializations', SpecializationViewSet, basename='specialization')
# router.register(r'doctors', DoctorViewSet, basename='doctor')

urlpatterns = [
    #path('', ListBulkCreateSlotsApiView.as_view(), name='bulk-create-slots'),
]
urlpatterns += router.urls
"""
 POST: users/ - register a new user
 POST: users/token/ - get JWT tokens
 POST: users/token/refresh/ - refresh JWT token
 GET: users/me/ - get my profile info
 PUT/PATCH: users/me/ - update profile info
"""
