import re
import matplotlib.pyplot as plt

def parse_gcode(file_path):
    drawing_segments = []
    current_x, current_y = 0, 0
    pen_down = False
    current_path = []

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip().upper()

            if 'M300 S30' in line:
                pen_down = True
                # Start a new drawing segment
                current_path = [(current_x, current_y)]
            elif 'M300 S50' in line:
                pen_down = False
                if current_path:
                    # Finish the current drawing segment
                    drawing_segments.append(current_path)
                    current_path = []

            elif line.startswith('G0') or line.startswith('G1'):
                x_match = re.search(r'X([-+]?[0-9]*\.?[0-9]+)', line)
                y_match = re.search(r'Y([-+]?[0-9]*\.?[0-9]+)', line)

                if x_match:
                    current_x = float(x_match.group(1))
                if y_match:
                    current_y = float(y_match.group(1))

                if pen_down:
                    current_path.append((current_x, current_y))

    # If pen is still down at end of file
    if pen_down and current_path:
        drawing_segments.append(current_path)

    return drawing_segments

def draw_path(segments, output_path="gcode_plot.png"):
    if not segments:
        print("No path segments to draw.")
        return

    plt.figure(figsize=(6, 6))
    for segment in segments:
        x_vals, y_vals = zip(*segment)
        plt.plot(x_vals, y_vals, marker='o', linestyle='-', color='blue')

    plt.title("G-code Path")
    plt.xlabel("X axis")
    plt.ylabel("Y axis")
    plt.axis('equal')
    plt.grid(True)
    plt.savefig(output_path)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    gcode_file = "../Temp/output.gcode"  # fixed slashes
    path_segments = parse_gcode(gcode_file)
    draw_path(path_segments)
