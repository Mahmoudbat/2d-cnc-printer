import xml.etree.ElementTree as ET
import os

# Configuration
XY_FEEDRATE = 3500.0        # Feedrate for G1 moves
PEN_UP_ANGLE = 50.0         # Servo angle when pen is up
PEN_DOWN_ANGLE = 30.0       # Servo angle when pen is down
SCALE = 0.1                 # Scale SVG units to mm
FLIP_Y = False              # Do not flip Y; already handled in Arduino code
script_dir = os.path.dirname(os.path.abspath(__file__))
temp_dir = os.path.join(script_dir, "../Temp")
input_svg = os.path.join(temp_dir, "output.svg")
output_gcode = os.path.join(temp_dir, "output.gcode")


class GCodeContext:
    def __init__(self, xy_feedrate=XY_FEEDRATE, pen_up_angle=PEN_UP_ANGLE, pen_down_angle=PEN_DOWN_ANGLE):
        self.xy_feedrate = xy_feedrate
        self.pen_up_angle = pen_up_angle
        self.pen_down_angle = pen_down_angle
        self.gcode_lines = []

    # In GCodeContext class:
    def pen_up(self):
        self.gcode_lines.append(f"M300 S{self.pen_up_angle:.2f}")

    def pen_down(self):
        self.gcode_lines.append(f"M300 S{self.pen_down_angle:.2f}")

    def move_to(self, x, y):
        self.gcode_lines.append(f"G1 X{x:.2f} Y{y:.2f}")

    def generate_gcode(self):
        print(f"DEBUG: Total GCode commands generated: {len(self.gcode_lines)}")
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
                    print(f"DEBUG: Found path `d` attribute: {d[:50]}...")
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
        current_x, current_y = 0, 0
        i = 0
        while i < len(parsed_commands):
            cmd = parsed_commands[i][0]
            values = parsed_commands[i][1:].strip()
            values = list(map(float, values.split())) if values else []

            if cmd in {"M", "m"}:
                try:
                    x, y = values[:2]
                    if cmd == "m":
                        x += current_x
                        y += current_y
                    current_x = x * SCALE
                    current_y = y * SCALE * (-1 if FLIP_Y else 1)
                    coordinates.append((current_x, current_y))
                    print(f"DEBUG: {cmd} MoveTo ({current_x:.2f}, {current_y:.2f})")
                except ValueError as e:
                    print(f"ERROR: Failed to parse {cmd} MoveTo: {e}")
                i += 1

            elif cmd in {"L", "l"}:
                try:
                    x, y = values[:2]
                    if cmd == "l":
                        x += current_x
                        y += current_y
                    current_x = x * SCALE
                    current_y = y * SCALE * (-1 if FLIP_Y else 1)
                    coordinates.append((current_x, current_y))
                    print(f"DEBUG: {cmd} LineTo ({current_x:.2f}, {current_y:.2f})")
                except ValueError as e:
                    print(f"ERROR: Failed to parse {cmd} LineTo: {e}")
                i += 1

            elif cmd in {"C", "c"}:
                try:
                    x, y = values[-2:]
                    if cmd == "c":
                        x += current_x
                        y += current_y
                    current_x = x * SCALE
                    current_y = y * SCALE * (-1 if FLIP_Y else 1)
                    coordinates.append((current_x, current_y))
                    print(f"DEBUG: {cmd} Cubic Bézier to ({current_x:.2f}, {current_y:.2f})")
                except ValueError as e:
                    print(f"ERROR: Failed to parse {cmd} Cubic Bézier: {e}")
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

    def convert_to_gcode(self):
        paths = self.parse_svg()
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
