#!/usr/bin/python3

import hal, time, serial

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
time.sleep(2)  # el UNO se reinicia al abrir el puerto

h = hal.component("movimiento_x")
h.newpin("x_plus",  hal.HAL_BIT, hal.HAL_OUT)   # X+ (para observar)
h.newpin("x_minus", hal.HAL_BIT, hal.HAL_OUT)   # X- (para observar)
h.ready()

UMBRAL = 0.0005      # cambio minimo de posicion entre lecturas
RETENCION = 0.3      # segundos que se mantiene la direccion tras el ultimo movimiento

prev = None
t_mov = 0
direccion = 0        # 1 = X+, -1 = X-, 0 = detenido
ultimo = None

try:
    while True:
        time.sleep(0.05)
        try:
            pos = hal.get_value('joint.0.motor-pos-cmd')
        except Exception:
            continue

        if prev is not None:
            delta = pos - prev
            if delta > UMBRAL:
                direccion = 1
                t_mov = time.time()
            elif delta < -UMBRAL:
                direccion = -1
                t_mov = time.time()
        prev = pos

        if time.time() - t_mov > RETENCION:
            direccion = 0

        h['x_plus']  = (direccion == 1)
        h['x_minus'] = (direccion == -1)

        # codigo para el Arduino: 1 = X+ (amarillo), 2 = X- (blanco), -1 = detenido
        codigo = {1: 1, -1: 2, 0: -1}[direccion]
        if codigo != ultimo:
            ser.write(f'{codigo}\n'.encode())
            ultimo = codigo
except KeyboardInterrupt:
    pass
finally:
    ser.write(b'-1\n')
    ser.close()
    raise SystemExit
