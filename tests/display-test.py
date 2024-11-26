#!/usr/bin/env python3

import time
import st7789
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont

# Initialize display
disp = st7789.ST7789(
    height=240,
    width=240,
    rotation=90,
    port=0,
    cs=1,
    dc=9,
    backlight=13,
    spi_speed_hz=80_000_000
)

def test_display():
    try:
        # Initialize display
        disp.begin()
        
        # Create canvas
        image = Image.new('RGB', (240, 240), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            print("Could not load font, falling back to default")
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw test pattern
        
        # 1. Red background
        draw.rectangle([(0, 0), (240, 60)], fill=(255, 0, 0))
        draw.text((20, 20), "Red", font=font, fill=(255, 255, 255))
        
        # 2. Green section
        draw.rectangle([(0, 60), (240, 120)], fill=(0, 255, 0))
        draw.text((20, 80), "Green", font=font, fill=(0, 0, 0))
        
        # 3. Blue section
        draw.rectangle([(0, 120), (240, 180)], fill=(0, 0, 255))
        draw.text((20, 140), "Blue", font=font, fill=(255, 255, 255))
        
        # 4. Text section
        draw.rectangle([(0, 180), (240, 240)], fill=(255, 255, 255))
        draw.text((20, 190), "Display Test", font=font, fill=(0, 0, 0))
        draw.text((20, 220), "Press Ctrl+C to exit", font=small_font, fill=(0, 0, 0))
        
        # Show the image
        disp.display(image)
        print("Display test pattern shown. Press Ctrl+C to exit.")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTest completed")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    test_display()
