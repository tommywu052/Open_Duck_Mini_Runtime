import board
import neopixel
import time
import colorsys
import argparse
import sys

# Configuration
LED_COUNT = 8
LED_PIN = board.D18
LED_BRIGHTNESS = 0.4
LED_ORDER = neopixel.GRB

DELAY = 0.06
GRADIENT_SPREAD = 0.05
TAIL_LENGTH = 8

pixels = neopixel.NeoPixel(
    LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS,
    auto_write=False, pixel_order=LED_ORDER
)

def parse_color(color_str):
    """Parses a hex color string like 'FF0000' or '255,0,0'"""
    if ',' in color_str:
        return tuple(int(x.strip()) for x in color_str.split(','))
    elif len(color_str) == 6:
        return tuple(int(color_str[i:i+2], 16) for i in (0, 2, 4))
    else:
        raise ValueError("Color must be 'R,G,B' or 6-digit hex (e.g., 'FF0000')")

def flowing_light(color=(255, 0, 0), delay=0.08):
    while True:
        for i in range(LED_COUNT):
            pixels.fill((0, 0, 0))
            pixels[i] = color
            pixels.show()
            time.sleep(delay)

def fancy_gradient_flow():
    hue_offset = 0.0
    while True:
        for i in range(LED_COUNT):
            hue = (hue_offset + i * GRADIENT_SPREAD) % 1.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
            pixels[i] = (r, g, b)
        pixels.show()
        hue_offset = (hue_offset + 0.01) % 1.0
        time.sleep(DELAY)

def white_flow_round_trip():
    direction = 1
    pos = 0
    while True:
        pixels.fill((0, 0, 0))
        for i in range(TAIL_LENGTH):
            fade = (TAIL_LENGTH - i) / TAIL_LENGTH
            index = pos - i * direction
            if 0 <= index < LED_COUNT:
                intensity = int(255 * fade)
                pixels[index] = (intensity, intensity, intensity)
        pixels.show()
        pos += direction
        if pos >= LED_COUNT + TAIL_LENGTH:
            direction = -1
            pos = LED_COUNT - 1
        elif pos < -TAIL_LENGTH:
            direction = 1
            pos = 0
        time.sleep(DELAY)

def white_flow_round_trip(color=(0, 255, 255)):
    direction = 1  # 1 = forward, -1 = backward
    pos = 0

    while True:
        pixels.fill((0, 0, 0))  # Clear all LEDs

        for i in range(TAIL_LENGTH):
            fade = (TAIL_LENGTH - i) / TAIL_LENGTH
            index = pos - i * direction
            if 0 <= index < LED_COUNT:
                r = int(color[0] * fade)
                g = int(color[1] * fade)
                b = int(color[2] * fade)
                pixels[index] = (r, g, b)

        pixels.show()
        pos += direction

        if pos >= LED_COUNT + TAIL_LENGTH:
            direction = -1
            pos = LED_COUNT - 1
        elif pos < -TAIL_LENGTH:
            direction = 1
            pos = 0

        time.sleep(DELAY)


# === Main ===

def main():
    parser = argparse.ArgumentParser(description="WS2812B LED Animation Controller")
    parser.add_argument('--mode', required=True, choices=['flow', 'gradient', 'white'],
                        help="Animation mode: flow, gradient, white")
    parser.add_argument('--color', default='00FFFF',  # cyan default
                        help="Color in hex (FF00FF) or RGB (0,255,255) format; used for flow and white modes")

    args = parser.parse_args()

    # Parse color only if mode needs it
    if args.mode in ['flow', 'white']:
        try:
            color = parse_color(args.color)
        except argparse.ArgumentTypeError as e:
            print(f"Invalid color format: {e}")
            sys.exit(1)
    else:
        color = None  # gradient mode ignores color

    try:
        if args.mode == 'flow':
            flowing_light(color=color)
        elif args.mode == 'gradient':
            fancy_gradient_flow()
        elif args.mode == 'white':
            white_flow_round_trip(color=color)
    except KeyboardInterrupt:
        pixels.fill((0, 0, 0))
        pixels.show()
        print("\nStopped.")

if __name__ == '__main__':
    main()