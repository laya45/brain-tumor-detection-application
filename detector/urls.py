from django.urls import path
from . import views


urlpatterns = [

    # ==========================================
    # AUTH
    # ==========================================

    path(
        "auth/",
        views.auth_choice,
        name="auth_choice"
    ),

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "register/",
        views.register,
        name="register"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),


    # ==========================================
    # APPLICATION
    # ==========================================

    path(
        "",
        views.home,
        name="home"
    ),

    path(
        "history/",
        views.history,
        name="history"
    ),

    path(
        "prediction/<int:prediction_id>/",
        views.prediction_detail,
        name="prediction_detail"
    ),

]