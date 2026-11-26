#!/usr/bin/python3

import hal, time, serial

ser = serial.Serial('/dev/ttyACM0', 115200)

h = hal.component("arduino")

# --- joint x ---

h.newpin("in_x", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("out_x", hal.HAL_FLOAT, hal.HAL_OUT)

# --- joint z ---

h.newpin("in_z", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("out_z", hal.HAL_FLOAT, hal.HAL_OUT)

h.ready()

# --- bucle para que no desaparezca ---

try: 
    while True:
        time.sleep(0.1)
        val = hal.get_value('arduino.in_x')
        val = int(val)
        ser.write(f'{val}\n'.encode())

        
except KeyboardInterrupt:
    raise SystemExit

