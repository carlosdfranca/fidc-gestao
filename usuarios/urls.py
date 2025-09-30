from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path("profile/", views.profile_view, name="profile"),
    path("otp/", views.otp_view, name="otp"),
    path("login/", views.login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

]
