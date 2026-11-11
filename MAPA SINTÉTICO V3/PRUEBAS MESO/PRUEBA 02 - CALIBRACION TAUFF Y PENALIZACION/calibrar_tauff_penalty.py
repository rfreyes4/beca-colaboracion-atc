#!/usr/bin/env python3

import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean

# ============================================================
# PRUEBA 02 - CALIBRACION TAUFF Y PENALIZACIONES
# ============================================================

BASE = Path(__file__).resolve().parents[2]
CARPETA = Path(__file__).resolve().parent
LOGS = CARPETA / "logs"

LOGS.mkdir(parents=True, exist_ok=True)

ARCHIVO_LOG = LOGS / f"resultados_{datetime.now():%Y%m%d_%H%M%S}.log"

# Parametros de las pruebas
VEHICULOS = [3500, 4000, 4500, 5000, 5500]
TAUFF = [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
PENALIZACIONES = [0, 2, 4, 6, 8, 9, 10]

# Pesos utilizados para calcular el error
PESO_LOSS = 0.50
PESO_FIN = 0.30
PESO_TELE = 0.20

referencias = {}
resultados = {}

contador = 0
total = len(VEHICULOS) * (
    1 + len(TAUFF) * len(PENALIZACIONES)
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def mostrar(linea=""):
    print(linea, flush=True)

    with ARCHIVO_LOG.open("a", encoding="utf-8") as log:
        log.write(linea + "\n")


def extraer(texto, expresion, defecto=None):
    coincidencia = re.search(
        expresion, texto, re.MULTILINE
    )

    if coincidencia:
        return float(coincidencia.group(1))

    return defecto


# ============================================================
# CALCULO DEL ERROR
# ============================================================

def evaluar(meso, micro):

    # Error relativo del TimeLoss
    e_loss = (
        100 * abs(meso["loss"] - micro["loss"])
        / max(micro["loss"], 1)
    )

    # Error relativo de vehiculos finalizados
    e_fin = (
        100 * abs(meso["fin"] - micro["fin"])
        / max(micro["fin"], 1)
    )

    # Error normalizado de teleports
    # Se utiliza una escala minima de 50 para evitar
    # dividir por cero cuando MICRO tiene 0 teleports.
    e_tele = (
        100 * abs(meso["tele"] - micro["tele"])
        / max(micro["tele"], 50)
    )

    # Error ponderado
    puntuacion = (
        PESO_LOSS * e_loss
        + PESO_FIN * e_fin
        + PESO_TELE * e_tele
    )

    return puntuacion, e_loss, e_fin, e_tele


# ============================================================
# EJECUCION DE SUMO
# ============================================================

def simular(n, tauff=None, penalty=None):

    global contador
    contador += 1

    micro = tauff is None

    comando = [
        "sumo",
        "-n", "red_5x5/red_5x5.net.xml",
        "-r", f"red_5x5/{n}_rutas/rutas_{n}.rou.xml",
        "--begin", "0",
        "--end", "3600",
        "--time-to-teleport", "300",
        "--duration-log.statistics", "true",
        "--no-step-log", "true",
        "--no-warnings", "true"
    ]

    if not micro:

        comando += [
            "--mesosim", "true",
            "--meso-ltm", "false",

            "--meso-junction-control", "true",
            "--meso-junction-control.limited", "true",

            "--meso-minor-penalty", str(penalty),

            "--meso-tauff", str(tauff),
            "--meso-taufj", "1.13",
            "--meso-taujf", "1.73",
            "--meso-taujj", "1.40",

            "--meso-edgelength", "98",
            "--meso-jam-threshold", "-1",
            "--meso-recheck", "0",
            "--meso-overtaking", "false"
        ]

    inicio = time.perf_counter()

    ejecucion = subprocess.run(
        comando,
        cwd=BASE,
        capture_output=True,
        text=True
    )

    real = time.perf_counter() - inicio
    texto = ejecucion.stdout

    fin = extraer(
        texto,
        r"Statistics \(avg of (\d+)\)"
    )

    loss = extraer(
        texto,
        r"^\s*TimeLoss:\s*([0-9.]+)"
    )

    if ejecucion.returncode != 0 or fin is None or loss is None:
        mostrar(
            f"ERROR: N={n}, tauff={tauff}, penalty={penalty}"
        )
        mostrar(ejecucion.stdout)
        mostrar(ejecucion.stderr)
        raise RuntimeError("Simulacion fallida")

    datos = {
        "fin": int(fin),

        "ins": int(extraer(
            texto, r"^\s*Inserted:\s*(\d+)", 0
        )),

        "run": int(extraer(
            texto, r"^\s*Running:\s*(\d+)", 0
        )),

        "wait": int(extraer(
            texto, r"^\s*Waiting:\s*(\d+)", 0
        )),

        "tele": int(extraer(
            texto, r"^\s*Teleports:\s*(\d+)", 0
        )),

        "loss": loss,

        "speed": extraer(
            texto, r"^\s*Speed:\s*([0-9.]+)", 0
        ),

        "real": real
    }

    if micro:

        referencias[n] = datos

        mostrar(
            f"[{contador:03d}/{total}] MICRO N={n} | "
            f"Fin={datos['fin']} | "
            f"TimeLoss={loss:.2f}s | "
            f"Teleports={datos['tele']} | "
            f"real={real:.3f}s"
        )

    else:

        resultados[(tauff, penalty, n)] = datos

        score, el, ef, et = evaluar(
            datos, referencias[n]
        )

        mostrar(
            f"[{contador:03d}/{total}] "
            f"MESO N={n} | "
            f"tauff={tauff:.1f} | "
            f"penalty={penalty:2d} | "
            f"Fin={datos['fin']:4d} | "
            f"TimeLoss={loss:7.2f}s | "
            f"Teleports={datos['tele']:3d} | "
            f"Error={score:6.2f} | "
            f"real={real:.3f}s"
        )

    return datos


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    if not shutil.which("sumo"):
        sys.exit("ERROR: SUMO no esta instalado")

    net = BASE / "red_5x5/red_5x5.net.xml"

    rutas = [
        BASE / f"red_5x5/{n}_rutas/rutas_{n}.rou.xml"
        for n in VEHICULOS
    ]

    faltantes = [
        str(p)
        for p in [net, *rutas]
        if not p.is_file()
    ]

    if faltantes:
        sys.exit(
            "ERROR: faltan archivos:\n"
            + "\n".join(faltantes)
        )

    mostrar("=" * 100)
    mostrar("PRUEBA 02 - CALIBRACION TAUFF + PENALIZACION")
    mostrar("=" * 100)

    mostrar(f"Fecha: {datetime.now()}")
    mostrar(f"Red: {net}")
    mostrar(f"Vehiculos: {VEHICULOS}")
    mostrar(f"Tauff: {TAUFF}")
    mostrar(f"Penalizaciones: {PENALIZACIONES}")
    mostrar("Control limitado: ACTIVADO")
    mostrar("Modelo: MESO convencional")
    mostrar("Penalizacion y tauff: variables")
    mostrar("Pesos error: 50% Loss / 30% Fin / 20% Tele")
    mostrar(f"Total simulaciones: {total}")

    # --------------------------------------------------------
    # REFERENCIAS MICROSCOPICAS
    # --------------------------------------------------------

    mostrar("\n=== REFERENCIA MICRO ===")

    for n in VEHICULOS:
        simular(n)

    # --------------------------------------------------------
    # SIMULACIONES MESOSCOPICAS
    # --------------------------------------------------------

    mostrar("\n=== CALIBRACION MESO ===")

    for tauff in TAUFF:

        for penalty in PENALIZACIONES:

            mostrar(
                f"\n--- TAUFF={tauff:.1f} "
                f"PENALIZACION={penalty} ---"
            )

            for n in VEHICULOS:
                simular(n, tauff, penalty)

    # --------------------------------------------------------
    # CLASIFICACION DE RESULTADOS
    # --------------------------------------------------------

    ranking = []

    for tauff in TAUFF:

        for penalty in PENALIZACIONES:

            errores = [
                evaluar(
                    resultados[(tauff, penalty, n)],
                    referencias[n]
                )
                for n in VEHICULOS
            ]

            ranking.append((
                mean(e[0] for e in errores),
                tauff,
                penalty,
                mean(e[1] for e in errores),
                mean(e[2] for e in errores),
                mean(e[3] for e in errores)
            ))

    ranking.sort()

    mostrar("\n" + "=" * 100)
    mostrar("TOP 15 CONFIGURACIONES - MENOR ERROR")
    mostrar("=" * 100)

    mostrar(
        f"{'Puesto':>6} "
        f"{'Tauff':>7} "
        f"{'Penalty':>8} "
        f"{'Score':>9} "
        f"{'ErrLoss%':>10} "
        f"{'ErrFin%':>10} "
        f"{'ErrTele%':>10}"
    )

    for pos, (score, tauff, pen, el, ef, et) in enumerate(
        ranking[:15], 1
    ):

        mostrar(
            f"{pos:6d} "
            f"{tauff:7.1f} "
            f"{pen:8d} "
            f"{score:9.2f} "
            f"{el:10.2f} "
            f"{ef:10.2f} "
            f"{et:10.2f}"
        )

    # --------------------------------------------------------
    # COMPARACION CON CONFIGURACION ORIGINAL
    # --------------------------------------------------------

    mostrar("\n" + "=" * 100)
    mostrar("GANADORA VS CONFIGURACION ANTERIOR 6/4")
    mostrar("=" * 100)

    configuraciones = [
        (
            ranking[0][1],
            ranking[0][2],
            "MEJOR PRUEBA 02"
        ),
        (
            6.0,
            4,
            "ANTERIOR 6/4"
        )
    ]

    for tauff, penalty, titulo in configuraciones:

        mostrar(
            f"\n{titulo}: "
            f"tauff={tauff:.1f}, penalty={penalty}"
        )

        mostrar(
            f"{'N':>5} "
            f"{'Fin MICRO':>10} "
            f"{'Fin MESO':>10} "
            f"{'Loss MICRO':>11} "
            f"{'Loss MESO':>10} "
            f"{'Tele MICRO':>11} "
            f"{'Tele MESO':>10} "
            f"{'Error':>8}"
        )

        for n in VEHICULOS:

            a = referencias[n]
            b = resultados[(tauff, penalty, n)]

            score, *_ = evaluar(b, a)

            mostrar(
                f"{n:5d} "
                f"{a['fin']:10d} "
                f"{b['fin']:10d} "
                f"{a['loss']:11.2f} "
                f"{b['loss']:10.2f} "
                f"{a['tele']:11d} "
                f"{b['tele']:10d} "
                f"{score:8.2f}"
            )

    # --------------------------------------------------------
    # MEJOR CONFIGURACION POR DEMANDA
    # --------------------------------------------------------

    mostrar("\n" + "=" * 100)
    mostrar("MEJOR CONFIGURACION POR CANTIDAD DE VEHICULOS")
    mostrar("=" * 100)

    for n in VEHICULOS:

        candidatos = sorted(
            (
                evaluar(
                    resultados[(t, p, n)],
                    referencias[n]
                )[0],
                t,
                p
            )
            for t in TAUFF
            for p in PENALIZACIONES
        )

        score, t, p = candidatos[0]

        mostrar(
            f"N={n} | "
            f"tauff={t:.1f} | "
            f"penalty={p} | "
            f"Error={score:.2f}"
        )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    mostrar("\n" + "=" * 100)
    mostrar(f"SIMULACIONES COMPLETADAS: {contador}/{total}")
    mostrar(f"LOG GUARDADO: {ARCHIVO_LOG}")
    mostrar("=" * 100)


if __name__ == "__main__":
    main()

