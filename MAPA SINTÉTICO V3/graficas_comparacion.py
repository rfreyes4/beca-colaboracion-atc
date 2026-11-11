#!/usr/bin/env python3

from pathlib import Path
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


# ============================================================
# COMPARACION MICRO VS MESO 4/6 - SUMO V3
# Datos obtenidos de modelo.md y las pruebas definitivas
# ============================================================

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "imagenes" / "comparacion_micro_meso"

SALIDA.mkdir(parents=True, exist_ok=True)

DEMANDAS = [3000, 3500, 4000, 4500, 5000, 5500]


# ============================================================
# RESULTADOS MICROSCOPICOS
# ============================================================

MICRO = {
    "cargados": [3001, 3500, 4000, 4500, 5001, 5501],

    "insertados": [2992, 3486, 3969, 4379, 3698, 3986],

    "finalizados": [2897, 3368, 3792, 4124, 2684, 2888],

    "pendientes": [9, 14, 31, 121, 1303, 1515],

    "velocidad": [10.81, 10.04, 9.00, 7.87, 7.25, 6.71],

    "duracion": [105.98, 117.03, 138.14, 173.00, 248.06, 262.23],

    "espera": [9.77, 17.29, 31.07, 56.62, 127.11, 134.09],

    "timeloss": [25.57, 36.88, 57.44, 92.71, 165.64, 179.94],

    "retraso_salida": [4.03, 6.64, 13.44, 34.05, 32.58, 60.07],

    "recorrido": [1102.87, 1099.53, 1106.50, 1097.62, 1096.76, 1088.74],

    "teleports": [0, 0, 0, 0, 96, 122],

    # Tiempos limpios del apartado 4.6 de modelo.md
    "real_limpio": [0.673, 0.834, 1.099, 1.563, 4.339, 5.216]
}


# ============================================================
# RESULTADOS MESOSCOPICOS DEFINITIVOS 4/6
# ============================================================

MESO = {
    "cargados": [3001, 3500, 4000, 4500, 5001, 5501],

    "insertados": [3001, 3500, 3999, 4488, 4262, 4336],

    "finalizados": [2895, 3388, 3867, 4022, 2276, 2045],

    "pendientes": [0, 0, 1, 12, 739, 1165],

    "velocidad": [10.68, 10.11, 9.39, 8.07, 6.90, 6.53],

    "duracion": [106.32, 113.17, 125.93, 163.04, 256.73, 290.05],

    "espera": [4.97, 6.76, 8.79, 12.22, 26.77, 31.72],

    "timeloss": [25.52, 32.59, 44.72, 82.49, 178.04, 212.82],

    "retraso_salida": [0.58, 0.74, 0.94, 1.22, 1.43, 1.90],

    "recorrido": [1107.63, 1104.55, 1112.70, 1101.09, 1078.73, 1057.60],

    "teleports": [0, 0, 0, 0, 174, 242],

    # Tiempos limpios obtenidos con Bash time
    "real_limpio": [0.194, 0.218, 0.239, 0.286, 1.307, 2.199]
}


# ============================================================
# CONFIGURACION GENERAL DE LAS GRAFICAS
# ============================================================

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 14
})


def crear_ejes(titulo, unidad):

    fig, ax = plt.subplots(figsize=(10, 5.8))

    ax.set_title(titulo, pad=14)
    ax.set_xlabel("Vehículos generados (aproximadamente)")
    ax.set_ylabel(unidad)

    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    return fig, ax


def guardar(fig, nombre):

    fig.tight_layout()

    destino = SALIDA / nombre

    fig.savefig(
        destino,
        dpi=220,
        bbox_inches="tight"
    )

    plt.close(fig)

    print("Guardada:", destino.relative_to(BASE))


# ============================================================
# FUNCIONES PARA COMPARAR MICRO Y MESO
# ============================================================

def comparar_lineas(nombre, titulo, ylabel, clave):

    fig, ax = crear_ejes(titulo, ylabel)

    ax.plot(
        DEMANDAS,
        MICRO[clave],
        "-o",
        linewidth=2.2,
        markersize=7,
        label="MICRO"
    )

    ax.plot(
        DEMANDAS,
        MESO[clave],
        "-s",
        linewidth=2.2,
        markersize=7,
        label="MESO 4/6"
    )

    ax.set_xticks(DEMANDAS)
    ax.legend()

    guardar(fig, nombre)


def comparar_barras(nombre, titulo, ylabel, clave):

    fig, ax = crear_ejes(titulo, ylabel)

    x = list(range(len(DEMANDAS)))
    ancho = 0.36

    ax.bar(
        [v - ancho / 2 for v in x],
        MICRO[clave],
        width=ancho,
        label="MICRO"
    )

    ax.bar(
        [v + ancho / 2 for v in x],
        MESO[clave],
        width=ancho,
        label="MESO 4/6"
    )

    ax.set_xticks(x, DEMANDAS)
    ax.legend()

    guardar(fig, nombre)


# ============================================================
# 1. GRAFICAS DE ESTADISTICAS MEDIAS
# ============================================================

comparar_lineas(
    "01_velocidad.png",
    "Velocidad media: MICRO vs MESO",
    "Velocidad (m/s)",
    "velocidad"
)

comparar_lineas(
    "02_tiempo_perdido.png",
    "Tiempo perdido medio (TimeLoss)",
    "Tiempo perdido (s)",
    "timeloss"
)

comparar_lineas(
    "03_tiempo_espera.png",
    "Tiempo de espera medio (WaitingTime)",
    "Tiempo de espera (s)",
    "espera"
)

comparar_lineas(
    "04_duracion.png",
    "Duración media del recorrido",
    "Duración (s)",
    "duracion"
)

comparar_lineas(
    "05_retraso_salida.png",
    "Retraso medio de incorporación (DepartDelay)",
    "Retraso (s)",
    "retraso_salida"
)

comparar_lineas(
    "06_longitud_recorridos.png",
    "Longitud media de rutas finalizadas",
    "Longitud (m)",
    "recorrido"
)


# ============================================================
# 2. GRAFICAS DE VEHICULOS
# ============================================================

comparar_barras(
    "07_insertados.png",
    "Vehículos insertados en la red",
    "Vehículos",
    "insertados"
)

comparar_barras(
    "08_finalizados.png",
    "Vehículos que completaron el recorrido",
    "Vehículos",
    "finalizados"
)

comparar_barras(
    "09_pendientes.png",
    "Vehículos pendientes de entrar (segundo 3600)",
    "Vehículos",
    "pendientes"
)

comparar_barras(
    "10_teleports.png",
    "Teletransportes registrados",
    "Teletransportes",
    "teleports"
)


# ============================================================
# 3. COMPARACION DE TIEMPOS LIMPIOS
# ============================================================

comparar_lineas(
    "11_tiempo_ejecucion_limpio.png",
    "Tiempo real de ejecución (mediciones limpias)",
    "Tiempo real (s)",
    "real_limpio"
)


# ============================================================
# 4. ACELERACION DE MESO FRENTE A MICRO
# ============================================================

aceleracion = [
    micro / meso
    for micro, meso in zip(
        MICRO["real_limpio"],
        MESO["real_limpio"]
    )
]

fig, ax = crear_ejes(
    "Aceleración de MESO frente a MICRO",
    "Veces más rápido (×)"
)

ax.bar(
    [str(v) for v in DEMANDAS],
    aceleracion
)

for i, valor in enumerate(aceleracion):
    ax.text(
        i,
        valor + 0.08,
        f"{valor:.2f}×",
        ha="center",
        fontsize=10
    )

ax.set_ylim(0, max(aceleracion) * 1.16)

guardar(fig, "12_aceleracion.png")


# ============================================================
# 5. PORCENTAJE DE VEHICULOS FINALIZADOS
# ============================================================

pct_micro = [
    100 * fin / cargados
    for fin, cargados in zip(
        MICRO["finalizados"],
        MICRO["cargados"]
    )
]

pct_meso = [
    100 * fin / cargados
    for fin, cargados in zip(
        MESO["finalizados"],
        MESO["cargados"]
    )
]

fig, ax = crear_ejes(
    "Porcentaje de viajes finalizados antes de 3600 s",
    "Finalizados / cargados (%)"
)

ax.plot(
    DEMANDAS,
    pct_micro,
    "-o",
    linewidth=2.2,
    label="MICRO"
)

ax.plot(
    DEMANDAS,
    pct_meso,
    "-s",
    linewidth=2.2,
    label="MESO 4/6"
)

ax.set_xticks(DEMANDAS)
ax.set_ylim(0, 105)
ax.legend()

guardar(fig, "13_porcentaje_finalizados.png")


# ============================================================
# 6. INFLUENCIA DE TAUFF SOBRE TIMELOSS
# Primera prueba: penalty = 4, control limitado activado
# ============================================================

TAUFF = [1.13, 3.00, 4.00, 4.50, 5.00, 5.50, 6.00]

LOSS_5000 = [
    16.23, 21.16, 49.04, 82.97,
    146.78, 144.60, 178.04
]

LOSS_5500 = [
    16.56, 22.52, 102.34, 125.65,
    174.34, 182.95, 212.82
]

fig, ax = crear_ejes(
    "Influencia de tauff en TimeLoss (penalización = 4 s)",
    "TimeLoss medio (s)"
)

ax.set_xlabel("meso-tauff (s)")

ax.plot(
    TAUFF,
    LOSS_5000,
    "-o",
    label="MESO, 5000 vehículos"
)

ax.plot(
    TAUFF,
    LOSS_5500,
    "-s",
    label="MESO, 5500 vehículos"
)

ax.axhline(
    MICRO["timeloss"][4],
    linestyle="--",
    label="MICRO, 5000 vehículos"
)

ax.axhline(
    MICRO["timeloss"][5],
    linestyle=":",
    label="MICRO, 5500 vehículos"
)

ax.set_xticks(TAUFF)
ax.legend(loc="upper left")

guardar(fig, "14_influencia_tauff.png")


# ============================================================
# FIN
# ============================================================

print()
print("=" * 65)
print("14 GRAFICAS GENERADAS CORRECTAMENTE")
print(f"Carpeta: {SALIDA}")
print("=" * 65)
