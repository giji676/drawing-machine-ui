from svg_to_gcode.compiler import Compiler, interfaces
from svg_to_gcode.geometry import Vector
from svg_to_gcode.svg_parser import parse_file


class CustomInterface(interfaces.Gcode):
    def __init__(self):
        super().__init__()
        self.fan_speed = 1

    # Override the laser_off method such that it also powers off the fan.
    def laser_off(self):
        return "PENUP"

    # Override the set_laser_power method
    def set_laser_power(self, power):
        if power < 0 or power > 1:
            raise ValueError(
                f"{power} is out of bounds. Laser power must be given between 0 and 1. "
                f"The interface will scale it correctly."
            )

        return "PENDOWN"

    def set_absolute_coordinates(self):
        return ""

    def linear_move(self, x=None, y=None, z=None):

        if self._next_speed is None:
            raise ValueError(
                "Undefined movement speed. Call set_movement_speed before executing movement commands."
            )

        # Don't do anything if linear move was called without passing a value.
        if x is None and y is None and z is None:
            return ""
        command = ""

        # Move if not 0 and not None
        command += f"{x} " if x is not None else ""
        command += f"{y}" if y is not None else ""

        if self.position is not None or (x is not None and y is not None):
            if x is None:
                x = self.position.x

            if y is None:
                y = self.position.y

            self.position = Vector(x, y)

        return command


def SVGToGCODE(input_path, output_path):
    # Instantiate a compiler, specifying the custom interface and the speed at which the tool should move.
    gcode_compiler = Compiler(
        CustomInterface, movement_speed=1000, cutting_speed=300, pass_depth=5
    )

    curves = parse_file(input_path)  # Parse an svg file into geometric curves

    gcode_compiler.append_curves(curves)
    gcode_compiler.compile_to_file(output_path)
    return 1
