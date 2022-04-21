import easyocr
import numpy as np
import requests
import cv2

reader = easyocr.Reader(["en"], gpu=False, verbose=False)


# Avoid having to instantiate the Solver() object at each call
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Solver(metaclass=Singleton):
    def __init__(self) -> None:
        self.session = requests.Session()
        self.endpoints = {
            "captcha": "https://webresolver.nl/public/captcha/captcha.png"
        }

    # Download the captcha, and make it readable for cv2 / numpy
    def prepare_captcha(self):
        requests_picture = self.session.get(self.endpoints["captcha"], stream=True).raw
        image = np.asarray(bytearray(requests_picture.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    # Go get the background file
    @staticmethod
    def prepare_background():
        image = cv2.imread("background.png")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    # Remove the background on the captcha with the version without letter
    # Reverse the colors to have a better distinction of the letters. It is easier to read grey on white than grey on black
    @staticmethod
    def remove_background(captcha, background):
        subtract = cv2.subtract(background, captcha)
        return np.invert(subtract)

    # ocr the image where the background has been removed
    @staticmethod
    def ocr(picure):
        text = reader.readtext(picure, detail=0)
        if len(text) >= 1:
            text = text[0]
        return "".join(text.split(" "))


def get_captcha():
    solver = Solver()

    captcha = solver.prepare_captcha()
    background = solver.prepare_background()
    removed_brackground = solver.remove_background(captcha, background)

    captcha_text = solver.ocr(removed_brackground)
    return captcha_text


# Global actions performed to obtain a valid captcha
if __name__ == "__main__":
    # Get and ocr a capture until getting a coherent result
    while True:
        captcha = get_captcha()
        if len(captcha) == 4 and captcha.isdigit():
            print(captcha)
            exit(0)
