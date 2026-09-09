from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # AUTH
    # ========================================================

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

    # ========================================================
    # DASHBOARD
    # ========================================================

    path(
        "",
        views.home,
        name="home"
    ),

    # ========================================================
    # HISTORY
    # ========================================================

    path(
        "history/",
        views.history,
        name="history"
    ),

    # ========================================================
    # PREDICTION DETAIL
    # ========================================================

    path(
        "prediction/<int:prediction_id>/",
        views.prediction_detail,
        name="prediction_detail"
    ),

    # ========================================================
    # PRIVATE MRI IMAGE
    # ========================================================

    path(
        "prediction/<int:prediction_id>/image/",
        views.prediction_image,
        name="prediction_image"
    ),
]