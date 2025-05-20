import os
import re
import math
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

PEN_UP = 50
PEN_DOWN = 30
FLIP_Y = False  # Set True if Y should be flipped (e.g., for screen vs machine)

class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

def sim_coords(x, y):
    return x, (-y if FLIP_Y else y)

def parse_gcode_file_lines(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    return [line.rstrip('\n') for line in lines]

def arc_points(start, end, center, clockwise, num=30):
    sx, sy = start
    ex, ey = end
    cx, cy = center
    r = math.hypot(sx - cx, sy - cy)
    angle1 = math.atan2(sy - cy, sx - cx)
    angle2 = math.atan2(ey - cy, ex - cx)
    if clockwise:
        if angle2 > angle1:
            angle2 -= 2 * math.pi
    else:
        if angle2 < angle1:
            angle2 += 2 * math.pi
    points = []
    for i in range(num + 1):
        theta = angle1 + (angle2 - angle1) * i / num
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        points.append((x, y))
    return points

def generate_segments_from_gcode(gcode_lines):
    currentPos = Point(0, 0)
    pen_is_down = False
    segments = []
    for idx, line in enumerate(gcode_lines):
        line_u = line.strip().split(';')[0].upper()
        if not line_u:
            continue
        # G0/G1 linear moves
        if line_u.startswith('G0') or line_u.startswith('G1'):
            x_match = re.search(r'X([-+]?\d*\.?\d+)', line_u)
            y_match = re.search(r'Y([-+]?\d*\.?\d+)', line_u)
            x = currentPos.x
            y = currentPos.y
            if x_match:
                x = float(x_match.group(1))
            if y_match:
                y = float(y_match.group(1))
            simX, simY = sim_coords(x, y)
            if pen_is_down and (simX != currentPos.x or simY != currentPos.y):
                segment = [(currentPos.x, currentPos.y), (simX, simY), 'line']
                segments.append((segment, idx))
            currentPos.x = simX
            currentPos.y = simY
        # G2/G3 arc moves
        elif line_u.startswith('G2') or line_u.startswith('G3'):
            x_match = re.search(r'X([-+]?\d*\.?\d+)', line_u)
            y_match = re.search(r'Y([-+]?\d*\.?\d+)', line_u)
            i_match = re.search(r'I([-+]?\d*\.?\d+)', line_u)
            j_match = re.search(r'J([-+]?\d*\.?\d+)', line_u)
            x = currentPos.x
            y = currentPos.y
            i = 0.0
            j = 0.0
            if x_match:
                x = float(x_match.group(1))
            if y_match:
                y = float(y_match.group(1))
            if i_match:
                i = float(i_match.group(1))
            if j_match:
                j = float(j_match.group(1))
            simX, simY = sim_coords(x, y)
            centerX, centerY = sim_coords(currentPos.x + i, currentPos.y + j)
            if pen_is_down:
                arc = arc_points(
                    (currentPos.x, currentPos.y),
                    (simX, simY),
                    (centerX, centerY),
                    clockwise=line_u.startswith('G2'),
                    num=50
                )
                segment = [arc, 'arc']
                segments.append((segment, idx))
            currentPos.x = simX
            currentPos.y = simY
        # Pen up/down
        elif 'M300' in line_u:
            s_match = re.search(r'S(\d+)', line_u)
            if s_match:
                sval = int(s_match.group(1))
                if sval == PEN_DOWN:
                    pen_is_down = True
                elif sval == PEN_UP:
                    pen_is_down = False
    return segments

def plot_segments_gcode_interactive(gcode_lines, output_gcode, output_plot="simulated_plot.png"):
    segments = generate_segments_from_gcode(gcode_lines)
    fig, ax = plt.subplots(figsize=(8, 8))
    lines = []
    gcode_idx_map = []
    for idx, (seg, gcode_idx) in enumerate(segments):
        if isinstance(seg[-1], str) and seg[-1] == 'line':
            x, y = zip(*seg[:-1])
            l, = ax.plot(x, y, 'b-', picker=3, label=str(gcode_idx))
        elif isinstance(seg[-1], str) and seg[-1] == 'arc':
            arc_pts = seg[0]
            x, y = zip(*arc_pts)
            l, = ax.plot(x, y, 'g-', picker=3, label=str(gcode_idx))
        else:
            continue
        lines.append(l)
        gcode_idx_map.append(gcode_idx)
    ax.set_title("Click segment to select, 'd' to mark invisible/pen-up, close to save")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_aspect('equal')
    ax.grid(True)
    plt.tight_layout()

    selected = {'line': None, 'idx': None, 'gidx': None}
    virtual_penup_lines = set()

    def on_pick(event):
        for i, l in enumerate(lines):
            if event.artist == l and l.get_visible():
                if selected['line']:
                    selected['line'].set_color('b')
                selected['line'] = l
                selected['idx'] = i
                selected['gidx'] = gcode_idx_map[i]
                l.set_color('r')
                fig.canvas.draw()
                print(f"Selected plotted segment for G-code line {gcode_idx_map[i]}:")
                print(f"    {gcode_lines[gcode_idx_map[i]]}")
                print("Press 'd' to mark as pen-up/hide, or select another.")
                break

    def on_key(event):
        if event.key == 'd' and selected['idx'] is not None:
            idx = selected['idx']
            gidx = selected['gidx']
            # Mark for "virtual pen-up"
            virtual_penup_lines.add(gidx)
            # Hide from plot (don't remove from the list!)
            lines[idx].set_visible(False)
            # Deselect
            selected['line'] = None
            selected['idx'] = None
            selected['gidx'] = None
            fig.canvas.draw_idle()  # Fast redraw, no autoscale
            print(f"Marked G-code line {gidx} for virtual pen-up: {gcode_lines[gidx]}")
            print("Segment hidden and will be surrounded by M300 S50/S30 on save.")

    fig.canvas.mpl_connect('pick_event', on_pick)
    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()
    plt.close(fig)

    # --- Save on window close ---
    # Instead of deleting, wrap the marked lines with pen up/down
    new_gcode = []
    for idx, line in enumerate(gcode_lines):
        if line is None:
            continue
        if idx in virtual_penup_lines:
            new_gcode.append(f"M300 S{PEN_UP}")    # Pen up before
            new_gcode.append(line)                 # The original line
            new_gcode.append(f"M300 S{PEN_DOWN}")  # Pen down after
        else:
            new_gcode.append(line)

    # Backup if overwriting original
    if os.path.exists(output_gcode):
        backup_path = output_gcode + ".bak"
        with open(backup_path, "w") as f:
            for line in gcode_lines:
                if line is not None:
                    f.write(line + "\n")
        print(f"Original G-code backed up to: {os.path.abspath(backup_path)}")

    with open(output_gcode, "w") as f:
        for line in new_gcode:
            f.write(line + "\n")
    print(f"Cleaned G-code saved as {os.path.abspath(output_gcode)}")

    # --- Show cleaned output ---
    segments_cleaned = generate_segments_from_gcode(new_gcode)
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    for seg, _ in segments_cleaned:
        if isinstance(seg[-1], str) and seg[-1] == 'line':
            x, y = zip(*seg[:-1])
            ax2.plot(x, y, 'b-')
        elif isinstance(seg[-1], str) and seg[-1] == 'arc':
            arc_pts = seg[0]
            x, y = zip(*arc_pts)
            ax2.plot(x, y, 'g-')
    ax2.set_title("Simulated CNC Plotter Output (Cleaned/Edited)")
    ax2.set_xlabel("X")
    ax2.set_ylabel("Y")
    ax2.set_aspect('equal')
    ax2.grid(True)
    plt.tight_layout()
    fig2.savefig(output_plot, dpi=200, bbox_inches='tight')
    plt.close(fig2)
    print(f"Plot saved as {os.path.abspath(output_plot)}")

if __name__ == "__main__":
    gcode_file = "../Temp/output.gcode"
    plot_segments_gcode_interactive(parse_gcode_file_lines(gcode_file), output_gcode=gcode_file)