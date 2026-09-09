import os
import tempfile
import uuid

from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, Http404

from vercel.blob import BlobClient

from .models import Prediction
from .ml_models import predict_image


# ============================================================
# AUTH CHOICE
# ============================================================

def auth_choice(request):

    if request.user.is_authenticated:
        return redirect("home")

    return render(
        request,
        "detector/auth_choice.html"
    )


# ============================================================
# REGISTER
# ============================================================

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
                {
                    "error": "Passwords do not match."
                }
            )

        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                "detector/register.html",
                {
                    "error": "Username already exists."
                }
            )

        user = User.objects.create_user(
            username=username,
            password=password
        )

        login(request, user)

        return redirect("home")

    return render(
        request,
        "detector/register.html"
    )


# ============================================================
# LOGIN
# ============================================================

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

            login(
                request,
                user
            )

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


# ============================================================
# LOGOUT
# ============================================================

@login_required
def logout_view(request):

    logout(request)

    return redirect("auth_choice")


# ============================================================
# UPLOAD MRI TO VERCEL BLOB
# ============================================================

def upload_to_vercel_blob(upload_file):

    extension = os.path.splitext(
        upload_file.name
    )[1].lower()

    blob_filename = (
        f"mri/{uuid.uuid4().hex}{extension}"
    )

    temporary_path = None

    try:

        # ----------------------------------------------------
        # Create temporary file in /tmp
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            temporary_path = temp_file.name

            for chunk in upload_file.chunks():

                temp_file.write(chunk)

        # ----------------------------------------------------
        # Upload to private Vercel Blob
        # ----------------------------------------------------

        with BlobClient() as client:

            blob = client.upload_file(
                temporary_path,
                blob_filename,
                access="private",
                content_type=(
                    upload_file.content_type
                    or "application/octet-stream"
                ),
            )

        return blob, temporary_path

    except Exception:

        if (
            temporary_path
            and os.path.exists(temporary_path)
        ):
            os.remove(temporary_path)

        raise


# ============================================================
# HOME / MRI ANALYSIS
# ============================================================

@login_required
def home(request):

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        return render(
            request,
            "detector/home.html"
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        upload_file = request.FILES.get(
            "mri_image"
        )

        # ----------------------------------------------------
        # Validate file exists
        # ----------------------------------------------------

        if not upload_file:

            return render(
                request,
                "detector/home.html",
                {
                    "error": (
                        "Please select an MRI image."
                    )
                }
            )

        # ----------------------------------------------------
        # Validate image type
        # ----------------------------------------------------

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
                        "Please upload a JPG, JPEG, "
                        "PNG, or WEBP image."
                    )
                }
            )

        # ----------------------------------------------------
        # Validate file size
        # ----------------------------------------------------

        max_size = 4.5 * 1024 * 1024

        if upload_file.size > max_size:

            return render(
                request,
                "detector/home.html",
                {
                    "error": (
                        "Image is too large. "
                        "Please upload an image "
                        "smaller than 4.5 MB."
                    )
                }
            )

        temporary_path = None

        try:

            # =================================================
            # STEP 1
            # Upload MRI to Vercel Blob
            # =================================================

            blob, temporary_path = (
                upload_to_vercel_blob(
                    upload_file
                )
            )

            print(
                "MRI uploaded to Blob:",
                blob.url
            )

            # =================================================
            # STEP 2
            # Run TensorFlow prediction
            # =================================================

            result = predict_image(
                temporary_path
            )

            probabilities = (
                result["probabilities"]
            )

            print(
                "Prediction:",
                result["predicted_class"]
            )

            print(
                "Confidence:",
                result["confidence"]
            )

            # =================================================
            # STEP 3
            # Save prediction in PostgreSQL
            # =================================================

            prediction_record = (
                Prediction.objects.create(
                    user=request.user,

                    image_url=blob.url,

                    predicted_class=(
                        result["predicted_class"]
                    ),

                    confidence=(
                        result["confidence"]
                    ),

                    glioma_probability=(
                        probabilities["Glioma"]
                    ),

                    meningioma_probability=(
                        probabilities[
                            "Meningioma"
                        ]
                    ),

                    no_tumor_probability=(
                        probabilities[
                            "No Tumor"
                        ]
                    ),

                    pituitary_tumor_probability=(
                        probabilities[
                            "Pituitary Tumor"
                        ]
                    ),
                )
            )

            # =================================================
            # STEP 4
            # Display result
            # =================================================

            return render(
                request,
                "detector/home.html",
                {
                    "uploaded": True,

                    "file_path": None,

                    "prediction": (
                        result[
                            "predicted_class"
                        ]
                    ),

                    "confidence": round(
                        result["confidence"] * 100,
                        2
                    ),

                    "glioma": round(
                        probabilities["Glioma"]
                        * 100,
                        2
                    ),

                    "meningioma": round(
                        probabilities[
                            "Meningioma"
                        ] * 100,
                        2
                    ),

                    "no_tumor": round(
                        probabilities[
                            "No Tumor"
                        ] * 100,
                        2
                    ),

                    "pituitary_tumor": round(
                        probabilities[
                            "Pituitary Tumor"
                        ] * 100,
                        2
                    ),

                    "prediction_id": (
                        prediction_record.id
                    ),
                }
            )

        except Exception as e:

            print(
                "MRI upload/prediction error:",
                repr(e)
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

            # ------------------------------------------------
            # Delete temporary /tmp file
            # ------------------------------------------------

            if (
                temporary_path
                and os.path.exists(
                    temporary_path
                )
            ):

                os.remove(
                    temporary_path
                )


# ============================================================
# HISTORY
# ============================================================

@login_required
def history(request):

    predictions = (
        Prediction.objects
        .filter(
            user=request.user
        )
        .order_by(
            "-created_at"
        )
    )

    for prediction in predictions:

        prediction.confidence_display = (
            round(
                prediction.confidence * 100,
                2
            )
        )

    return render(
        request,
        "detector/history.html",
        {
            "predictions": predictions
        }
    )


# ============================================================
# PREDICTION DETAIL
# ============================================================

@login_required
def prediction_detail(
    request,
    prediction_id
):

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


# ============================================================
# SECURE PRIVATE MRI IMAGE
# ============================================================

@login_required
def prediction_image(request, prediction_id):

    prediction = get_object_or_404(
        Prediction,
        id=prediction_id,
        user=request.user
    )

    if not prediction.image_url:
        raise Http404("MRI image not found.")

    blob_url = prediction.image_url

    # Get the Vercel Blob token
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")

    if not token:
        print("ERROR: BLOB_READ_WRITE_TOKEN is not available.")
        raise Http404("Blob authentication is not configured.")

    try:
        import urllib.request

        # Request the private Blob with authentication
        blob_request = urllib.request.Request(
            blob_url,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        with urllib.request.urlopen(blob_request, timeout=30) as response:

            image_data = response.read()

            content_type = response.headers.get(
                "Content-Type",
                "image/jpeg"
            )

        django_response = HttpResponse(
            image_data,
            content_type=content_type
        )

        # Do not allow the private MRI image to be cached publicly
        django_response["Cache-Control"] = "private, no-store"
        django_response["X-Content-Type-Options"] = "nosniff"

        return django_response

    except Exception as e:

        print(
            "Private MRI image error:",
            repr(e)
        )

        raise Http404(
            "Unable to retrieve MRI image."
        )