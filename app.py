from flask import Flask, render_template, request, jsonify
import base64
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, load_img
import PIL
import io
import cv2

app = Flask(__name__)

face_cascade = cv2.CascadeClassifier(
    "./static/xml/haarcascade_frontalface_default.xml")


model = load_model("./static/models/emotion_detector_1681572728.3088243.h5")
class_names = {
    0: 'Anger',
    1: 'Disgust',
    2: 'Fear',
    3: 'Happy',
    4: 'Neutral',
    5: 'Sadness',
    6: 'Surprise'
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/snapImage', methods=['POST'])
def snapImage():

    # Get the image data from the request
    image_data = request.form.get('imageData')

    # Decode the image data
    image_data = base64.b64decode(image_data.split(',')[1])

    # Convert the image data to a numpy array
    nparr = np.frombuffer(image_data, np.uint8)
    img_grey = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    normal_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Convert normal image to RGB
    normal_img = cv2.cvtColor(normal_img, cv2.COLOR_BGR2RGB)

    # Detect the face in the image
    faces = face_cascade.detectMultiScale(img_grey, 1.3, 5)

    if len(faces) == 0:
        return jsonify({'prediction': 'no face detected'})

    # Get the first face detected
    (x, y, w, h) = faces[0]

    # Draw a rectangle around the face
    img_with_rect = cv2.rectangle(
        normal_img.copy(), (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Crop the image to the face
    img_grey = img_grey[y:y+h, x:x+w]

    # Resize the image and convert it to an array
    img_grey = cv2.resize(img_grey, (48, 48))
    img_array = img_to_array(img_grey)
    img_array = img_array.reshape(
        (1, img_array.shape[0], img_array.shape[1], 1))

    prediction = model.predict(img_array)
    predicted_class = np.argmax(prediction)
    predicted_emotion = class_names[predicted_class]

    # Write the predicted emotion on the image
    img_with_text = cv2.putText(img_with_rect, predicted_emotion, (x, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Convert the image to a JPEG string
    img_buffer = io.BytesIO()
    PIL.Image.fromarray(img_with_text).save(img_buffer, format="JPEG")
    img_str = base64.b64encode(img_buffer.getvalue()).decode()

    response = {'prediction': predicted_emotion, 'imageData': img_str}

    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
