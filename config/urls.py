"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clinic/', include("clinic.urls"), name='clinic'),
    path('users/', include("user.urls"), name='user'),
    # Внутрішні маршрути бібліотеки django-allauth.
    # Вони потрібні для обробки логіки соцмереж (OAuth-провайдерів), генерації правильних
    # redirect_uri (callback), верифікації email-адрес та зв'язку Google-акаунта з Django-юзером.
    path('accounts/', include('allauth.urls')),

    # Стандартні вбудовані візуальні сторінки Django для авторизації (вхід, вихід, зміна пароля).
    # Зазвичай у чистих API проєктах це використовується як запасний варіант або для тестування шаблонів.
    path('accounts/profile', include('django.contrib.auth.urls')),
    path('/', include('payment.urls'), name='payment'),
]
