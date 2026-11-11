#!/usr/bin/env python3

import subprocess
import time
import resource
import re
import shlex
from datetime import datetime
from pathlib import Path

# ============================================================
# SIMULACION MESOSCOPICA DEFINITIVA - SUMO V3
# Configuracion MESO 4/6
# ============================================================

BASE = Path(__file__).resolve().parents[1]
CARPETA = Path(__file__).resolve().parent

FECHA = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
LOGS = CARPETA / "logs" / f"ejecucion_{FECHA}"

LOGS.mkdir(parents=True, exist_ok=True)

VEHICULOS = [3000, 3500, 4000, 4500, 5000, 5500]

# Tiempos reales obtenidos anteriormente con Bash time
TIEMPOS_ANTERIORES = {
    3000: (0.194, 0.164, 0.030),
    3500: (0.218, 0.194, 0.024),
    4000: (0.239, 0.214, 0.025),
    4500: (0.286, 0.261, 0.024),
    5000: (1.307, 1.282, 0.021),
    5500: (2.199, 2.159, 0.028)
}

resultados = []


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def extraer(texto, patron, defecto=None):
    m = re.search(patron, texto, re.MULTILINE)
    return float(m.group(1)) if m else defecto


def entero(texto, patron, defecto=0):
    valor = extraer(texto, patron)
    return int(valor) if valor is not None else defecto


def mostrar(mensaje=""):
    print(mensaje, flush=True)


# ============================================================
# EJECUCION DE UNA SIMULACION
# ============================================================

def simular(n):

    red = BASE / "red_5x5/red_5x5.net.xml"
    rutas = BASE / f"red_5x5/{n}_rutas/rutas_{n}.rou.xml"

    if not red.is_file() or not rutas.is_file():
        mostrar(f"ERROR: faltan archivos para {n} vehiculos")
        return

    comando = [
        "sumo",
        "-n", str(red),
        "-r", str(rutas),

        "--mesosim", "true",
        "--meso-ltm", "false",

        "--meso-junction-control", "true",
        "--meso-junction-control.limited", "true",
        "--meso-minor-penalty", "4",

        "--meso-tauff", "6.00",
        "--meso-taufj", "1.13",
        "--meso-taujf", "1.73",
        "--meso-taujj", "1.40",

        "--meso-edgelength", "98",
        "--meso-jam-threshold", "-1",
        "--meso-recheck", "0",
        "--meso-overtaking", "false",

        "--begin", "0",
        "--end", "3600",
        "--time-to-teleport", "300",

        "--duration-log.statistics", "true",
        "--no-step-log", "true",
        "--no-warnings", "true"
    ]

    mostrar(f"\n{'='*75}")
    mostrar(f"             MESO DEFINITIVO - {n} VEHICULOS")
    mostrar(f"{'='*75}")

    # Medicion del tiempo real y CPU
    cpu_antes = resource.getrusage(resource.RUSAGE_CHILDREN)
    inicio = time.perf_counter()

    proceso = subprocess.run(
        comando,
        cwd=BASE,
        capture_output=True,
        text=True
    )

    real = time.perf_counter() - inicio
    cpu_despues = resource.getrusage(resource.RUSAGE_CHILDREN)

    user = cpu_despues.ru_utime - cpu_antes.ru_utime
    sys = cpu_despues.ru_stime - cpu_antes.ru_stime

    salida = proceso.stdout

    archivo = LOGS / f"meso_{n}.log"

    if proceso.returncode != 0:
        archivo.write_text(
            f"ERROR EN SIMULACION {n}\n\n"
            + shlex.join(comando)
            + "\n\nSTDOUT:\n"
            + proceso.stdout
            + "\nSTDERR:\n"
            + proceso.stderr,
            encoding="utf-8"
        )

        mostrar(f"ERROR: consultar {archivo}")
        return

    # Numero de vehiculos finalizados
    fin = extraer(
        salida,
        r"Statistics \(avg of (\d+)\)"
    )

    if fin is None:
        archivo.write_text(salida, encoding="utf-8")
        mostrar("ERROR: no se encontraron estadisticas")
        return

    # Separar estadisticas de rendimiento y vehiculos
    partes = re.split(
        r"Statistics \(avg of \d+\):",
        salida,
        maxsplit=1
    )

    estadisticas = partes[1] if len(partes) > 1 else ""

    insertados = entero(
        salida,
        r"^\s*Inserted:\s*(\d+)"
    )

    loaded = entero(
        salida,
        r"^\s*Inserted:\s*\d+\s*\(Loaded:\s*(\d+)\)",
        insertados
    )

    running = entero(
        salida,
        r"^\s*Running:\s*(\d+)"
    )

    waiting = entero(
        salida,
        r"^\s*Waiting:\s*(\d+)"
    )

    teleports = entero(
        salida,
        r"^\s*Teleports:\s*(\d+)"
    )

    jam = entero(
        salida,
        r"^\s*Teleports:\s*\d+.*Jam:\s*(\d+)"
    )

    ruta_media = extraer(
        estadisticas,
        r"^\s*RouteLength:\s*([\d.]+)",
        0
    )

    velocidad = extraer(
        estadisticas,
        r"^\s*Speed:\s*([\d.]+)",
        0
    )

    duracion = extraer(
        estadisticas,
        r"^\s*Duration:\s*([\d.]+)",
        0
    )

    waitingtime = extraer(
        estadisticas,
        r"^\s*WaitingTime:\s*([\d.]+)",
        0
    )

    timeloss = extraer(
        estadisticas,
        r"^\s*TimeLoss:\s*([\d.]+)",
        0
    )

    departdelay = extraer(
        estadisticas,
        r"^\s*DepartDelay:\s*([\d.]+)",
        0
    )

    velocidad_kmh = velocidad * 3.6

    datos = {
        "n": n,
        "loaded": loaded,
        "insertados": insertados,
        "fin": int(fin),
        "running": running,
        "waiting": waiting,
        "teleports": teleports,
        "jam": jam,
        "ruta": ruta_media,
        "velocidad": velocidad,
        "velocidad_kmh": velocidad_kmh,
        "duracion": duracion,
        "waitingtime": waitingtime,
        "timeloss": timeloss,
        "departdelay": departdelay,
        "real": real,
        "user": user,
        "sys": sys
    }

    resultados.append(datos)

    anterior = TIEMPOS_ANTERIORES[n]

    # ========================================================
    # GUARDAR LOG INDIVIDUAL
    # ========================================================

    contenido = f"""
===========================================================
SIMULACION MESOSCOPICA DEFINITIVA - {n} VEHICULOS
===========================================================

FECHA: {datetime.now()}

CONFIGURACION:
Modelo: MESO convencional
Control intersecciones: true
Control limitado: true
Penalizacion: 4 segundos
Tauff: 6.00 segundos
Taufj: 1.13 segundos
Taujf: 1.73 segundos
Taujj: 1.40 segundos
Meso edgelength: 98 metros
Jam threshold: -1
Meso recheck: 0
Meso overtaking: false
Tiempo simulado: 0 - 3600 segundos
Time to teleport: 300 segundos

===========================================================
VEHICULOS
===========================================================

Loaded:       {loaded}
Inserted:     {insertados}
Finished:     {int(fin)}
Running:      {running}
Waiting:      {waiting}
Teleports:    {teleports}
Teleports Jam:{jam}

===========================================================
ESTADISTICAS MEDIAS DE VEHICULOS FINALIZADOS
===========================================================

RouteLength:  {ruta_media:.2f} m
Speed:        {velocidad:.2f} m/s
Speed:        {velocidad_kmh:.2f} km/h
Duration:     {duracion:.2f} s
WaitingTime:  {waitingtime:.2f} s
TimeLoss:     {timeloss:.2f} s
DepartDelay:  {departdelay:.2f} s

===========================================================
TIEMPOS LIMPIOS - MEDICION ANTERIOR
===========================================================

real: {anterior[0]:.3f} s
user: {anterior[1]:.3f} s
sys:  {anterior[2]:.3f} s

===========================================================
TIEMPOS DE ESTA EJECUCION
===========================================================

real: {real:.3f} s
user: {user:.3f} s
sys:  {sys:.3f} s

===========================================================
COMANDO UTILIZADO
===========================================================

{shlex.join(comando)}

===========================================================
SALIDA ORIGINAL DE SUMO
===========================================================

{salida}

===========================================================
FIN DEL LOG
===========================================================
"""

    archivo.write_text(
        contenido.strip() + "\n",
        encoding="utf-8"
    )

    # Mostrar resumen en consola
    mostrar(f"Loaded:       {loaded}")
    mostrar(f"Inserted:     {insertados}")
    mostrar(f"Finished:     {int(fin)}")
    mostrar(f"Running:      {running}")
    mostrar(f"Waiting:      {waiting}")
    mostrar(f"Teleports:    {teleports}")
    mostrar(f"Speed:        {velocidad:.2f} m/s")
    mostrar(f"Speed:        {velocidad_kmh:.2f} km/h")
    mostrar(f"Duration:     {duracion:.2f} s")
    mostrar(f"WaitingTime:  {waitingtime:.2f} s")
    mostrar(f"TimeLoss:     {timeloss:.2f} s")
    mostrar(f"DepartDelay:  {departdelay:.2f} s")
    mostrar(f"RouteLength:  {ruta_media:.2f} m")

    mostrar("\nTIEMPOS ACTUALES:")
    mostrar(
        f"real {real:.3f}s | "
        f"user {user:.3f}s | "
        f"sys {sys:.3f}s"
    )

    mostrar(f"\nLog guardado: {archivo.name}")


# ============================================================
# EJECUTAR TODAS LAS SIMULACIONES
# ============================================================

for n in VEHICULOS:
    simular(n)


# ============================================================
# RESUMEN GENERAL
# ============================================================

lineas = []

def resumen(linea=""):
    lineas.append(linea)
    mostrar(linea)


resumen("\n" + "=" * 125)
resumen("                 RESUMEN GENERAL - MESO DEFINITIVO 4/6")
resumen("=" * 125)

resumen(
    f"{'N':>5} "
    f"{'Loaded':>7} "
    f"{'Insert':>7} "
    f"{'Finish':>7} "
    f"{'Running':>8} "
    f"{'Waiting':>8} "
    f"{'Tele':>6} "
    f"{'Speed':>8} "
    f"{'Loss':>9} "
    f"{'WaitTime':>9} "
    f"{'Duration':>9} "
    f"{'Real':>8}"
)

resumen("-" * 125)

for r in resultados:

    resumen(
        f"{r['n']:5d} "
        f"{r['loaded']:7d} "
        f"{r['insertados']:7d} "
        f"{r['fin']:7d} "
        f"{r['running']:8d} "
        f"{r['waiting']:8d} "
        f"{r['teleports']:6d} "
        f"{r['velocidad']:8.2f} "
        f"{r['timeloss']:9.2f} "
        f"{r['waitingtime']:9.2f} "
        f"{r['duracion']:9.2f} "
        f"{r['real']:8.3f}"
    )

resumen("\nSpeed en m/s; Loss, WaitTime, Duration y Real en segundos.")
resumen("Las medias de SUMO corresponden a vehiculos finalizados.")

resumen("\n" + "=" * 90)
resumen("TIEMPOS LIMPIOS ORIGINALES")
resumen("=" * 90)

resumen(
    f"{'Vehiculos':>10} "
    f"{'Real':>10} "
    f"{'User':>10} "
    f"{'Sys':>10}"
)

for n in VEHICULOS:
    real, user, sys = TIEMPOS_ANTERIORES[n]
    resumen(
        f"{n:10d} "
        f"{real:10.3f} "
        f"{user:10.3f} "
        f"{sys:10.3f}"
    )

resumen("\n" + "=" * 90)
resumen("ESTADISTICAS ADICIONALES")
resumen("=" * 90)

for r in resultados:
    resumen(
        f"N={r['n']} | "
        f"Speed={r['velocidad_kmh']:.2f} km/h | "
        f"RouteLength={r['ruta']:.2f} m | "
        f"DepartDelay={r['departdelay']:.2f} s | "
        f"TeleportsJam={r['jam']} | "
        f"user={r['user']:.3f}s | "
        f"sys={r['sys']:.3f}s"
    )

resumen("\n" + "=" * 90)
resumen(f"SIMULACIONES COMPLETADAS: {len(resultados)}/{len(VEHICULOS)}")
resumen(f"CARPETA DE LOGS: {LOGS}")
resumen("=" * 90)

archivo_resumen = LOGS / "resumen_general.log"

archivo_resumen.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)

mostrar(f"\nResumen guardado en: {archivo_resumen}")
