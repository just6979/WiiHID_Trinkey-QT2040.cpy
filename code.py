import gc
import time

import board
import displayio
import microcontroller
import neopixel
import terminalio
import usb_hid
from Gamepad import Gamepad
from adafruit_debouncer import Debouncer
from adafruit_display_text import label
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_hid.mouse import Mouse
from digitalio import DigitalInOut, Direction
from i2cdisplaybus import I2CDisplayBus
from wiichuck.nunchuk import Nunchuk

start_time = time.monotonic()

MODES = ['L-Stick', 'D-Pad', 'Mouse']
mode = 1

print(
    f'{board.board_id}: '
    f'UID 0x{microcontroller.cpu.uid.hex()}, '
    f'{microcontroller.cpu.frequency / 1000 / 1000} MHz, '
    f'{microcontroller.cpu.temperature:0.1f} °C'
)
print('Starting up...')

print(f'Setting up onboard NeoPixel')
status_neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.05)
status_neopixel.fill(0xFF8800)
time.sleep(0.5)

print(f'Setting up onboard Button')
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

SCREEN_ADDRESS = 0x3C
DISPLAY_UPDATE_DELAY = 0.016
last_display_update = 0
display = None
try:
    displayio.release_displays()
    display_bus = I2CDisplayBus(i2c, device_address=SCREEN_ADDRESS)
    display = SSD1306(display_bus, width=128, height=64)
    display.rotation = 180
    print(f'Found 128x32 OLED at {SCREEN_ADDRESS:#x}')
except ValueError as e:
    print(f'No 128x32 OLED found at {SCREEN_ADDRESS:#x}')

NUNCHUCK_ADDRESS = 0x52
WII_READ_DELAY = 0.002
last_wii_read = 0
nunchuk = None
try:
    nunchuk = Nunchuk(i2c, NUNCHUCK_ADDRESS)
    print(f'Found Wii Nunchuck at {NUNCHUCK_ADDRESS:#x}')
except ValueError:
    print(f'No Wii Nunchuck found at {NUNCHUCK_ADDRESS:#x}')

if not display and not nunchuk:
    print('Cannot find Nunchuck or Display')
    status_neopixel.fill(0xFF0000)
    while True: time.sleep(10)

text_area = None
if display:
    BORDER = 5
    splash = displayio.Group()
    display.root_group = splash

    color_bitmap = displayio.Bitmap(display.width, display.height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    inner_bitmap = displayio.Bitmap(display.width - BORDER * 2, display.height - BORDER * 2, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0x000000
    inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER)
    splash.append(inner_sprite)

    text = MODES[mode]
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=display.height // 2 - 1)
    splash.append(text_area)

    display.root_group = splash

deadzone = 20

# gamepad = Gamepad(usb_hid.devices)

mouse = Mouse(usb_hid.devices)
sensitivity = 33
left_down = False
right_down = False
middle_down = False

jx = jy = 127
ax = ay = az = 0
jz = jc = False

pixel_x = 6
pixel_y = 4
old_x = old_y = 0

# check the environment every 5 seconds
ENV_READ_DELAY = 5
last_env_read = 0

if display or nunchuk:
    status_neopixel.fill(0x0000FF)

if display and nunchuk:
    status_neopixel.fill(0x00FF00)

print(f'Setup complete: {time.monotonic() - start_time}s')
gc.collect()
print(gc.mem_free())

while True:
    now = time.monotonic()

    boot_button.update()
    if boot_button.rose:
        mode += 1
        if mode >= len(MODES): mode = 0
        text = MODES[mode]
        print(MODES[mode])

    if now - last_env_read >= ENV_READ_DELAY:
        last_env_read = now
        print(f'{now:.3f}s: MCU Temp: {microcontroller.cpu.temperature} °C')

    if nunchuk and now - last_wii_read >= WII_READ_DELAY:
        last_wii_read = now
        jx, jy = nunchuk.joystick
        ax, ay, az = nunchuk.acceleration
        jc, jz = nunchuk.buttons

        if jx > 127 > jx - deadzone:
            jx = 127
        if jx < 127 < jx + deadzone:
            jx = 127
        if jy > 127 > jy - deadzone:
            jy = 127
        if jy < 127 < jy + deadzone:
            jy = 127

        if jx != 127 or jy != 127 or jz or jc:
            msg = f'[{'Z' if jz else ' '}{'C' if jc else ' '}] J[{jx:>3},{jy:>3}] A[{ax:>3},{ay:>3},{az:>3}]'
            print(f'{now:.3f}: {msg}')

        if mode == 0:
            # gamepad.move_joysticks(jx, jy)
            pass

        if mode == 1:
            # gamepad.move_dpad(jx, jy)
            pass

        if mode == 2:
            x = (sensitivity * (jx - 127) // 255)
            y = (sensitivity * (jy - 127) // 255)
            mouse.move(x, -y)
            if jz and jc:
                mouse.press(Mouse.MIDDLE_BUTTON)
                middle_down = True
            elif middle_down:
                mouse.release(Mouse.MIDDLE_BUTTON)
                middle_down = False
            if jz:
                mouse.press(Mouse.LEFT_BUTTON)
                left_down = True
            elif left_down:
                mouse.release(Mouse.LEFT_BUTTON)
                left_down = False
            if jc:
                mouse.press(Mouse.RIGHT_BUTTON)
                right_down = True
            elif right_down:
                mouse.release(Mouse.RIGHT_BUTTON)
                right_down = False

    if display and now - last_display_update >= DISPLAY_UPDATE_DELAY:
        last_display_update = now
        text_area.text = MODES[mode]
