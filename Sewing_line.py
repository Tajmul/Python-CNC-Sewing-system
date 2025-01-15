import pygame
import math
import serial
import time
import os

# Initialize pygame
pygame.init()

# Constants
WINDOW_SIZE = 800
BLOCK_SIZE = 1
STITCH_LENGTH = 2.5  # mm per stitch
PIXELS_PER_MM = 5  # Assume 1 mm = 5 pixels for scaling
STITCH_PIXELS = STITCH_LENGTH * PIXELS_PER_MM

# Colors
BACKGROUND_COLOR = (255, 255, 255)
LINE_COLOR = (0, 255, 0)
DOT_COLOR = (0, 0, 0)
SIMULATION_DOT_COLOR = (255, 0, 0)
BUTTON_COLOR = (0, 128, 255)
TEXT_COLOR = (255, 255, 255)

# Screen setup
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("CNC Sewing Line")

# Fonts
font = pygame.font.Font(None, 36)

# Variables
running = True
start_point = None
current_position = None
lines = {}  # Dictionary of patterns {"pattern_name": [(start, end), ...]}
current_pattern = "Pattern1"  # Default pattern
moving_fast = False
move_start_time = None

# Buttons
send_button = pygame.Rect(50, 750, 200, 40)
simulate_button = pygame.Rect(300, 750, 200, 40)
reset_button = pygame.Rect(550, 750, 200, 40)
save_button = pygame.Rect(50, 700, 200, 40)
open_button = pygame.Rect(300, 700, 200, 40)

# Pattern buttons
pattern_buttons = []
for i in range(10):
    pattern_buttons.append(pygame.Rect(650, 50 + i * 50, 120, 40))

# Arduino setup
try:
    arduino = serial.Serial('COM3', 115200, timeout=1)  # Update COM port as needed
    time.sleep(2)  # Allow time for connection
except Exception as e:
    print(f"Arduino connection failed: {e}")
    arduino = None

# Functions
def draw_simulation_dot(x, y):
    pygame.draw.circle(screen, SIMULATION_DOT_COLOR, (int(x), int(y)), 3)
    pygame.display.flip()
    time.sleep(0.1)  # Simulate stitching delay

def send_to_arduino(lines):
    if arduino:
        for line in lines:
            start, end = line
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            distance = math.hypot(dx, dy)
            steps = int(distance // STITCH_PIXELS)
            for step in range(1, steps + 1):
                x = start[0] + (dx / distance) * step * STITCH_PIXELS
                y = start[1] + (dy / distance) * step * STITCH_PIXELS
                draw_simulation_dot(x, y)
                command = f"G1 X{x / PIXELS_PER_MM:.2f} Y{y / PIXELS_PER_MM:.2f}\n"
                arduino.write(command.encode())
                print(command.strip())  # Display in serial monitor

                # Display X, Y in the window
                screen.fill(BACKGROUND_COLOR, (600, 10, 190, 40))  # Clear previous text
                coord_text = font.render(f"X: {x / PIXELS_PER_MM:.2f} Y: {y / PIXELS_PER_MM:.2f}", True, TEXT_COLOR)
                screen.blit(coord_text, (600, 10))
                pygame.display.flip()

                time.sleep(0.1)  # Simulate sending delay
        arduino.write(b"M30\n")  # End of program
        print("Data sent to Arduino")
    else:
        print("Arduino not connected")

def simulate_stitches(lines):
    for line in lines:
        start, end = line
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.hypot(dx, dy)
        steps = int(distance // STITCH_PIXELS)
        for step in range(1, steps + 1):
            x = start[0] + (dx / distance) * step * STITCH_PIXELS
            y = start[1] + (dy / distance) * step * STITCH_PIXELS
            draw_simulation_dot(x, y)

def reset_drawing():
    global lines, start_point, current_position
    lines[current_pattern] = []
    start_point = None
    current_position = None
    screen.fill(BACKGROUND_COLOR)
    pygame.display.flip()

def save_gcode(filename, lines):
    try:
        with open(filename, 'w') as file:
            for pattern, pattern_lines in lines.items():
                file.write(f"; {pattern}\n")  # Write pattern name as a comment
                for line in pattern_lines:
                    start, end = line
                    file.write(f"G1 X{start[0] / PIXELS_PER_MM:.2f} Y{start[1] / PIXELS_PER_MM:.2f}\n")
                    file.write(f"G1 X{end[0] / PIXELS_PER_MM:.2f} Y{end[1] / PIXELS_PER_MM:.2f}\n")
            file.write("M30\n")  # End of program
        print(f"G-code saved to {filename}")
    except Exception as e:
        print(f"Failed to save G-code: {e}")

def open_gcode(filename):
    global lines
    try:
        with open(filename, 'r') as file:
            lines = {}
            current_pattern = None
            content = file.readlines()
            for line in content:
                if line.startswith(";"):
                    current_pattern = line.strip()[2:]  # Extract pattern name
                    lines[current_pattern] = []
                elif line.startswith("G1") and current_pattern:
                    coords = line.strip().split()
                    x = float(coords[1][1:]) * PIXELS_PER_MM
                    y = float(coords[2][1:]) * PIXELS_PER_MM
                    if len(lines[current_pattern]) > 0 and len(lines[current_pattern][-1]) == 1:
                        lines[current_pattern][-1] = (lines[current_pattern][-1][0], (x, y))
                    else:
                        lines[current_pattern].append(((x, y),))
        print(f"G-code loaded from {filename}")
    except Exception as e:
        print(f"Failed to open G-code: {e}")

# Main loop
while running:
    screen.fill(BACKGROUND_COLOR)

    # Draw buttons
    pygame.draw.rect(screen, BUTTON_COLOR, send_button)
    pygame.draw.rect(screen, BUTTON_COLOR, simulate_button)
    pygame.draw.rect(screen, BUTTON_COLOR, reset_button)
    pygame.draw.rect(screen, BUTTON_COLOR, save_button)
    pygame.draw.rect(screen, BUTTON_COLOR, open_button)

    send_text = font.render("Send to Arduino", True, TEXT_COLOR)
    simulate_text = font.render("Simulate Offline", True, TEXT_COLOR)
    reset_text = font.render("Reset", True, TEXT_COLOR)
    save_text = font.render("Save G-code", True, TEXT_COLOR)
    open_text = font.render("Open G-code", True, TEXT_COLOR)

    screen.blit(send_text, (send_button.x + 10, send_button.y + 5))
    screen.blit(simulate_text, (simulate_button.x + 10, simulate_button.y + 5))
    screen.blit(reset_text, (reset_button.x + 50, reset_button.y + 5))
    screen.blit(save_text, (save_button.x + 30, save_button.y + 5))
    screen.blit(open_text, (open_button.x + 30, open_button.y + 5))

    # Draw pattern buttons
    for i, button in enumerate(pattern_buttons):
        pygame.draw.rect(screen, BUTTON_COLOR, button)
        pattern_text = font.render(f"Pattern{i + 1}", True, TEXT_COLOR)
        screen.blit(pattern_text, (button.x + 10, button.y + 5))

    # Highlight selected pattern
    selected_pattern_button = pattern_buttons[int(current_pattern[-1]) - 1]
    pygame.draw.rect(screen, (255, 0, 0), selected_pattern_button, 2)

    # Draw existing lines with stitches
    for pattern, pattern_lines in lines.items():
        for line in pattern_lines:
            start, end = line
            pygame.draw.line(screen, LINE_COLOR, start, end, 2)

            # Draw stitches as dots
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            distance = math.hypot(dx, dy)
            steps = int(distance // STITCH_PIXELS)
            for step in range(1, steps + 1):
                x = start[0] + (dx / distance) * step * STITCH_PIXELS
                y = start[1] + (dy / distance) * step * STITCH_PIXELS
                pygame.draw.circle(screen, DOT_COLOR, (int(x), int(y)), 2)

    # Event handling
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
        moving_fast = True
        move_start_time = pygame.time.get_ticks()
    else:
        moving_fast = False
        move_start_time = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if send_button.collidepoint(event.pos):
                if current_pattern in lines:
                    send_to_arduino(lines[current_pattern])
            elif simulate_button.collidepoint(event.pos):
                if current_pattern in lines:
                    simulate_stitches(lines[current_pattern])
            elif reset_button.collidepoint(event.pos):
                reset_drawing()
            elif save_button.collidepoint(event.pos):
                save_gcode(f"{current_pattern}.gcode", lines)
            elif open_button.collidepoint(event.pos):
                open_gcode(f"{current_pattern}.gcode")
            else:
                for i, button in enumerate(pattern_buttons):
                    if button.collidepoint(event.pos):
                        current_pattern = f"Pattern{i + 1}"
                        if current_pattern not in lines:
                            lines[current_pattern] = []
                        reset_drawing()
                        break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if start_point is None:
                    start_point = current_position
                else:
                    lines[current_pattern].append((start_point, current_position))
                    start_point = current_position
            elif event.key == pygame.K_s:  # 'S' key to finish current line
                if start_point and current_position:
                    lines[current_pattern].append((start_point, current_position))
                start_point = None  # Allow starting a new sewing line
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                if current_position is None:
                    current_position = (WINDOW_SIZE // 2, WINDOW_SIZE // 2)
                x, y = current_position
                if event.key == pygame.K_UP:
                    y -= BLOCK_SIZE if not moving_fast else BLOCK_SIZE * 5
                elif event.key == pygame.K_DOWN:
                    y += BLOCK_SIZE if not moving_fast else BLOCK_SIZE * 5
                elif event.key == pygame.K_LEFT:
                    x -= BLOCK_SIZE if not moving_fast else BLOCK_SIZE * 5
                elif event.key == pygame.K_RIGHT:
                    x += BLOCK_SIZE if not moving_fast else BLOCK_SIZE * 5
                current_position = (x, y)

    # Draw current position
    if current_position:
        pygame.draw.circle(screen, DOT_COLOR, current_position, 3)

    pygame.display.flip()

pygame.quit()
