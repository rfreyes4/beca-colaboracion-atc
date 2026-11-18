#!/usr/bin/env python3
"""MICRO V4: semaforos base + progresivos; rutas estaticas y dinamicas."""

from collections import deque
from pathlib import Path
import subprocess

BASE = Path.cwd()
SALIDA = BASE / "micro" / "progresivos"
DEMANDAS = [3000, 4000, 5000, 6000, 7000, 8000, 9000, 11000]
SEMAFOROS = [
    "red_7x7/semaforos.add.xml",
    "red_7x7/semaforos_progresivos_rectas.add.xml",
]
RED = "red_7x7/red_7x7.net.xml"

# Verificar todas las entradas ANTES de empezar a simular.
entradas = [RED, *SEMAFOROS]
entradas += [f"red_7x7/{n}_rutas/rutas_{n}.rou.xml" for n in DEMANDAS]
no_existen = [nombre for nombre in entradas if not (BASE / nombre).is_file()]
if no_existen:
    raise SystemExit("ERROR: faltan estos archivos:\n" + "\n".join(no_existen))

print("MICRO V4 - SEMAFOROS BASE + PROGRESIVOS", flush=True)
print("Carpeta de trabajo:", BASE, flush=True)
print("Archivos semaforicos:", ", ".join(SEMAFOROS), flush=True)

for modo in ("estatico", "dinamico"):
    carpeta = SALIDA / modo
    carpeta.mkdir(parents=True, exist_ok=True)

    for n in DEMANDAS:
        print(f"\n{'=' * 60}", flush=True)
        print(f"MICRO {modo.upper()} | {n} VEHICULOS", flush=True)
        print("=" * 60, flush=True)

        comando = [
            "sumo",
            "-n", RED,
            "-r", f"red_7x7/{n}_rutas/rutas_{n}.rou.xml",
            "-a", ",".join(SEMAFOROS),
            "--begin", "0",
            "--end", "3600",
            "--seed", "42",
            "--time-to-teleport", "300",
            "--device.rerouting.probability", "0" if modo == "estatico" else "1",
            "--no-step-log", "true",
        ]
        if modo == "dinamico":
            comando += ["--device.rerouting.period", "120"]

        # Ejecucion completa: estadisticas, avisos y tiempo real/user/sys.
        archivo = carpeta / f"micro_{n}.log"
        completo = comando + ["--duration-log.statistics", "true", "--verbose", "true"]
        with archivo.open("w", encoding="utf-8") as log:
            resultado = subprocess.run(
                ["bash", "-c", 'time -p "$@"', "bash", *completo],
                cwd=BASE, stdout=log, stderr=subprocess.STDOUT,
                check=False,
            )
        if resultado.returncode:
            raise SystemExit(f"ERROR en {modo}, {n}. Revisa: {archivo}")

        # Comprobar que SUMO realmente haya cargado LOS DOS archivos.
        with archivo.open(encoding="utf-8", errors="replace") as log:
            ultimas = deque(log, maxlen=23)
            log.seek(0)
            cargados = log.read()
        for semaforo in SEMAFOROS:
            if f"Loading additional-files from '{semaforo}'" not in cargados:
                raise SystemExit(f"ERROR: no consta carga de {semaforo}. Revisa {archivo}")

        print("\nRESULTADOS COMPLETOS (ultimas lineas):", flush=True)
        print("".join(ultimas), flush=True)

        # Ejecucion limpia: misma simulacion, sin informes por pantalla.
        archivo_limpio = carpeta / f"micro_{n}_limpio.log"
        with archivo_limpio.open("w", encoding="utf-8") as log:
            resultado = subprocess.run(
                ["bash", "-c", 'time -p "$@" >/dev/null 2>&1', "bash", *comando],
                cwd=BASE, stdout=log, stderr=subprocess.STDOUT,
                check=False,
            )
        if resultado.returncode:
            raise SystemExit(f"ERROR en tiempo limpio {modo}, {n}.")
        print("TIEMPOS LIMPIOS:", flush=True)
        print(archivo_limpio.read_text(encoding="utf-8"), flush=True)

print("\nTODAS LAS PRUEBAS MICRO PROGRESIVAS FINALIZADAS", flush=True)
print("Resultados guardados en:", SALIDA, flush=True)
