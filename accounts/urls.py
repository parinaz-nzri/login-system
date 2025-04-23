from django.urls import path
from .views import VerifyCodeView, SendCodeView, LoginView, RegisterView

urlpatterns = [
    path('request-otp/', SendCodeView.as_view()),
    path('verify-otp/', VerifyCodeView.as_view()),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
]
