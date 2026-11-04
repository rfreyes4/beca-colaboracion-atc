from pathlib import Path
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

# Carpeta donde se guardarán las gráficas
SALIDA = Path(__file__).resolve().parent

# Resultados obtenidos en las simulaciones microscópicas V2
vehiculos = [2000, 2500, 3000, 3500, 4000, 4500, 5000]

generados = [2000, 2500, 3001, 3500, 4000, 4500, 5001]
insertados = [2000, 2500, 3001, 3500, 4000, 4481, 3180]

velocidades = [9.49, 8.98, 8.43, 7.66, 6.56, 5.42, 3.96]
esperas = [3.77, 6.77, 10.56, 17.82, 32.62, 56.11, 229.07]
tiempos = [0.506, 0.652, 0.782, 0.984, 1.476, 2.106, 6.976]


def preparar_grafica(titulo, eje_y):
    plt.figure(figsize=(9, 5))
    plt.title(titulo)
    plt.xlabel("Demanda de vehículos")
    plt.ylabel(eje_y)
    plt.xticks(vehiculos)
    plt.grid(axis="y", alpha=0.3)


def guardar(nombre):
    plt.tight_layout()
    plt.savefig(SALIDA / nombre, dpi=180)
    plt.close()
    print(f"Creada: imagenes/{nombre}")


# --------------------------------------------------
# GRÁFICA 1: VELOCIDAD MEDIA
# --------------------------------------------------

preparar_grafica(
    "Velocidad media - Simulación microscópica V2",
    "Velocidad media (m/s)"
)

plt.plot(vehiculos, velocidades, marker="o", linewidth=2)
plt.ylim(bottom=0)

guardar("grafica_velocidad.png")


# --------------------------------------------------
# GRÁFICA 2: TIEMPO DE ESPERA
# --------------------------------------------------

preparar_grafica(
    "Tiempo de espera medio - Simulación microscópica V2",
    "Tiempo de espera (s)"
)

plt.plot(vehiculos, esperas, marker="o", linewidth=2)
plt.ylim(bottom=0)

guardar("grafica_espera.png")


# --------------------------------------------------
# GRÁFICA 3: TIEMPO REAL DE EJECUCIÓN
# --------------------------------------------------

preparar_grafica(
    "Tiempo de ejecución - Simulación microscópica V2",
    "Tiempo real (s)"
)

plt.plot(vehiculos, tiempos, marker="o", linewidth=2)
plt.ylim(bottom=0)

guardar("grafica_tiempo.png")


# --------------------------------------------------
# GRÁFICA 4: VEHÍCULOS GENERADOS E INSERTADOS
# --------------------------------------------------

posiciones = list(range(len(vehiculos)))
ancho = 0.38

plt.figure(figsize=(9, 5))

plt.bar(
    [x - ancho / 2 for x in posiciones],
    generados,
    width=ancho,
    label="Generados"
)

plt.bar(
    [x + ancho / 2 for x in posiciones],
    insertados,
    width=ancho,
    label="Insertados"
)

plt.title("Vehículos generados e insertados - V2")
plt.xlabel("Demanda de vehículos")
plt.ylabel("Número de vehículos")
plt.xticks(posiciones, vehiculos)
plt.grid(axis="y", alpha=0.3)
plt.legend()

guardar("grafica_insertados.png")


print("\nTodas las gráficas se han guardado correctamente.")
