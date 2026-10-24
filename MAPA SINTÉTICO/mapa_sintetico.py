import argparse
import csv
import random
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# 1. Funciones auxiliares

def escribir_xml(raiz, destino):
    ET.indent(raiz, space="  ")
    ET.ElementTree(raiz).write(
        destino,
        encoding="utf-8",
        xml_declaration=True
    )


def cadena_puntos(puntos):
    return " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in puntos
    )


# 2. Generador principal

def generar(n, longitud, semilla, p_horizontal, carpeta):

    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = f"red_{n}x{n}"

    nod_file = carpeta / f"{nombre}.nod.xml"
    edg_file = carpeta / f"{nombre}.edg.xml"
    con_file = carpeta / f"{nombre}.con.xml"
    pri_file = carpeta / f"{nombre}.prioridades.csv"
    net_file = carpeta / f"{nombre}.net.xml"

    aleatorio = random.Random(semilla)

    posiciones = [
        (r, c)
        for r in range(n)
        for c in range(n)
    ]

    n_horizontales = round(n * n * p_horizontal)

    prioridad_h = set(
        aleatorio.sample(posiciones, n_horizontales)
    )

    def prioridad(r, c, orientacion):
        horizontal = (r, c) in prioridad_h
        return 3 if (orientacion == "H") == horizontal else 1

    def nodo(r, c):
        return f"j-{r}-{c}"

    def xy(r, c):
        return (
            c * longitud,
            (n - 1 - r) * longitud
        )


    # 3. Estructuras XML

    nodos = ET.Element("nodes")
    aristas = ET.Element("edges")
    conexiones = ET.Element("connections")

    entrantes = {
        p: {} for p in posiciones
    }

    salientes = {
        p: {} for p in posiciones
    }


    # 4. Creación de intersecciones

    for r, c in posiciones:

        x, y = xy(r, c)

        ET.SubElement(
            nodos,
            "node",
            {
                "id": nodo(r, c),
                "x": f"{x:.2f}",
                "y": f"{y:.2f}",
                "type": "priority",
                "rightOfWay": "edgePriority",
                "keepClear": "true"
            }
        )


    # 5. Función para añadir carreteras

    def anadir_arista(
        id_arista,
        origen,
        destino,
        orientacion,
        puntos=None
    ):

        r0, c0 = origen
        r1, c1 = destino

        if (
            orientacion in entrantes[destino]
            or orientacion in salientes[origen]
        ):
            raise RuntimeError(
                "Entrada o salida duplicada"
            )

        datos = {
            "id": id_arista,
            "from": nodo(r0, c0),
            "to": nodo(r1, c1),
            "priority": str(
                prioridad(r1, c1, orientacion)
                if orientacion in ("H", "V") else 1
            ),
            "numLanes": "1",
            "speed": "13.89",
            "spreadType": "right"
        }

        if puntos is not None:
            datos["shape"] = cadena_puntos(puntos)

        ET.SubElement(
            aristas,
            "edge",
            datos
        )

        entrantes[destino][orientacion] = id_arista
        salientes[origen][orientacion] = id_arista


    # 6. Parámetros geométricos

    # Todos los tramos conectan nodos consecutivos.
    # La separación entre nodos viene dada por longitud.


    # 7. Carreteras horizontales

    for r in range(n):

        if r % 2 == 0:
            columnas = list(range(n))
        else:
            columnas = list(range(n - 1, -1, -1))

        for c0, c1 in zip(
            columnas,
            columnas[1:]
        ):

            anadir_arista(
                f"h-{r}-{c0}-a-{c1}",
                (r, c0),
                (r, c1),
                "H"
            )


    # 8. Carreteras verticales

    for c in range(n):

        if c % 2 == 0:
            filas = list(range(n))
        else:
            filas = list(range(n - 1, -1, -1))

        for r0, r1 in zip(
            filas,
            filas[1:]
        ):

            anadir_arista(
                f"v-{c}-{r0}-a-{r1}",
                (r0, c),
                (r1, c),
                "V"
            )


    # 8.1. Aristas adicionales de retorno

    anadir_arista(
        "retorno-inicial",
        (1, 0),
        (0, 0),
        "R"
    )

    anadir_arista(
        "retorno-final",
        (n - 1, n - 1),
        (n - 2, n - 1),
        "R"
    )


    # 9. Conexiones entre carreteras

    for posicion in posiciones:

        if (
            not entrantes[posicion]
            or not salientes[posicion]
        ):
            raise RuntimeError(
                f"Intersección incompleta: {posicion}"
            )

        for entrada in entrantes[posicion].values():

            for salida in salientes[posicion].values():

                ET.SubElement(
                    conexiones,
                    "connection",
                    {
                        "from": entrada,
                        "to": salida,
                        "fromLane": "0",
                        "toLane": "0"
                    }
                )


    # 10. Guardar archivos XML

    escribir_xml(nodos, nod_file)
    escribir_xml(aristas, edg_file)
    escribir_xml(conexiones, con_file)


    # 11. Guardar prioridades en CSV

    with pri_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as archivo:

        escritor = csv.writer(archivo)

        escritor.writerow([
            "fila",
            "columna",
            "prioridad",
            "prioridad_entrada_H",
            "prioridad_entrada_V"
        ])

        for r, c in posiciones:

            escritor.writerow([
                r + 1,
                c + 1,
                (
                    "horizontal"
                    if (r, c) in prioridad_h
                    else "vertical"
                ),
                prioridad(r, c, "H"),
                prioridad(r, c, "V")
            ])


    # 12. Información de la red

    total_aristas = 2 * n * (n - 1) + 2

    print(
        f"\nRed {n}x{n}: "
        f"{n*n} intersecciones, "
        f"{total_aristas} tramos dirigidos."
    )

    print(
        f"Tramos interiores: {longitud:g} metros entre nodos."
    )

    print(
        f"Prioridad H: {n_horizontales}; "
        f"V: {n*n-n_horizontales}."
    )

    print(
        "Aristas adicionales: 2."
    )

    print(
        f"Archivos guardados en: {carpeta.resolve()}"
    )


    # 13. Conversión a red SUMO

    netconvert = shutil.which("netconvert")

    if netconvert:

        orden = [
            netconvert,
            "--node-files", str(nod_file),
            "--edge-files", str(edg_file),
            "--connection-files", str(con_file),
            "--output-file", str(net_file),
            "--no-turnarounds", "true"
        ]

        print("\nCreando red final con netconvert...")

        proceso = subprocess.run(
            orden,
            check=False
        )

        if proceso.returncode:

            print(
                "Error al convertir la red.",
                file=sys.stderr
            )

            sys.exit(proceso.returncode)

        print(f"RED LISTA: {net_file.resolve()}")

        print(
            f"Para visualizarla: "
            f"netedit -s '{net_file.resolve()}'"
        )

    else:

        print(
            "\nNo se ha encontrado netconvert."
        )

        print(
            "Los XML se han generado correctamente."
        )

        print(
            "Instala SUMO y ejecuta netconvert."
        )


# 14. Función principal

def main():

    parser = argparse.ArgumentParser(
        description="Generador de red sintética NxN para SUMO"
    )

    parser.add_argument(
        "-n",
        "--n",
        type=int,
        help="Número de filas y columnas (impar, mínimo 3)"
    )

    parser.add_argument(
        "--longitud",
        type=float,
        default=100.0,
        help="Separación entre intersecciones en metros"
    )

    parser.add_argument(
        "--semilla",
        type=int,
        default=42,
        help="Semilla aleatoria"
    )

    parser.add_argument(
        "--p-horizontal",
        type=float,
        default=0.5,
        help="Proporción de prioridades horizontales"
    )

    parser.add_argument(
        "--salida",
        type=Path,
        default=None,
        help="Carpeta de salida"
    )

    args = parser.parse_args()

    if args.n is None:

        try:

            args.n = int(
                input(
                    "Introduce N (filas y columnas): "
                ).strip()
            )

        except (ValueError, EOFError):

            parser.error(
                "N debe ser un número entero"
            )

    if args.n < 3 or args.n % 2 == 0:

        parser.error(
            "N debe ser impar y como mínimo 3"
        )

    if args.longitud < 20:

        parser.error(
            "La longitud mínima es de 20 metros"
        )

    if not 0 <= args.p_horizontal <= 1:

        parser.error(
            "La proporción debe estar entre 0 y 1"
        )

    salida = (
        args.salida
        if args.salida
        else Path(f"red_{args.n}x{args.n}")
    )

    generar(
        args.n,
        args.longitud,
        args.semilla,
        args.p_horizontal,
        salida
    )


# 15. Inicio del programa

if __name__ == "__main__":
    main()