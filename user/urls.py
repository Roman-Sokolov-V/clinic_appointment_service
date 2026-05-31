from django.urls import path, include
from rest_framework import routers
from .views import GoogleLogin, ManageUserView

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
# /users/token/
    # Отримання пари JWT-токенів (Access та Refresh) за допомогою звичайного логіна та пароля.
    # Фронтенд відправляє {username, password}, а у відповідь отримує токени для доступу до захищених ендпоінтів.
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', ManageUserView.as_view(), name='me'),
    # КРИТИЧНО ВАЖЛИВИЙ ЕНДПОІНТ ДЛЯ GOOGLE OAUTH.
    # Саме сюди твій фронтенд (або в нашому випадку Postman/скрипт) відправляє отриманий від Google "code".
    # View-клас GoogleLogin бере цей код, сам у фоні міняє його на Access Token від Google,
    # створює/знаходить юзера в базі даних Django і повертає тобі фінальні JWT-токени твого власного сайту.
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    # /users/auth/... (наприклад: /users/auth/logout/, /users/auth/user/)
    # Набір стандартних REST-ендпоінтів від бібліотеки `dj_rest_auth`.
    # Забезпечує базові операції авторизації через API: безпечний вихід із системи (logout з інвалідацією токенів),
    # скидання пароля через email тощо.
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
