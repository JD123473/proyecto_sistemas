#!/usr/bin/python3

import hal, time, serial

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
time.sleep(2)  # el UNO se reinicia al abrir el puerto

h = hal.component("movimiento_xz")
h.newpin("x_plus",  hal.HAL_BIT, hal.HAL_OUT)
h.newpin("x_minus", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("z_plus",  hal.HAL_BIT, hal.HAL_OUT)
h.newpin("z_minus", hal.HAL_BIT, hal.HAL_OUT)
h.ready()

UMBRAL = 0.0005      # cambio minimo de posicion entre lecturas
RETENCION = 0.3      # segundos que se mantiene la direccion tras el ultimo movimiento

# joint.0 = X, joint.1 = Z (trivkins coordinates=xz)
JOINTS = {'x': 'joint.0.motor-pos-cmd', 'z': 'joint.1.motor-pos-cmd'}

prev = {'x': None, 'z': None}
t_mov = {'x': 0, 'z': 0}
direccion = {'x': 0, 'z': 0}     # 1 = positivo, -1 = negativo, 0 = detenido
ultimo = None

def codigo_eje(d):
    return {1: 1, -1: 2, 0: 0}[d]

try:
    while True:
        time.sleep(0.05)
        ahora = time.time()

        for eje, pin in JOINTS.items():
            try:
                pos = hal.get_value(pin)
            except Exception:
                continue

            if prev[eje] is not None:
                delta = pos - prev[eje]
                if delta > UMBRAL:
                    direccion[eje] = 1
                    t_mov[eje] = ahora
                elif delta < -UMBRAL:
                    direccion[eje] = -1
                    t_mov[eje] = ahora
            prev[eje] = pos

            if ahora - t_mov[eje] > RETENCION:
                direccion[eje] = 0

        h['x_plus']  = (direccion['x'] == 1)
        h['x_minus'] = (direccion['x'] == -1)
        h['z_plus']  = (direccion['z'] == 1)
        h['z_minus'] = (direccion['z'] == -1)

        # decena = X, unidad = Z
        codigo = codigo_eje(direccion['x']) * 10 + codigo_eje(direccion['z'])
        if codigo != ultimo:
            ser.write(f'{codigo}\n'.encode())
            ultimo = codigo
except KeyboardInterrupt:
    pass
finally:
    ser.write(b'0\n')
    ser.close()
    raise SystemExit
