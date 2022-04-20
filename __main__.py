import os
import random
import string

import easyocr
import numpy as np
import requests
from PIL import Image, ImageChops

reader = easyocr.Reader(["en"], gpu=False, verbose=False)


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

        self.temp_name = self.get_random_string()

    def prepare_captcha(self) -> None:
        requests_picture = self.session.get(self.endpoints["captcha"], stream=True)
        with open(f"{self.temp_name}.png", "wb") as f:
            for chunk in requests_picture:
                f.write(chunk)

        return Image.open(f"{self.temp_name}.png")

    def get_random_string(self) -> str:
        return "".join(random.choice(string.ascii_letters) for _ in range(5))

    def prepare_background(self):
        return Image.open("background.png").convert("RGB")

    def remove_background(self, captcha, background):
        subtract = ImageChops.subtract(background, captcha)
        mask1 = Image.eval(subtract, lambda a: 0 if a <= 24 else 255)
        mask2 = mask1.convert("1")

        blank = Image.eval(subtract, lambda a: 0)
        new = Image.composite(background, blank, mask2)

        return np.array(new)

    def ocr(self, picure):
        text = reader.readtext(picure, detail=0)[0]
        return "".join(text.split(" "))


def get_captcha():
    solver = Solver()

    captcha = solver.prepare_captcha()
    background = solver.prepare_background()
    removed_brackground = solver.remove_background(captcha, background)

    captcha_text = solver.ocr(removed_brackground)
    os.remove(f"{solver.temp_name}.png")

    return captcha_text


if __name__ == "__main__":
    wait_captcha = True
    while wait_captcha:
        captcha = get_captcha()
        if len(captcha) == 4 and captcha.isdigit():
            print(captcha)
            wait_captcha = False
