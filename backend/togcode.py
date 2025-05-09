import xml.etree.ElementTree as ET
import os

# Configuration
XY_FEEDRATE = 3500.0  # Feedrate for G1 moves (removed from the G-code)
PEN_UP_ANGLE = 50.0  # Servo angle when pen is up
PEN_DOWN_ANGLE = 30.0  # Servo angle when pen is down
STEPS_PER_MM_X = 273.3  # Steps per mm for X-axis
STEPS_PER_MM_Y = 192.3  # Steps per mm for Y-axis
FLIP_Y = True  # Flip the Y-axis (depending on your CNC setup)
script_dir = os.path.dirname(os.path.abspath(__file__))
temp_dir = os.path.join(script_dir, "../Temp")
input_svg = os.path.join(temp_dir, "output.svg")
output_gcode = os.path.join(temp_dir, "output.gcode")

# Boundary dimensions in millimeters
BOUNDARY_X = 15.2
BOUNDARY_Y = 15.2

# Adjust scaling based on the steps per mm
SCALE_X = 1 / STEPS_PER_MM_X  # Adjust to inverse of steps per mm for X-axis
SCALE_Y = 1 / STEPS_PER_MM_Y  # Adjust to inverse of steps per mm for Y-axis


class GCodeContext:
    def __init__(self, pen_up_angle=PEN_UP_ANGLE, pen_down_angle=PEN_DOWN_ANGLE):
        self.pen_up_angle = pen_up_angle
        self.pen_down_angle = pen_down_angle
        self.gcode_lines = []

    def pen_up(self):
        self.gcode_lines.append(f"M300 S{self.pen_up_angle:.2f}")

    def pen_down(self):
        self.gcode_lines.append(f"M300 S{self.pen_down_angle:.2f}")

    def move_to(self, x, y):
        self.gcode_lines.append(f"G1 X{x:.2f} Y{y:.2f}")  # Removed feedrate

    def generate_gcode(self):
        print(f"DEBUG: Total GCode commands generated: {len(self.gcode_lines)}")

        # Add a G1 X0 Y0 move at the end of the G-code
        self.gcode_lines.append("G1 X0 Y0")

        return "\n".join(self.gcode_lines)


class SVGToGCodeConverter:
    def __init__(self, svg_file, gcode_context):
        self.svg_file = svg_file
        self.gcode_context = gcode_context
        self.namespace = {"svg": "http://www.w3.org/2000/svg"}

    def parse_svg(self):
        try:
            tree = ET.parse(self.svg_file)
            root = tree.getroot()
            paths = []

            for elem in root.findall(".//svg:path", self.namespace):
                d = elem.attrib.get("d")
                if d:
                    print(f"DEBUG: Found path d attribute: {d[:50]}...")
                    parsed_path = self.parse_path_data(d)
                    if parsed_path:
                        print(f"DEBUG: Parsed path with {len(parsed_path)} points.")
                        paths.append(parsed_path)
            print(f"DEBUG: Total paths parsed: {len(paths)}")
            return paths
        except ET.ParseError as e:
            print(f"ERROR: Failed to parse SVG file: {e}")
            return []

    def parse_path_data(self, path_data):
        parsed_commands = []
        current_command = ""
        for char in path_data:
            if char.isalpha():
                if current_command:
                    parsed_commands.append(current_command.strip())
                current_command = char
            else:
                current_command += char
        if current_command:
            parsed_commands.append(current_command.strip())

        coordinates = []
        current_x, current_y = 0.0, 0.0
        i = 0
        while i < len(parsed_commands):
            cmd = parsed_commands[i][0]
            values = parsed_commands[i][1:].strip()
            values = list(map(float, values.replace(',', ' ').split())) if values else []

            if cmd in {"M", "m"}:
                for j in range(0, len(values), 2):
                    x, y = values[j], values[j + 1]
                    if cmd == "m":
                        x = current_x + x * SCALE_X
                        y = current_y + y * SCALE_Y
                    else:
                        x = x * SCALE_X
                        y = y * SCALE_Y

                    current_x = x
                    current_y = y
                    coordinates.append((current_x, current_y))
                    print(f"DEBUG: {cmd} MoveTo ({current_x:.2f}, {current_y:.2f})")
                i += 1

            elif cmd in {"L", "l"}:
                for j in range(0, len(values), 2):
                    x, y = values[j], values[j + 1]
                    if cmd == "l":
                        x = current_x + x * SCALE_X
                        y = current_y + y * SCALE_Y
                    else:
                        x = x * SCALE_X
                        y = y * SCALE_Y

                    current_x = x
                    current_y = y
                    coordinates.append((current_x, current_y))
                    print(f"DEBUG: {cmd} LineTo ({current_x:.2f}, {current_y:.2f})")
                i += 1

            elif cmd in {"C", "c"}:
                for j in range(0, len(values), 6):
                    x1, y1 = values[j], values[j + 1]
                    x2, y2 = values[j + 2], values[j + 3]
                    x, y = values[j + 4], values[j + 5]

                    if cmd == "c":
                        x1 += current_x / SCALE_X
                        y1 += current_y / SCALE_Y
                        x2 += current_x / SCALE_X
                        y2 += current_y / SCALE_Y
                        x += current_x / SCALE_X
                        y += current_y / SCALE_Y

                    x1 *= SCALE_X
                    y1 *= SCALE_Y
                    x2 *= SCALE_X
                    y2 *= SCALE_Y
                    x *= SCALE_X
                    y *= SCALE_Y

                    steps = 10  # You can increase for smoother curves
                    for t in range(steps + 1):
                        t /= steps
                        xt = (1 - t) ** 3 * current_x + 3 * (1 - t) ** 2 * t * x1 + 3 * (
                                    1 - t) * t ** 2 * x2 + t ** 3 * x
                        yt = (1 - t) ** 3 * current_y + 3 * (1 - t) ** 2 * t * y1 + 3 * (
                                    1 - t) * t ** 2 * y2 + t ** 3 * y
                        coordinates.append((xt, yt))

                    current_x = x
                    current_y = y
                    print(f"DEBUG: {cmd} Cubic Bézier to ({current_x:.2f}, {current_y:.2f})")
                i += 1

            elif cmd in {"Z", "z"}:
                if coordinates:
                    coordinates.append(coordinates[0])
                    print(f"DEBUG: {cmd} ClosePath to ({coordinates[0][0]:.2f}, {coordinates[0][1]:.2f})")
                i += 1

            else:
                print(f"DEBUG: Unsupported or malformed command: {cmd}")
                i += 1

        return coordinates

    def scale_and_center_paths(self, paths):
        # Determine the bounds of the image
        min_x = min(point[0] for path in paths for point in path)
        max_x = max(point[0] for path in paths for point in path)
        min_y = min(point[1] for path in paths for point in path)
        max_y = max(point[1] for path in paths for point in path)

        width = max_x - min_x
        height = max_y - min_y

        # Calculate scaling factor
        scale_factor = min(BOUNDARY_X / width, BOUNDARY_Y / height)

        # Calculate translation to center the drawing
        x_offset = (BOUNDARY_X - width * scale_factor) / 2
        y_offset = (BOUNDARY_Y - height * scale_factor) / 2

        # Scale and translate all paths
        scaled_paths = []
        for path in paths:
            scaled_path = [
                ((x - min_x) * scale_factor + x_offset, (y - min_y) * scale_factor + y_offset)
                for x, y in path
            ]
            scaled_paths.append(scaled_path)

        return scaled_paths

    def convert_to_gcode(self):
        paths = self.parse_svg()
        if not paths:
            print("DEBUG: No paths found in the SVG")
            return

        # Scale and center paths to fit within the boundary
        paths = self.scale_and_center_paths(paths)

        for idx, path in enumerate(paths):
            if not path:
                print(f"DEBUG: Skipping empty path at index {idx}")
                continue
            print(f"DEBUG: Processing path {idx} with {len(path)} points.")
            self.gcode_context.pen_up()
            self.gcode_context.move_to(*path[0])
            self.gcode_context.pen_down()

            for point in path[1:]:
                self.gcode_context.move_to(*point)

            self.gcode_context.pen_up()


def main():
    gcode_context = GCodeContext()
    converter = SVGToGCodeConverter(input_svg, gcode_context)

    print(f"DEBUG: Starting conversion for {input_svg}")
    converter.convert_to_gcode()

    gcode_content = gcode_context.generate_gcode()
    with open(output_gcode, "w") as f:
        f.write(gcode_content)
    print(f"GCode written to {output_gcode}")


if __name__ == "__main__":
    main()