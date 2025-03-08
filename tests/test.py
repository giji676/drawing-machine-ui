import time
from rembg import new_session, remove

from PIL import Image

class Test:
    def __init__(self):
        self.pil_image = Image.open(r"C:\Users\tvten\Desktop\F16.jpg")

    def test_rembg(self, image: Image) -> None:
        if image is None:
            return
        session = new_session("u2net_lite", providers=["CPUExecutionProvider"])

        try:
            start_time = time.time()
            image = remove(image, session=session)
            #image = remove(image)

            end_time = time.time()
            exec_time = end_time - start_time
            print(f"Finishd in {exec_time}")
        except Exception as e:
            print("❌ Error occurred in rembg:", e)

        jpg_image = Image.new("RGB", image.size, "white")
        jpg_image.paste(image, (0, 0))
        image = jpg_image
        image.show()

test = Test()
test.test_rembg(test.pil_image)
