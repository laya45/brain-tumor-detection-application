from django.db import models
from django.contrib.auth.models import User


class Prediction(models.Model):

    user = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name="predictions",
    null=True,
    blank=True
    )

    image = models.ImageField(
        upload_to="uploads/"
    )

    predicted_class = models.CharField(
        max_length=100
    )

    confidence = models.FloatField()

    glioma_probability = models.FloatField()

    meningioma_probability = models.FloatField()

    no_tumor_probability = models.FloatField()

    pituitary_tumor_probability = models.FloatField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

@property
def glioma_percentage(self):
    return round(self.glioma_probability * 100, 2)


@property
def meningioma_percentage(self):
    return round(self.meningioma_probability * 100, 2)


@property
def no_tumor_percentage(self):
    return round(self.no_tumor_probability * 100, 2)


@property
def pituitary_tumor_percentage(self):
    return round(self.pituitary_tumor_probability * 100, 2)

    def __str__(self):
        return self.predicted_class