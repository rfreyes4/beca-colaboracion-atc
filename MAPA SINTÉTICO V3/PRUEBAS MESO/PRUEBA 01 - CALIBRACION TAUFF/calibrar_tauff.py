import subprocess
import re
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# PRUEBA 01 - CALIBRACION DEL PARAMETRO TAUFF
# Comparacion MICRO vs MESO con control limitado
# ============================================================

BASE = Path(__file__).resolve().parents[2]
CARPETA = Path(__file__).resolve().parent
LOGS = CARPETA / "logs"

LOGS.mkdir(parents=True, exist_ok=True)

fecha = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
ARCHIVO_LOG = LOGS / f"resultados_{fecha}.log"

VEHICULOS = [3500, 4000, 4500, 5000, 5500]
TAUFF = [1.13, 3.0, 4.0, 4.5, 5.0, 5.5, 6.0]
PENALTY = 4

resultados = {}
contador = 0
total = len(VEHICULOS) * (1 + len(TAUFF) + 2)


# ============================================================
# FUNCIONES
# ============================================================

def mostrar(mensaje=""):
    print(mensaje, flush=True)

    with ARCHIVO_LOG.open("a", encoding="utf-8") as f:
        f.write(mensaje + "\n")


def extraer(texto, patron, defecto=0):
    m = re.search(patron, texto, re.MULTILINE)
    return float(m.group(1)) if m else defecto


def simular(n, modo, tauff=None):
    global contador
    contador += 1

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

    if modo != "MICRO":

        control = "true" if modo == "LIMITADO" else "false"

        comando += [
            "--mesosim", "true",
            "--meso-ltm", "false",
            "--meso-junction-control", control,
            "--meso-junction-control.limited", control,
            "--meso-minor-penalty", str(PENALTY),
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

    p = subprocess.run(
        comando,
        cwd=BASE,
        capture_output=True,
        text=True
    )

    tiempo = time.perf_counter() - inicio

    if p.returncode != 0:
        mostrar(f"ERROR: N={n} Modo={modo} Tauff={tauff}")
        mostrar(p.stderr or p.stdout)
        return None

    texto = p.stdout

    if "Statistics (avg of" not in texto:
        mostrar(f"ERROR: Estadisticas no encontradas en N={n}")
        mostrar(texto)
        return None

    fin = int(extraer(texto, r"Statistics \(avg of (\d+)\)"))
    ins = int(extraer(texto, r"^\s*Inserted:\s*(\d+)"))
    run = int(extraer(texto, r"^\s*Running:\s*(\d+)"))
    wait = int(extraer(texto, r"^\s*Waiting:\s*(\d+)"))
    tele = int(extraer(texto, r"^\s*Teleports:\s*(\d+)"))
    loss = extraer(texto, r"^\s*TimeLoss:\s*([\d.]+)")
    speed = extraer(texto, r"^\s*Speed:\s*([\d.]+)")

    resultado = {
        "fin": fin,
        "ins": ins,
        "run": run,
        "wait": wait,
        "tele": tele,
        "loss": loss,
        "speed": speed,
        "real": tiempo
    }

    resultados[(n, modo, tauff)] = resultado

    valor = f"{tauff:.2f}" if tauff is not None else "  - "

    mostrar(
        f"[{contador:02d}/{total}] "
        f"{modo:9s} | tauff={valor} | "
        f"Fin={fin:4d} | "
        f"TimeLoss={loss:7.2f}s | "
        f"Teleports={tele:3d} | "
        f"Speed={speed:5.2f} | "
        f"real={tiempo:.3f}s"
    )

    return resultado


# ============================================================
# INICIO DEL EXPERIMENTO
# ============================================================

mostrar("=" * 105)
mostrar(" PRUEBA 01 - CALIBRACION TAUFF EN SUMO")
mostrar("=" * 105)
mostrar(f"Fecha: {datetime.now()}")
mostrar(f"Red: {BASE / 'red_5x5/red_5x5.net.xml'}")
mostrar(f"Vehiculos: {VEHICULOS}")
mostrar(f"Valores tauff: {TAUFF}")
mostrar(f"Penalizacion MESO: {PENALTY}")
mostrar("Control limitado: activado en las pruebas LIMITADO")
mostrar("Simulacion: 0 - 3600 segundos")
mostrar("Teletransporte: 300 segundos")
mostrar(f"Total simulaciones: {total}")


for n in VEHICULOS:

    mostrar("\n" + "=" * 105)
    mostrar(f" EXPERIMENTO - {n} VEHICULOS")
    mostrar("=" * 105)

    # Simulacion MICRO de referencia
    simular(n, "MICRO")

    # Simulaciones MESO con control limitado
    for tauff in TAUFF:
        simular(n, "LIMITADO", tauff)

    # Simulaciones MESO sin control de intersecciones
    # Se mantiene la penalizacion de 4 segundos
    for tauff in [3.0, 6.0]:
        simular(n, "SIN_CTRL", tauff)


# ============================================================
# COMPARACION CON MICRO
# ============================================================

mostrar("\n\n" + "=" * 105)
mostrar(" COMPARACION FINAL - CONTROL LIMITADO FRENTE A MICRO")
mostrar("=" * 105)

mostrar(
    f"{'Vehiculos':>10} "
    f"{'Tauff':>7} "
    f"{'Fin':>7} "
    f"{'Tele':>6} "
    f"{'TimeLoss':>10} "
    f"{'Dif.Loss':>10} "
    f"{'Dif.Fin':>9} "
    f"{'Dif.Tele':>9}"
)

mostrar("-" * 105)

for n in VEHICULOS:

    micro = resultados.get((n, "MICRO", None))

    if micro is None:
        continue

    mostrar(
        f"{n:10d} "
        f"{'MICRO':>7} "
        f"{micro['fin']:7d} "
        f"{micro['tele']:6d} "
        f"{micro['loss']:10.2f} "
        f"{'-':>10} "
        f"{'-':>9} "
        f"{'-':>9}"
    )

    for tauff in TAUFF:

        r = resultados.get((n, "LIMITADO", tauff))

        if r is None:
            continue

        diferencia_loss = r["loss"] - micro["loss"]
        diferencia_fin = r["fin"] - micro["fin"]
        diferencia_tele = r["tele"] - micro["tele"]

        mostrar(
            f"{n:10d} "
            f"{tauff:7.2f} "
            f"{r['fin']:7d} "
            f"{r['tele']:6d} "
            f"{r['loss']:10.2f} "
            f"{diferencia_loss:+10.2f} "
            f"{diferencia_fin:+9d} "
            f"{diferencia_tele:+9d}"
        )

    mostrar("-" * 105)


# ============================================================
# INFLUENCIA DEL CONTROL LIMITADO
# ============================================================

mostrar("\n" + "=" * 105)
mostrar(" INFLUENCIA DEL CONTROL LIMITADO")
mostrar("=" * 105)

mostrar(
    f"{'Vehiculos':>10} "
    f"{'Tauff':>7} "
    f"{'Control':>12} "
    f"{'Finalizados':>12} "
    f"{'Teleports':>10} "
    f"{'TimeLoss':>10}"
)

mostrar("-" * 105)

for n in VEHICULOS:
    for tauff in [3.0, 6.0]:
        for modo in ["SIN_CTRL", "LIMITADO"]:

            r = resultados.get((n, modo, tauff))

            if r is None:
                continue

            mostrar(
                f"{n:10d} "
                f"{tauff:7.2f} "
                f"{modo:>12} "
                f"{r['fin']:12d} "
                f"{r['tele']:10d} "
                f"{r['loss']:10.2f}"
            )


# ============================================================
# FINAL
# ============================================================

mostrar("\n" + "=" * 105)
mostrar(f"SIMULACIONES COMPLETADAS: {len(resultados)}/{total}")
mostrar(f"LOG GUARDADO EN: {ARCHIVO_LOG}")
mostrar("=" * 105)

