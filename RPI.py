import time
import requests
import numpy as np
from keras.models import load_model
from threading import Thread


model = load_model("network2.h5")
brain_waves = [
    [23623, 11182, 19781, 18250, 8140, 10460, 4684, 11255, 44, 48],
    [158150, 10443, 5787, 10414, 5828, 3369, 1863, 1097, 44, 64],
]

def make_prediction():
    prediction = model.predict([brain_waves])
    return prediction

def get_data_from_api():
    while True:
        time.sleep(1.5)
        response = requests.get("ngrok-url")
        data = response.json()
        brain_waves.append([data['delta'], data['theta'], data['low-alpha'], data['high-alpha'], data['low-beta'], data["high-beta"], data["low-gamma"], data["mid-game"]])

def recommend_and_play_music():
    # Add music features here
    pass

if __name__ == "__main__":
    t1 = Thread(target=get_data_from_api)
    t2 = Thread(target=recommend_and_play_music)
    t1.run()
    t2.run()
    t2.join()
    t1.join()