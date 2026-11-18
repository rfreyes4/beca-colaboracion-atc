import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SALIDA = BASE / "meso" / "prueba_3"
VEHICULOS = [3000, 4000, 5000, 6000, 7000, 8000, 9000, 11000]

SALIDA.mkdir(parents=True, exist_ok=True)

for n in VEHICULOS:

    print(f"\n{'=' * 50}", flush=True)
    print(f"MESO PRUEBA 2 - {n} VEHICULOS", flush=True)
    print("=" * 50, flush=True)

    comando = [
        "sumo",
        "-n", "red_7x7/red_7x7.net.xml",
        "-r", f"red_7x7/{n}_rutas/rutas_{n}.rou.xml",
        "-a", "red_7x7/semaforos.add.xml",
        "--begin", "0",
        "--end", "3600",
        "--seed", "42",
        "--time-to-teleport", "300",
        "--device.rerouting.probability", "0",
        "--mesosim", "true",
        "--meso-ltm", "false",
        "--meso-edgelength", "50",
        "--meso-junction-control", "true",
        "--meso-junction-control.limited", "false",
        "--meso-jam-threshold", "-1",
        "--meso-overtaking", "false",
        "--no-step-log", "true"
    ]

    # RESULTADOS COMPLETOS
    print("\nRESULTADOS COMPLETOS:\n", flush=True)

    completo = subprocess.run(
        ["bash", "-c", 'time -p "$@"', "bash",
         *comando, "--duration-log.statistics", "true"],
        cwd=BASE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    (SALIDA / f"meso_{n}.log").write_text(
        completo.stdout, encoding="utf-8"
    )

    print("\n".join(completo.stdout.splitlines()[-22:]), flush=True)

    if completo.returncode != 0:
        raise RuntimeError(f"Error en MESO {n} completo")

    # TIEMPOS LIMPIOS
    print("\nTIEMPOS LIMPIOS:\n", flush=True)

    limpio = subprocess.run(
        ["bash", "-c", 'time -p "$@" > /dev/null 2>&1',
         "bash", *comando],
        cwd=BASE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    (SALIDA / f"meso_{n}_limpio.log").write_text(
        limpio.stdout, encoding="utf-8"
    )

    print(limpio.stdout, flush=True)

    if limpio.returncode != 0:
        raise RuntimeError(f"Error en MESO {n} limpio")

print("\nTODAS LAS PRUEBAS FINALIZADAS")
