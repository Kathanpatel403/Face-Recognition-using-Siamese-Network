from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button

from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.texture import Texture

import cv2
import tensorflow as tf
from layers import L1Dist
import os
import numpy as np
from tensorflow.keras.models import load_model


class CamApp(App):
    def build(self):
        self.webcam = Image(size_hint=(1, .8))
        self.button = Button(
            text='Verify', on_press=self.verify, size_hint=(1, .1))
        self.verification_text = Label(
            text="Verification Uninitiated", size_hint=(1, .1))

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.webcam)
        layout.add_widget(self.button)
        layout.add_widget(self.verification_text)

        # loading model:
        print("Bofore loading the model.")
        binary_cross_loss = tf.losses.BinaryCrossentropy()
        self.model = load_model('siameseModel.h5', custom_objects={'L1Dist': L1Dist, 'BinaryCrossentropy': tf.losses.BinaryCrossentropy})
        print("After loading the model.")

        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update, 1.0/33.0)

        return layout

# this function will run continuously to capture webcam feed.
    def update(self, *args):

        ret, frame = self.capture.read()
        frame = frame[120:120+250, 200:200+250, :]

        buf = cv2.flip(frame, 0).tostring()
        img_texture = Texture.create(
            size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        img_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.webcam.texture = img_texture

    def preprocess(self, file_path):
        byte_img = tf.io.read_file(file_path)
        img = tf.io.decode_jpeg(byte_img)
        # resized image to 100 X 100.
        img = tf.image.resize(img, (100, 100))
        # scalling the image between 0 and 1.
        img = img / 255.0
        return img

    def verify(self, *args):
        detection_threshold = 0.5
        verification_threshold = 0.5

        # Capture input image from webcam
        SAVE_PATH = os.path.join(
            'application_data', 'input_image', 'input_image.jpg')
        ret, frame = self.capture.read()
        frame = frame[120:120+250, 200:200+250, :]
        cv2.imwrite(SAVE_PATH, frame)

        results = []
        for image in os.listdir(os.path.join('application_data', 'verification_images')):
            input_img = self.preprocess(os.path.join('application_data', 'input_image', 'input_image.jpg'))
            validation_img = self.preprocess(os.path.join('application_data', 'verification_images', image))
            print("Before predicting using model.")

            result = self.model.predict(list(np.expand_dims([input_img, validation_img], axis=1)))
            results.append(result)

        # Detection threshold: metric above which a prediction is considered positive
        # Verification threshold: proportion of positive predictions / total positive predictions
        detection = np.sum(np.array(results) > detection_threshold)
        verification = detection / len(os.listdir(os.path.join('application_data', 'verification_images')))
        verified = verification > verification_threshold

        # Update text to show verification result
        self.verification_text.text = 'Verified' if verified else 'Not Verified'

        return results, verified

if __name__ == '__main__':
    CamApp().run()