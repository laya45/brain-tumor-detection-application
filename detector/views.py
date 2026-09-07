from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from .models import Prediction
from .ml_models import predict_image


# =========================================================
# AUTH CHOICE
# =========================================================

def auth_choice(request):

    if request.user.is_authenticated:
        return redirect("home")

    return render(
        request,
        "detector/auth_choice.html"
    )


# =========================================================
# REGISTER
# =========================================================

def register(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        # Password confirmation
        if password != password2:

            return render(
                request,
                "detector/register.html",
                {
                    "error": "Passwords do not match."
                }
            )

        # Check username
        if User.objects.filter(username=username).exists():

            return render(
                request,
                "detector/register.html",
                {
                    "error": "Username already exists."
                }
            )

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password
        )

        # Login automatically
        login(request, user)

        return redirect("home")

    return render(
        request,
        "detector/register.html"
    )


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("home")

        return render(
            request,
            "detector/login.html",
            {
                "error": "Invalid username or password."
            }
        )

    return render(
        request,
        "detector/login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@login_required
def logout_view(request):

    logout(request)

    return redirect("auth_choice")


# =========================================================
# HOME / MRI PREDICTION
# =========================================================

@login_required
def home(request):

    # -----------------------------
    # GET REQUEST
    # -----------------------------

    if request.method == "GET":

        return render(
            request,
            "detector/home.html"
        )

    # -----------------------------
    # POST REQUEST
    # -----------------------------

    if request.method == "POST":

        upload_file = request.FILES.get("mri_image")

        # No image uploaded
        if not upload_file:

            return render(
                request,
                "detector/home.html",
                {
                    "error": "Please select an MRI image."
                }
            )

        # Create database record
        prediction_record = Prediction.objects.create(

            user=request.user,

            image=upload_file,

            predicted_class="Processing",

            confidence=0.0,

            glioma_probability=0.0,

            meningioma_probability=0.0,

            no_tumor_probability=0.0,

            pituitary_tumor_probability=0.0,
        )

        # Get saved image path
        image_path = prediction_record.image.path

        # Run ML prediction
        result = predict_image(image_path)

        probabilities = result["probabilities"]

        # Update prediction record
        prediction_record.predicted_class = (
            result["predicted_class"]
        )

        prediction_record.confidence = (
            result["confidence"]
        )

        prediction_record.glioma_probability = (
            probabilities["Glioma"]
        )

        prediction_record.meningioma_probability = (
            probabilities["Meningioma"]
        )

        prediction_record.no_tumor_probability = (
            probabilities["No Tumor"]
        )

        prediction_record.pituitary_tumor_probability = (
            probabilities["Pituitary Tumor"]
        )

        prediction_record.save()

        # Display result
        return render(
            request,
            "detector/home.html",
            {
                "uploaded": True,

                "file_path": prediction_record.image.url,

                "prediction": result["predicted_class"],

                "confidence": round(
                    result["confidence"] * 100,
                    2
                ),

                "glioma": round(
                    probabilities["Glioma"] * 100,
                    2
                ),

                "meningioma": round(
                    probabilities["Meningioma"] * 100,
                    2
                ),

                "no_tumor": round(
                    probabilities["No Tumor"] * 100,
                    2
                ),

                "pituitary_tumor": round(
                    probabilities["Pituitary Tumor"] * 100,
                    2
                ),
            }
        )


# =========================================================
# PREDICTION HISTORY
# =========================================================

@login_required
def history(request):

    # Get only the logged-in user's predictions
    predictions = Prediction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    # Create a display value for confidence
    #
    # Database:
    # 0.9915
    #
    # Website:
    # 99.15%
    #
    for prediction in predictions:

        prediction.confidence_display = round(
            prediction.confidence * 100,
            2
        )

    return render(
        request,
        "detector/history.html",
        {
            "predictions": predictions
        }
    )


# =========================================================
# PREDICTION DETAIL
# =========================================================

@login_required
def prediction_detail(request, prediction_id):

    # Make sure the prediction belongs
    # to the currently logged-in user
    prediction_record = get_object_or_404(
        Prediction,
        id=prediction_id,
        user=request.user
    )

    return render(
        request,
        "detector/prediction_detail.html",
        {
            "prediction": prediction_record
        }
    )