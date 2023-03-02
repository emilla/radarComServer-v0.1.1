import time
import board
import busio
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont


class Display:
    def __init__(self, width, height, addr, reset_pin=board.D4):
        # Define the Reset Pin
        self.oled_reset = digitalio.DigitalInOut(reset_pin)
        # Display Parameters
        self.width = width
        self.height = height

        # Create blank image for drawing.
        self.image = Image.new('1', (width, height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # Load the font
        self.font = font = ImageFont.load_default()

        # Create the display
        self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, busio.I2C(board.SCL, board.SDA), addr=addr,
                                                 reset=self.oled_reset)

    # Clear the display
    def clear_display(self):
        # Clear display.
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    # Draw text on the display
    def draw_text(self, text):
        self.font = ImageFont.truetype('PixelOperator.ttf', 50)
        self.icon_font = ImageFont.truetype('lineawesome-webfont.ttf', 50)
        self.clear_display()
        self.draw.text((0, 0), text, font=self.font, fill=255)
        self.oled.image(self.image)
        self.oled.show()

# # Test the display
# if __name__ == '__main__':
#     display = OLED_Display(128, 64, 0x3C, board.D4, 'lineawesome-webfont.ttf')

#     while True:
#         # Update the display with a single character
#         display.draw_text('A')

#         # Wait for a period of time before updating the display again
#         time.sleep(1.0)
