#!/usr/bin/python3

import hal, time, serial, traceback

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
time.sleep(2)  # el UNO se reinicia al abrir el puerto
ser.reset_input_buffer()

h = hal.component("movimiento_xz_motores")

# --- salidas ---
for nombre in ("x_plus", "x_minus", "z_plus", "z_minus",     # direccion (observar)
               "power_on", "power_off",                      # -> halui.machine.on/off
               "estop_activate", "estop_reset",              # -> halui.estop.activate/reset
               "mode_auto", "prog_run",                      # -> halui.mode.auto / program.run
               "x_home_sw", "z_home_sw",                     # -> joint.N.home-sw-in
               "held", "estop_btn", "run_btn"):              # estado de botones (observar)
    h.newpin(nombre, hal.HAL_BIT, hal.HAL_OUT)

# --- entradas ---
for nombre in ("is_on",            # <- halui.machine.is-on
               "estop_is_active",  # <- halui.estop.is-activated
               "is_auto"):         # <- halui.mode.is-auto
    h.newpin(nombre, hal.HAL_BIT, hal.HAL_IN)

h.ready()

UMBRAL = 0.0005      # cambio minimo de posicion entre lecturas
RETENCION = 0.2      # segundos que se mantiene la direccion tras el ultimo movimiento
PULSO = 0.2          # duracion de los pulsos hacia halui (s)
ESPERA = 0.6         # tiempo minimo entre ordenes repetidas (s)
CADUCIDAD = 0.5      # sin mensajes del Arduino en este tiempo = comunicacion perdida

JOINTS = {'x': 'joint.0.motor-pos-cmd', 'z': 'joint.1.motor-pos-cmd'}

prev = {'x': None, 'z': None}
t_mov = {'x': 0, 'z': 0}
direccion = {'x': 0, 'z': 0}
ultimo = None

pulsos = {}                       # pin -> instante en que termina el pulso
t_cmd = {'power': 0, 'estop': 0}

t_msg = 0                         # instante del ultimo mensaje valido
boton = e_boton = r_boton = False
r_prev = None
run_estado = 0                    # 0 libre, 1 pedido, 2 esperando modo auto
t_run = 0
buf = b''

def pulso(nombre, ahora):
    h[nombre] = True
    pulsos[nombre] = ahora + PULSO

def codigo_eje(d):
    return {1: 1, -1: 2, 0: 0}[d]

try:
    while True:
        time.sleep(0.02)
        ahora = time.time()

        # --- leer mensajes del Arduino ---
        buf += ser.read(64)
        while b'\n' in buf:
            linea, buf = buf.split(b'\n', 1)
            linea = linea.strip()
            if linea in (b'H0', b'H1'):
                boton = (linea == b'H1');   t_msg = ahora
            elif linea in (b'E0', b'E1'):
                e_boton = (linea == b'E1'); t_msg = ahora
            elif linea in (b'R0', b'R1'):
                r_boton = (linea == b'R1'); t_msg = ahora
            elif linea.startswith(b'L'):
                try:
                    v = int(linea[1:])
                    h['x_home_sw'] = bool(v // 10)
                    h['z_home_sw'] = bool(v % 10)
                    t_msg = ahora
                except ValueError:
                    pass

        fresco = (ahora - t_msg) < CADUCIDAD
        mantenido = boton and fresco                 # habilitar
        estop_pedido = e_boton or not fresco         # sin comunicacion = E-stop
        h['held'] = mantenido
        h['estop_btn'] = e_boton
        h['run_btn'] = r_boton

        # --- terminar pulsos vencidos ---
        for n in [n for n, t in pulsos.items() if ahora >= t]:
            h[n] = False
            del pulsos[n]

        # --- habilitar: la maquina sigue al boton ---
        if ('power_on' not in pulsos and 'power_off' not in pulsos
                and ahora - t_cmd['power'] > ESPERA):
            if mantenido and not h['is_on']:
                pulso('power_on', ahora);  t_cmd['power'] = ahora
            elif not mantenido and h['is_on']:
                pulso('power_off', ahora); t_cmd['power'] = ahora

        # --- paro: el E-stop sigue al boton ---
        if ('estop_activate' not in pulsos and 'estop_reset' not in pulsos
                and ahora - t_cmd['estop'] > ESPERA):
            if estop_pedido and not h['estop_is_active']:
                pulso('estop_activate', ahora); t_cmd['estop'] = ahora
            elif not estop_pedido and h['estop_is_active']:
                pulso('estop_reset', ahora);    t_cmd['estop'] = ahora

        # --- ejecutar: al presionar, modo auto y luego run ---
        if fresco:
            if r_prev is None:
                r_prev = r_boton            # no ejecutar por un estado previo
            elif r_boton and not r_prev:
                run_estado = 1
            r_prev = r_boton

        if run_estado == 1:
            if h['is_on']:
                pulso('mode_auto', ahora)
                run_estado = 2
                t_run = ahora
            else:
                run_estado = 0              # maquina apagada: se ignora
        elif run_estado == 2:
            if h['is_auto'] and ahora - t_run > 0.3:
                pulso('prog_run', ahora)
                run_estado = 0
            elif ahora - t_run > 2.0:
                run_estado = 0

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

        # decena = X, unidad = Z (0 detenido, 1 positivo, 2 negativo)
        codigo = codigo_eje(direccion['x']) * 10 + codigo_eje(direccion['z'])
        if codigo != ultimo:
            ser.write(f'{codigo}\n'.encode())
            ultimo = codigo
except KeyboardInterrupt:
    pass
except Exception:
    traceback.print_exc()
finally:
    try:
        h['power_off'] = True
        h['estop_activate'] = True
        time.sleep(0.3)
        ser.write(b'0\n')
        ser.close()
    except Exception:
        pass
    raise SystemExit
