from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path("profile/", views.profile_view, name="profile"),

    # Auth (já usa os templates do app usuarios/registration)
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
]
