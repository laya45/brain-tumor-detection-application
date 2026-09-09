import os
import tempfile
import uuid

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from vercel.blob import BlobClient

from .models import Prediction
from .ml_models import predict_image


def auth_choice(request):
    if request.user.is_authenticated:
        return redirect("home")

    return render(request, "detector/auth_choice.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            return render(
                request,
                "detector/register.html",
                {"error": "Passwords do not match."}
            )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                "detector/register.html",
                {"error": "Username already exists."}
            )

        user = User.objects.create_user(
            username=username,
            password=password
        )

        login(request, user)

        return redirect("home")

    return render(request, "detector/register.html")


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
            {"error": "Invalid username or password."}
        )

    return render(request, "detector/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("auth_choice")


def upload_to_vercel_blob(upload_file):
    """
    Upload an uploaded MRI image to Vercel Blob.

    The Blob store is private, so the uploaded file is not
    publicly accessible without authentication/signed access.
    """

    original_name = upload_file.name

    extension = os.path.splitext(original_name)[1].lower()

    unique_filename = (
        f"mri/{uuid.uuid4().hex}{extension}"
    )

    temporary_path = None

    try:
        # Create a temporary file on the writable /tmp filesystem.
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            temporary_path = temp_file.name

            for chunk in upload_file.chunks():
                temp_file.write(chunk)

        # Create Vercel Blob client.
        client = BlobClient()

        # Upload to private Blob storage.
        blob = client.upload_file(
            temporary_path,
            unique_filename,
            access="private",
            content_type=upload_file.content_type or "application/octet-stream",
        )

        return blob

    finally:
        # Remove the temporary file after Blob upload.
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


@login_required
def home(request):

    if request.method == "GET":
        return render(
            request,
            "detector/home.html"
        )

    if request.method == "POST":

        upload_file = request.FILES.get("mri_image")

        if not upload_file:
            return render(
                request,
                "detector/home.html",
                {
                    "error": "Please select an MRI image."
                }
            )

        # Validate file type.
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/jpg",
            "image/webp",
        ]

        if upload_file.content_type not in allowed_types:
            return render(
                request,
                "detector/home.html",
                {
                    "error": (
                        "Invalid file type. "
                        "Please upload a JPG, JPEG, PNG, or WEBP image."
                    )
                }
            )

        # Vercel Functions have a 4.5 MB request-body limit
        # for server uploads.
        max_size = 4.5 * 1024 * 1024

        if upload_file.size > max_size:
            return render(
                request,
                "detector/home.html",
                {
                    "error": (
                        "Image is too large. "
                        "Please upload an image smaller than 4.5 MB."
                    )
                }
            )

        temporary_path = None

        try:

            # -------------------------------------------------
            # STEP 1: Save uploaded image temporarily
            # -------------------------------------------------

            extension = os.path.splitext(
                upload_file.name
            )[1].lower()

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension
            ) as temp_file:

                temporary_path = temp_file.name

                for chunk in upload_file.chunks():
                    temp_file.write(chunk)

            # -------------------------------------------------
            # STEP 2: Upload MRI to Vercel Blob
            # -------------------------------------------------

            blob_filename = (
                f"mri/{uuid.uuid4().hex}{extension}"
            )

            client = BlobClient()

            blob = client.upload_file(
                temporary_path,
                blob_filename,
                access="private",
                content_type=(
                    upload_file.content_type
                    or "application/octet-stream"
                ),
            )

            # -------------------------------------------------
            # STEP 3: Run TensorFlow prediction
            # -------------------------------------------------

            result = predict_image(
                temporary_path
            )

            probabilities = result["probabilities"]

            # -------------------------------------------------
            # STEP 4: Save prediction + Blob URL
            # -------------------------------------------------

            prediction_record = Prediction.objects.create(
                user=request.user,

                image_url=blob.url,

                predicted_class=result["predicted_class"],

                confidence=result["confidence"],

                glioma_probability=(
                    probabilities["Glioma"]
                ),

                meningioma_probability=(
                    probabilities["Meningioma"]
                ),

                no_tumor_probability=(
                    probabilities["No Tumor"]
                ),

                pituitary_tumor_probability=(
                    probabilities["Pituitary Tumor"]
                ),
            )

            # -------------------------------------------------
            # STEP 5: Return result to the home page
            # -------------------------------------------------

            return render(
                request,
                "detector/home.html",
                {
                    "uploaded": True,

                    "file_path": None,

                    "prediction": (
                        result["predicted_class"]
                    ),

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

        except Exception as e:

            print(
                "MRI upload/prediction error:",
                str(e)
            )

            return render(
                request,
                "detector/home.html",
                {
                    "error": (
                        "An error occurred while "
                        "processing the MRI image. "
                        "Please try again."
                    )
                }
            )

        finally:

            # -------------------------------------------------
            # STEP 6: Delete temporary local file
            # -------------------------------------------------

            if (
                temporary_path
                and os.path.exists(temporary_path)
            ):
                os.remove(temporary_path)


@login_required
def history(request):

    predictions = (
        Prediction.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

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


@login_required
def prediction_detail(request, prediction_id):

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