Using [Adafruit Trinkey QT2040](https://www.adafruit.com/product/5056),
[CircuitPython WiiChuck library](https://github.com/jfurcean/CircuitPython_WiiChuck),
and various Adafruit CircuitPython libraries, to turn a Wii Nunchuck
into a simple joystick/gamepad and* mouse emulator.

* Modes are switched with Button 0 on the Trinkey.
  * Button 0 is the only one kept easily accessible in my little stack of
    Trinkey sandwiched between the Nunchuck adapter and display.
  * ? Long press or double press for a menu to configure each mode ?
* Attached OLED (128x32) will display the modes and other info.

* Modes:
  * Nunchuck
    * L-Stick
      * Nunchuck stick Left-stick signals
      * Z sends Button 1 (South, XBox A, Nintendo B, PS Circle)
      * C sends Button 2 (East, XBox B, Nintendo A, PS X)
    * D-Pad
      * Nunchuck stick sends d-pad/hat signals
      * Buttons same as L-Stick Mode
    * Mouse
      * Nunchuck stick sends mouse move signals
        * Z & C buttons send Left & Right clicks, respectively
        * ? Both together send middle click ?
    * ? R-Stick ?
      * Same as L-Stick but send Right Stick
      * ? Maybe ?
  * Classic
    * Pass
      * Just acts like a gamepad
      * 2 axes, 2 triggers (3rd axis?), hat, 9 buttons (7 face, 2 shoulder)
        * No clickable sticks, so no L3/R3.
        * ? Treat full trigger pulls as 2 more buttons like on the GameCube controller ?
    * Flip
      * Same as Pass-through but L-Stick and D-Pad are swapped
    * Mixed
      * Left stick sends left stick
      * D-pad sends D-pad
      * Right stick sends mouse
      * Buttons send normal gamepad buttons, plus:
        * Full trigger pulls send left & right mouse clicks, either Z button sends middle click.
    * ? All Mouse ?
      * Both sticks and D-pad send mouse movement
      * Full trigger pulls send left & right mouse clicks, either Z button sends middle click
      * Y or Minus: LMB, A or Plus: RMB, X, B, or Home: MMB
      * ? Maybe ?
      
*  Neopixel will indicate the mode:
  * Nunchuck
    * [*L*ight] Blue for *L*-stick
    * *D*ark Blue for *D*-Pad
    * *M*agenta for *M*ouse
    * *G*reen for *G*ame
  * Classic
    * *P*ink for *P*ass
    * *F*uscia for *F*lip
    * *M*agenta for *M*ixed
    * If All Mouse exists:
      * White for Mixed (all colors for all modes)
      * *M*agenta is for All *M*ouse

* Next
  * Remember the mode
  * New modes:
    * Accel mouse
    * Joystick on stick, mouse on accel
    * All modes at once
  * Long press button in mouse mode to change sensitivity
  * configuration:
    * filesystem over USB?
    * nunchuck stick deadzones to account for worn ones that are drifty
    * button mapping
