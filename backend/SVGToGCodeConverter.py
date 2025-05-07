from PIL import Image, ImageDraw
import re


def parse_gcode_to_coordinates(gcode_lines):
    coordinates = []
    x, y = 0, 0
    drawing = False

    for line in gcode_lines:
        line = line.strip()
        if line.startswith(";") or not line:  # Ignore comments or empty lines
            continue

        if line.startswith("G1"):  # G1 command for movement
            x_match = re.search(r'X([0-9.+-]+)', line)
            y_match = re.search(r'Y([0-9.+-]+)', line)
            if x_match:
                x = float(x_match.group(1))
            if y_match:
                y = float(y_match.group(1))
            if drawing:  # Only append coordinates if we are drawing
                coordinates.append((x, y))

        elif line.startswith("M300"):  # Pen up/down commands
            s_match = re.search(r'S([0-9]+)', line)
            if s_match:
                s_value = int(float(s_match.group(1)))
                drawing = s_value == 30  # Pen down if S30, pen up otherwise

    return coordinates


def generate_png(coordinates, output_path="output.png", image_size=(1000, 1000), scale=1):
    # Create a blank white image
    img = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(img)

    # Scale coordinates and draw the lines
    prev_point = None
    for point in coordinates:
        scaled_point = (point[0] * scale, point[1] * scale)
        if prev_point:
            draw.line([prev_point, scaled_point], fill="black", width=2)
        prev_point = scaled_point

    # Save the image
    img.save(output_path)
    print(f"Image saved to {output_path}")


def main():
    # Specify the location of the G-code file
    gcode_location = "../Temp/output.gcode"  # Replace with the path to your G-code file

    # Read the G-code file
    try:
        with open(gcode_location, "r") as file:
            gcode_lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: File not found at {gcode_location}")
        return

    # Parse G-code to coordinates
    coordinates = parse_gcode_to_coordinates(gcode_lines)

    # Generate PNG image
    generate_png(coordinates, output_path="drawing.png", image_size=(1000, 1000), scale=1)


if __name__ == "__main__":
    main()