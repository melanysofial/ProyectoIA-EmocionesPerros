import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

class EmotionDetector:
    def __init__(self, model_path):
        self.model = load_model(model_path)
        self.labels = ['angry', 'happy', 'relaxed', 'sad']
    
    def predict_emotion(self, frame):
        img = cv2.resize(frame, (224, 224))
        img = img_to_array(img) / 255.0
        img = np.expand_dims(img, axis=0)
        preds = self.model.predict(img)[0]
        return self.labels[np.argmax(preds)], max(preds), preds
