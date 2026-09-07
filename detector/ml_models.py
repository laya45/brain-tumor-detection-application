import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image


# ============================================================
# MODEL PATH
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml_models",
    "brain_tumor_detection_model.h5"
)


# ============================================================
# CLASS LABELS
# ============================================================

CLASS_LABELS = [
    "Glioma",
    "Meningioma",
    "No Tumor",
    "Pituitary Tumor"
]


# ============================================================
# IMAGE SETTINGS
# ============================================================

IMAGE_SIZE = (224, 224)


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading brain tumor model...")

model = tf.keras.models.load_model(MODEL_PATH)

print("Brain tumor model loaded successfully!")


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_image(image_path):

    # ----------------------------------------
    # 1. Load image
    # ----------------------------------------

    img = image.load_img(
        image_path,
        target_size=IMAGE_SIZE
    )


    # ----------------------------------------
    # 2. Convert image to numpy array
    # ----------------------------------------

    img_array = image.img_to_array(img)


    # ----------------------------------------
    # 3. Add batch dimension
    # ----------------------------------------

    img_array = np.expand_dims(
        img_array,
        axis=0
    )


    # ----------------------------------------
    # 4. Normalize pixel values
    # ----------------------------------------

    img_array = img_array / 255.0


    # ----------------------------------------
    # 5. Run model prediction
    # ----------------------------------------

    predictions = model.predict(
        img_array,
        verbose=0
    )


    # ----------------------------------------
    # 6. Get probabilities
    # ----------------------------------------

    probabilities = predictions[0]


    # ----------------------------------------
    # 7. Find highest probability
    # ----------------------------------------

    predicted_index = np.argmax(probabilities)


    # ----------------------------------------
    # 8. Get predicted class
    # ----------------------------------------

    predicted_class = CLASS_LABELS[predicted_index]


    # ----------------------------------------
    # 9. Get confidence
    # ----------------------------------------

    confidence = float(
        probabilities[predicted_index]
    )


    # ----------------------------------------
    # 10. Create probability dictionary
    # ----------------------------------------

    probability_dict = {}

    for label, probability in zip(
        CLASS_LABELS,
        probabilities
    ):
        probability_dict[label] = float(probability)


    # ----------------------------------------
    # 11. Return results
    # ----------------------------------------

    return {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "probabilities": probability_dict
    }