#!/usr/bin/python3

import hal, time, serial

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
time.sleep(2)  # el UNO se reinicia al abrir el puerto

h = hal.component("arduino")
h.newpin("moving_x", hal.HAL_BIT, hal.HAL_OUT)  # solo para observar
h.ready()

UMBRAL = 0.0005      # cambio minimo de posicion entre lecturas
RETENCION = 0.3      # segundos que sigue encendido tras el ultimo movimiento

prev = None
t_mov = 0
ultimo = None
try:
    while True:
        time.sleep(0.05)
        try:
            pos = hal.get_value('joint.0.motor-pos-cmd')
        except Exception:
            continue
        if prev is not None and abs(pos - prev) > UMBRAL:
            t_mov = time.time()
        prev = pos

        moviendo = (time.time() - t_mov) < RETENCION
        h['moving_x'] = moviendo
        estado = 1 if moviendo else -1
        if estado != ultimo:
            ser.write(f'{estado}\n'.encode())
            ultimo = estado
except KeyboardInterrupt:
    pass
finally:
    ser.write(b'-1\n')
    ser.close()
    raise SystemExit
