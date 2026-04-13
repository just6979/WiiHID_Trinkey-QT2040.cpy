import gc
import time

import board
import displayio
import microcontroller
import neopixel
import terminalio
import usb_hid
from hid_gamepad import Gamepad
from adafruit_debouncer import Debouncer
from adafruit_display_text import label
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_hid.mouse import Mouse
from digitalio import DigitalInOut, Direction
from i2cdisplaybus import I2CDisplayBus
from wiichuck.nunchuk import Nunchuk

start_time = time.monotonic()

ORANGE = 0xFF8800
GREEN = 0x00FF00
BLUE = 0x0000FF
PURPLE = 0xFF0000
WHITE = 0xFFFFFF
BLACK = 0x000000

MODE_L_STICK = 0
MODE_D_PAD = 1
MODE_MOUSE = 2
MODES = ['L-Stick', 'D-Pad', 'Mouse']
mode = MODE_L_STICK

print(
    f'{board.board_id}: '
    f'UID 0x{microcontroller.cpu.uid.hex()}, '
    f'{microcontroller.cpu.frequency / 1000 / 1000} MHz, '
    f'{microcontroller.cpu.temperature:0.1f} °C'
)
print('Starting up...')

print(f'Setting up onboard NeoPixel')
status_neopixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.05)
status_neopixel.fill(ORANGE)

print(f'Setting up onboard Button')
onboard_button = DigitalInOut(board.BUTTON)
onboard_button.direction = Direction.INPUT
boot_button = Debouncer(onboard_button)

i2c = board.I2C()
print(f'Scanning I2C bus...')
i2c.try_lock()
devs = [hex(dev).upper() for dev in i2c.scan()]
print(f'Found {len(devs)} I2C devices: {devs}')
i2c.unlock()

DISPLAY_ADDRESS = 0x3C
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 32
display = None
try:
    displayio.release_displays()
    display_bus = I2CDisplayBus(i2c, device_address=DISPLAY_ADDRESS)
    display = SSD1306(display_bus, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)
    print(f'Found 128x32 OLED at {DISPLAY_ADDRESS:#X}')
except ValueError as e:
    print(f'No 128x32 OLED found at {DISPLAY_ADDRESS:#X}')

text_area = None
if display:
    root_group = displayio.Group()
    text_area = label.Label(
        terminalio.FONT,
        text=(MODES[mode]),
        color=WHITE,
        x=6,
        y=12
    )
    root_group.append(text_area)
    display.root_group = root_group

NUNCHUCK_ADDRESS = 0x52
nunchuk = None
try:
    nunchuk = Nunchuk(i2c, NUNCHUCK_ADDRESS)
    print(f'Found Wii Nunchuck at {NUNCHUCK_ADDRESS:#X}')
except ValueError:
    print(f'No Wii Nunchuck found at {NUNCHUCK_ADDRESS:#X}')

if not nunchuk:
    if not display:
        print('No Nunchuck nor Display')
        status_neopixel.fill(PURPLE)
        while True: time.sleep(10)
    else:
        msg = 'No Nunchuck'
        print(msg)
        text_area.text = msg
        status_neopixel.fill(PURPLE)
        while True: time.sleep(10)

deadzone = 10

gamepad = Gamepad(usb_hid.devices)

mouse = Mouse(usb_hid.devices)
sensitivity = 33
left_down = False
right_down = False
middle_down = False

jx = jy = 127
ax = ay = az = 0
jz = jc = False

# check the environment every 5 seconds
ENV_READ_DELAY = 5
last_env_read = 0

if display or nunchuk:
    status_neopixel.fill(BLUE)

if display and nunchuk:
    status_neopixel.fill(GREEN)

print(f'Setup complete: {time.monotonic() - start_time // 1000} ms')
gc.collect()
print(f'Free Memory: {gc.mem_free() // 1024} KB')

DISPLAY_UPDATE_DELAY = 0.016
WII_READ_DELAY = 0.002
last_display_update = 0
last_wii_read = 0

while True:
    now = time.monotonic()

    boot_button.update()
    if boot_button.rose:
        mode += 1
        # TODO: implement d-pad in hid_gamepad.py
        if mode == MODE_D_PAD: mode += 1
        if mode >= len(MODES): mode = 0
        text_area.text = MODES[mode]
        print(MODES[mode])

    if now - last_env_read >= ENV_READ_DELAY:
        last_env_read = now
        print(f'{now:.3f}s: MCU Temp: {microcontroller.cpu.temperature:.1f} °C')

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

        # normalize axis values between -127 to 127
        jx -= 127
        jy -= 127
        if jx > 127: jx = 127
        if jy > 127: jy = 127

        # flip y-axis values to match modern gamepad HID
        jy *= -1

        if jx != 0 or jy != 0 or jz or jc:
            msg = f'[{'Z' if jz else ' '}{'C' if jc else ' '}] J[{jx: 4},{jy: 4}] A[{ax:3},{ay:3},{az:3}]'
            print(f'{now:.3f}: {msg}')

        if mode == MODE_L_STICK:
            if jz:
                gamepad.press_buttons(1)
            else:
                gamepad.release_buttons(1)
            if jc:
                gamepad.press_buttons(2)
            else:
                gamepad.release_buttons(2)
            gamepad.move_joysticks(jx, jy)

        # if mode == MODE_D_PAD:
        #     gamepad.move_dpad(jx, jy)

        if mode == MODE_MOUSE:
            x = (sensitivity * (jx) // 255)
            y = (sensitivity * (jy) // 255)
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

    # if display and now - last_display_update >= DISPLAY_UPDATE_DELAY:
    #     last_display_update = now
    #     text_area.text = f'{MODES[mode]}\n[{'Z' if jz else ' '}{'C' if jc else ' '}] [{jx: 4},{jy: 4}]'
