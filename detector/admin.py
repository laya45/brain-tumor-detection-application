from django.contrib import admin
from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "predicted_class",
        "confidence",
        "created_at",
    )

    list_filter = (
        "user",
        "predicted_class",
        "created_at",
    )

    search_fields = (
        "user__username",
        "predicted_class",
    )