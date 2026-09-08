import os
import numpy as np


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml_models",
    "brain_tumor_detection_model.h5"
)

CLASS_LABELS = [
    "Glioma",
    "Meningioma",
    "No Tumor",
    "Pituitary Tumor"
]

IMAGE_SIZE = (224, 224)

model = None


def get_model():

    global model

    if model is None:

        import tensorflow as tf

        print("Loading brain tumor model...")

        model = tf.keras.models.load_model(
            MODEL_PATH
        )

        print("Brain tumor model loaded successfully!")

    return model


def predict_image(image_path):

    from tensorflow.keras.preprocessing import image

    model = get_model()

    print("Predicting image:", image_path)

    img = image.load_img(
        image_path,
        target_size=IMAGE_SIZE
    )

    img_array = image.img_to_array(img)

    img_array = np.expand_dims(
        img_array,
        axis=0
    )

    img_array = img_array / 255.0

    print("Image shape:", img_array.shape)

    predictions = model.predict(
        img_array,
        verbose=0
    )

    print("Raw predictions:", predictions)

    probabilities = predictions[0]

    predicted_index = np.argmax(probabilities)

    predicted_class = CLASS_LABELS[predicted_index]

    confidence = float(
        probabilities[predicted_index]
    )

    probability_dict = {
        "Glioma": float(probabilities[0]),
        "Meningioma": float(probabilities[1]),
        "No Tumor": float(probabilities[2]),
        "Pituitary Tumor": float(probabilities[3]),
    }

    return {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "probabilities": probability_dict,
    }