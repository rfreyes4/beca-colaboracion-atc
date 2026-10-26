from pathlib import Path
import re
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


# ==========================================
# CONFIGURACIÓN
# ==========================================

# Tiempos reales obtenidos con "time sumo"
# Estos valores no se guardan automáticamente en los XML.

TIEMPOS_REALES = {
    500: 0.151,
    1000: 0.220,
    1500: 0.327,
    2000: 0.432,
    2500: 0.577,
    3000: 0.911,
    3500: 5.826,
}

# Carpeta donde está este script
CARPETA = Path(__file__).resolve().parent

# Carpeta con las simulaciones
DATOS = CARPETA / "red_5x5"

# Carpeta donde se guardarán las gráficas
IMAGENES = CARPETA / "imagenes"


# ==========================================
# 1. LEER LOS RESULTADOS DE SUMO
# ==========================================

def cargar_resultados():

    resultados = []

    for carpeta in DATOS.glob("*_rutas"):

        if not carpeta.is_dir():
            continue

        coincidencia = re.fullmatch(
            r"(\d+)_rutas",
            carpeta.name
        )

        if not coincidencia:
            continue

        cantidad = int(coincidencia.group(1))

        archivo = carpeta / f"micro_{cantidad}_stats.xml"

        if not archivo.exists():
            print(f"No se encontró: {archivo}")
            continue

        try:

            raiz = ET.parse(archivo).getroot()

            vehiculos = raiz.find("vehicles")
            viajes = raiz.find("vehicleTripStatistics")
            teletransportes = raiz.find("teleports")

            if vehiculos is None or viajes is None:
                print(f"Faltan datos en: {archivo}")
                continue

            resultados.append({

                "cantidad": cantidad,

                "finalizados": int(
                    viajes.get("count", "0")
                ),

                "circulando": int(
                    vehiculos.get("running", "0")
                ),

                "esperando": int(
                    vehiculos.get("waiting", "0")
                ),

                "espera_media": float(
                    viajes.get("waitingTime", "0")
                ),

                "viaje_medio": float(
                    viajes.get("duration", "0")
                ),

                "teletransportes": (
                    int(teletransportes.get("total", "0"))
                    if teletransportes is not None
                    else 0
                ),

                "tiempo_real": TIEMPOS_REALES.get(cantidad),

            })

        except (ET.ParseError, ValueError) as error:
            print(f"Error leyendo {archivo}: {error}")

    # Ordenar por número de vehículos
    resultados.sort(
        key=lambda fila: fila["cantidad"]
    )

    if not resultados:
        raise SystemExit(
            "No se encontraron archivos de estadísticas válidos."
        )

    return resultados


# ==========================================
# 2. GUARDAR LAS GRÁFICAS
# ==========================================

def guardar(nombre):

    plt.tight_layout()

    plt.savefig(
        IMAGENES / nombre,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Guardada: imagenes/{nombre}")


# ==========================================
# 3. GENERAR LAS TRES GRÁFICAS
# ==========================================

def crear_graficas(resultados):

    # Crear la carpeta si no existe
    IMAGENES.mkdir(exist_ok=True)

    x = [r["cantidad"] for r in resultados]

    # --------------------------------------
    # GRÁFICA 1: ESTADO DE LOS VEHÍCULOS
    # --------------------------------------

    finalizados = [
        r["finalizados"] for r in resultados
    ]

    circulando = [
        r["circulando"] for r in resultados
    ]

    esperando = [
        r["esperando"] for r in resultados
    ]

    plt.figure(figsize=(10, 5.5))

    plt.bar(
        x,
        finalizados,
        width=280,
        label="Finalizados"
    )

    plt.bar(
        x,
        circulando,
        width=280,
        bottom=finalizados,
        label="Circulando"
    )

    plt.bar(
        x,
        esperando,
        width=280,
        bottom=[
            a + b
            for a, b in zip(finalizados, circulando)
        ],
        label="Esperando para entrar"
    )

    plt.title("Estado de los vehículos al finalizar")

    plt.xlabel("Vehículos programados")
    plt.ylabel("Número de vehículos")

    plt.xticks(x)

    plt.legend()
    plt.grid(axis="y", alpha=0.25)

    # Mostrar teletransportes registrados
    eventos = [
        f"{r['cantidad']}: {r['teletransportes']} teletransportes"
        for r in resultados
        if r["teletransportes"] > 0
    ]

    if eventos:
        plt.figtext(
            0.5,
            0.01,
            " | ".join(eventos),
            ha="center",
            fontsize=9
        )

    guardar("01_estado_vehiculos.png")

    # --------------------------------------
    # GRÁFICA 2: TIEMPOS DE ESPERA Y VIAJE
    # --------------------------------------

    plt.figure(figsize=(10, 5.5))

    plt.plot(
        x,
        [r["espera_media"] for r in resultados],
        "o-",
        label="Espera media"
    )

    plt.plot(
        x,
        [r["viaje_medio"] for r in resultados],
        "s-",
        label="Viaje medio"
    )

    plt.title("Tiempos medios de espera y viaje")

    plt.xlabel("Vehículos programados")
    plt.ylabel("Segundos")

    plt.xticks(x)

    plt.legend()
    plt.grid(alpha=0.25)

    plt.figtext(
        0.5,
        0.01,
        "Medias de los vehículos que completaron su viaje",
        ha="center",
        fontsize=9
    )

    guardar("02_tiempos_espera_viaje.png")

    # --------------------------------------
    # GRÁFICA 3: TIEMPO DE EJECUCIÓN
    # --------------------------------------

    con_tiempo = [
        r for r in resultados
        if r["tiempo_real"] is not None
    ]

    if con_tiempo:

        plt.figure(figsize=(10, 5.5))

        plt.plot(
            [r["cantidad"] for r in con_tiempo],
            [r["tiempo_real"] for r in con_tiempo],
            "o-"
        )

        plt.title("Tiempo real de ejecución de SUMO")

        plt.xlabel("Vehículos programados")
        plt.ylabel("Tiempo real (segundos)")

        plt.xticks(x)
        plt.ylim(bottom=0)

        plt.grid(alpha=0.25)

        guardar("03_tiempo_ejecucion.png")


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

if __name__ == "__main__":

    resultados = cargar_resultados()

    print(
        "Simulaciones encontradas:",
        [r["cantidad"] for r in resultados]
    )

    crear_graficas(resultados)

    print("\nGráficas guardadas en:")
    print(IMAGENES)