import time

import adafruit_displayio_ssd1306
import board
import displayio
import microcontroller
import neopixel
import terminalio
from adafruit_debouncer import Debouncer
from adafruit_display_text import label
from digitalio import DigitalInOut, Direction
from i2cdisplaybus import I2CDisplayBus
from wiichuck.nunchuk import Nunchuk

displayio.release_displays()

MODES = ['L-Stick', 'D-Pad', 'Mouse']
current_mode = 1

time.sleep(1)

print(
    f'{board.board_id}: '
    f'UID 0x{microcontroller.cpu.uid.hex()}, '
    f'{microcontroller.cpu.frequency / 1000 / 1000} MHz, '
    f'{microcontroller.cpu.temperature} C'
)

status_neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.05)
status_neopixel.fill(0xFF8800)

onboard_button = DigitalInOut(board.BUTTON)
onboard_button.direction = Direction.INPUT
boot_button = Debouncer(onboard_button)

i2c = board.I2C()
print(f'Opened I2C bus')
i2c.try_lock()
print(f'Scanning for devices')
devs = [hex(dev) for dev in i2c.scan()]
print(f'Found {len(devs)} I2C devices: {devs}')
i2c.unlock()

text_to_show = MODES[current_mode]

display_bus = I2CDisplayBus(i2c, device_address=0x3C,)

WIDTH = 128
HEIGHT = 32
BORDER = 5
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)
display.rotation = 180

splash = displayio.Group()
display.root_group = splash

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER)
splash.append(inner_sprite)

text = MODES[current_mode]
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=HEIGHT // 2 - 1)
splash.append(text_area)

display.root_group = splash

nunchuk_addr = 0x52

status_neopixel.fill(0x0000FF)

try:
    nunchuk = Nunchuk(i2c, nunchuk_addr)
    print(f'Found Wii Nunchuck at {nunchuk_addr:#x}')
except ValueError:
    print(f'No Wii Nunchuck found at {nunchuk_addr:#x}')

wii_read_delay = 0.002
last_wii_read = 0

status_neopixel.fill(0x00FF00)

jx = jy = 127
ax = ay = az = 0
jz = jc = False

pixel_x = 6
pixel_y = 4
old_x = old_y = 0

while True:
    now = time.monotonic()

    boot_button.update()
    if boot_button.rose:
        current_mode += 1
        if current_mode >= len(MODES): current_mode = 0s
        text = MODES[current_mode]
        print(MODES[current_mode])

    if nunchuk and now - last_wii_read >= wii_read_delay:
        last_wii_read = now
        jx, jy = nunchuk.joystick
        ax, ay, az = nunchuk.acceleration
        jc, jz = nunchuk.buttons
        msg = f'J[{jx:>3},{jy:>3}] A[{ax:>3},{ay:>3},{az:>3}] [{'Z' if jz else ' '}{'C' if jc else ' '}]'
        # print(msg)

    text_area.text = MODES[current_mode]
