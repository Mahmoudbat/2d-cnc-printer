import os
import math
from svgpathtools import svg2paths
from svgpathtools import Path, Line, QuadraticBezier, CubicBezier, Arc

# Configuration
temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Temp")
input_svg = os.path.join(temp_dir, "output.svg")
output_gcode = os.path.join(temp_dir, "output.gcode")
verbose = False

# Machine settings
XY_FEEDRATE = 3500.0
PEN_UP = 50
PEN_DOWN = 30
STEPS_PER_MM_X = 192.3
STEPS_PER_MM_Y = 192.3
FLIP_Y = False
FLIP_X = False

# Boundaries in mm
MAX_X = 16
MAX_Y = 14.4

SCALE_X = 1 / STEPS_PER_MM_X
SCALE_Y = 1 / STEPS_PER_MM_Y

def flip_coords(x, y):
    if FLIP_X:
        x = MAX_X - x
    if FLIP_Y:
        y = MAX_Y - y
    return x, y

class GCodeContext:
    def __init__(self):
        self.gcode = []
        self.pen_is_down = False

    def pen_up(self):
        if self.pen_is_down:
            self.gcode.append(f"M300 S{PEN_UP}")
            self.gcode.append("G4 P100")
            self.pen_is_down = False

    def pen_down(self):
        if not self.pen_is_down:
            self.gcode.append(f"M300 S{PEN_DOWN}")
            self.gcode.append("G4 P100")
            self.pen_is_down = True

    def move_to(self, x, y, rapid=False):
        x, y = flip_coords(x, y)
        move_cmd = "G0" if rapid else "G1"
        if rapid:
            self.gcode.append(f"{move_cmd} X{x:.2f} Y{y:.2f}")
        else:
            self.gcode.append(f"{move_cmd} X{x:.2f} Y{y:.2f} F{XY_FEEDRATE}")

    def generate_gcode(self):
        self.pen_up()
        self.gcode.append("G1 X0 Y0")
        return "\n".join(self.gcode)

def path_to_points(path, num_samples = 4):
    """Convert an svgpathtools Path into a list of (x, y) points, sampling curves."""
    points = []
    for seg in path:
        for i in range(num_samples+1):
            t = i / num_samples
            pt = seg.point(t)
            x, y = pt.real, pt.imag
            points.append((x * SCALE_X, y * SCALE_Y))
    # Remove duplicate consecutive points:
    filtered = []
    for pt in points:
        if not filtered or math.hypot(pt[0]-filtered[-1][0], pt[1]-filtered[-1][1]) > 1e-4:
            filtered.append(pt)
    return filtered

def scale_and_center(paths, max_x=MAX_X, max_y=MAX_Y):
    all_pts = [pt for path in paths for pt in path]
    if not all_pts:
        return paths
    min_x = min(x for x, y in all_pts)
    min_y = min(y for x, y in all_pts)
    max_x0 = max(x for x, y in all_pts)
    max_y0 = max(y for x, y in all_pts)
    width = max_x0 - min_x
    height = max_y0 - min_y
    if width == 0 or height == 0:
        scale = 1.0
    else:
        scale = min(max_x / width, max_y / height)
    x_offset = (max_x - width * scale) / 2
    y_offset = (max_y - height * scale) / 2
    new_paths = []
    for path in paths:
        new_paths.append([
            ( (x - min_x) * scale + x_offset,
              (y - min_y) * scale + y_offset )
            for (x, y) in path
        ])
    return new_paths

def convert_svg_to_gcode(input_svg, output_gcode):
    paths, _ = svg2paths(input_svg)
    all_path_pts = []
    for path in paths:
        pts = path_to_points(path)
        if pts:
            all_path_pts.append(pts)
    # Center and scale
    all_path_pts = scale_and_center(all_path_pts)
    # GCode generation
    ctx = GCodeContext()
    for path in all_path_pts:
        if len(path) < 2:
            continue
        ctx.pen_up()
        ctx.move_to(*path[0], rapid=True)
        ctx.pen_down()
        last_x, last_y = path[0]
        for x, y in path[1:]:
            # Only add if distance is significant
            if math.hypot(x-last_x, y-last_y) > 0.01:
                ctx.move_to(x, y)
                last_x, last_y = x, y
        ctx.pen_up()
    # Home
    ctx.pen_up()
    ctx.move_to(0, 0, rapid=True)
    with open(output_gcode, "w") as f:
        f.write(ctx.generate_gcode())
    print(f"✅ Successfully converted SVG to GCode and saved to {output_gcode}")

if __name__ == "__main__":
    convert_svg_to_gcode(input_svg, output_gcode)