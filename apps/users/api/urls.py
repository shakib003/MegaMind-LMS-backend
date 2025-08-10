from django.urls import path
from apps.users.api.views import UserSignupView, UserLoginView

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
]