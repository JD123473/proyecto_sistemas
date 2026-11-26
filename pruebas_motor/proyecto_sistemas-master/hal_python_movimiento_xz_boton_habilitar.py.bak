#!/usr/bin/python3

import hal, time, serial

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
time.sleep(2)  # el UNO se reinicia al abrir el puerto
ser.reset_input_buffer()

h = hal.component("movimiento_xz_boton_habilitar")
h.newpin("x_plus",    hal.HAL_BIT, hal.HAL_OUT)
h.newpin("x_minus",   hal.HAL_BIT, hal.HAL_OUT)
h.newpin("z_plus",    hal.HAL_BIT, hal.HAL_OUT)
h.newpin("z_minus",   hal.HAL_BIT, hal.HAL_OUT)
h.newpin("is_on",     hal.HAL_BIT, hal.HAL_IN)    # <- halui.machine.is-on
h.newpin("power_on",  hal.HAL_BIT, hal.HAL_OUT)   # -> halui.machine.on
h.newpin("power_off", hal.HAL_BIT, hal.HAL_OUT)   # -> halui.machine.off
h.newpin("held",      hal.HAL_BIT, hal.HAL_OUT)   # boton mantenido (para observar)
h.ready()

UMBRAL = 0.0005      # cambio minimo de posicion entre lecturas
RETENCION = 0.3      # segundos que se mantiene la direccion tras el ultimo movimiento
PULSO = 0.2          # duracion del pulso de power on/off (s)
ESPERA = 0.6         # tiempo minimo entre pulsos consecutivos (s)
CADUCIDAD = 0.5      # sin mensaje del boton en este tiempo = suelto

JOINTS = {'x': 'joint.0.motor-pos-cmd', 'z': 'joint.1.motor-pos-cmd'}

prev = {'x': None, 'z': None}
t_mov = {'x': 0, 'z': 0}
direccion = {'x': 0, 'z': 0}
ultimo = None
t_pulso = 0
t_ultimo_cmd = 0
t_msg = 0            # instante del ultimo mensaje del boton
boton = False
buf = b''

def codigo_eje(d):
    return {1: 1, -1: 2, 0: 0}[d]

try:
    while True:
        time.sleep(0.05)
        ahora = time.time()

        # --- leer el boton del Arduino ---
        buf += ser.read(64)
        while b'\n' in buf:
            linea, buf = buf.split(b'\n', 1)
            linea = linea.strip()
            if linea == b'H1':
                boton = True
                t_msg = ahora
            elif linea == b'H0':
                boton = False
                t_msg = ahora

        # sin mensajes recientes = se considera suelto
        mantenido = boton and (ahora - t_msg < CADUCIDAD)
        h['held'] = mantenido

        # --- terminar el pulso en curso ---
        if t_pulso and ahora - t_pulso > PULSO:
            h['power_on'] = False
            h['power_off'] = False
            t_pulso = 0

        # --- la maquina sigue al boton ---
        if t_pulso == 0 and ahora - t_ultimo_cmd > ESPERA:
            if mantenido and not h['is_on']:
                h['power_on'] = True
                t_pulso = t_ultimo_cmd = ahora
            elif not mantenido and h['is_on']:
                h['power_off'] = True
                t_pulso = t_ultimo_cmd = ahora

        # --- direccion de los ejes ---
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

        codigo = codigo_eje(direccion['x']) * 10 + codigo_eje(direccion['z'])
        if codigo != ultimo:
            ser.write(f'{codigo}\n'.encode())
            ultimo = codigo
except KeyboardInterrupt:
    pass
finally:
    try:
        h['power_on'] = False
        h['power_off'] = True      # al salir, la maquina se apaga
        time.sleep(0.3)
        ser.write(b'0\n')
        ser.close()
    except Exception:
        pass
    raise SystemExit
