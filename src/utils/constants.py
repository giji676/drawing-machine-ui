import os

GENERATED_FILES = "generated_files"
STYLE = os.path.normpath("src\\style\\style.qss")
PATH_MAKER = os.path.normpath("external\\thepathmaker-x64\\linkern.exe")

IMAGE_TSP = "image.tsp"
IMAGE_CYC = "image.cyc"
OUTPUT_COORDINATES_TXT = "output_coordinates.txt"
OUTPUT_STEPS_TXT = "path.txt"

TSP_PATH = os.path.join(GENERATED_FILES, IMAGE_TSP)
CYC_PATH = os.path.join(GENERATED_FILES, IMAGE_CYC)
OUTPUT_COODINATES_PATH = os.path.join(GENERATED_FILES, OUTPUT_COORDINATES_TXT)
OUTPUT_STEPS_PATH = os.path.join(GENERATED_FILES, OUTPUT_STEPS_TXT)

SETTINGS = "settings.json"

# Used only for displaying the machine on the canvas, doesn't affect coordinates
IMAGE_OFFSET = (100, 100)

DEFAULT_SETTINGS = {
    "beltToothDistance": 2,
    "toothOngear": 20,
    "stepsPerRev": 3200,
    "motorDir": [1, -1],
    "distanceBetweenMotors": 580,
    "startDistance": [590, 590],
    "paperSize": [190, 270],
    "paperOffset": 35,
}
