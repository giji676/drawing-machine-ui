This is a gui program I created to process images for my V plotter machine.
It takes in an image, and allows user to process it in multiple ways. For example,
grayscale, scale, rotate. But, the main functions are wave, dithering and linkern.

Wave: this function turns the image grayscale, and maps each pixel of the image
to a sin function with frequency and amplitude adjusted based on the pixel value.

Dithering: this funciton turns the image into black and white, by applying
Jarvis-Judice-Ninke Dithering. Output of this is then used by the linkern function.

Linkern: this function is a TSP (traveling salesman problem) solver. It is used to 
connect the points created by the dithering function using a single continuous line.

After the Wave or Linkern function is used, the output is used by toSteps.py to
turn the coordinate values into steps of the stepper motors on the plotter machine.
The steps are almost like GCODE.


The program also lets the user configure the dimensions and settings of the machine.
It lets you change settings such as paper size, starting position and more. The 
settings are then used with the toSteps.py to output the correct instructions for
the stepper motors.
