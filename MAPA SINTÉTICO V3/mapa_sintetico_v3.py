#!/usr/bin/env python3


import argparse
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from collections import defaultdict
from pathlib import Path


# Guardar archivos XML
def guardar_xml(raiz, ruta):

    ET.indent(raiz, space="  ")

    ET.ElementTree(raiz).write(
        ruta,
        encoding="utf-8",
        xml_declaration=True
    )


# Generación de la red
def generar(n, longitud, salida):

    salida.mkdir(parents=True, exist_ok=True)

    prefijo = f"red_{n}x{n}"

    archivo_nodos = salida / f"{prefijo}.nod.xml"
    archivo_aristas = salida / f"{prefijo}.edg.xml"
    archivo_conexiones = salida / f"{prefijo}.con.xml"
    archivo_red = salida / f"{prefijo}.net.xml"

    xml_nodos = ET.Element("nodes")
    xml_aristas = ET.Element("edges")
    xml_conexiones = ET.Element("connections")

    extremos = {}

    entradas = defaultdict(list)
    salidas = defaultdict(list)


    # Crear nodos
    def agregar_nodo(id_nodo, x, y, exterior=False):

        datos = {
            "id": id_nodo,
            "x": f"{x:.2f}",
            "y": f"{y:.2f}"
        }

        if exterior:

            datos["fringe"] = "outer"

        else:

            datos["type"] = "right_before_left"
            datos["keepClear"] = "true"

        ET.SubElement(xml_nodos, "node", datos)


    # Crear aristas
    def agregar_arista(id_arista, origen, destino):

        if id_arista in extremos:
            raise ValueError(f"Arista duplicada: {id_arista}")

        extremos[id_arista] = (origen, destino)

        entradas[destino].append(id_arista)
        salidas[origen].append(id_arista)

        ET.SubElement(xml_aristas, "edge", {

            "id": id_arista,
            "from": origen,
            "to": destino,

            "priority": "1",
            "numLanes": "1",
            "speed": "13.89",
            "spreadType": "right"

        })


    # Conectar dos nodos en ambos sentidos
    def conectar_bidireccionalmente(a, b):

        agregar_arista(f"e-{a}-a-{b}", a, b)
        agregar_arista(f"e-{b}-a-{a}", b, a)


    # Identificador de intersección
    def id_interior(r, c):

        return f"j-{r}-{c}"


    # Coordenadas de cada intersección
    def xy_interior(r, c):

        return c * longitud, (n - 1 - r) * longitud


    # 1. Crear los nodos de la malla
    for r in range(n):

        for c in range(n):

            agregar_nodo(
                id_interior(r, c),
                *xy_interior(r, c)
            )


    # 2. Crear calles interiores bidireccionales
    tramos_interiores = 0

    for r in range(n):

        for c in range(n):

            actual = id_interior(r, c)

            if c + 1 < n:

                conectar_bidireccionalmente(
                    actual,
                    id_interior(r, c + 1)
                )

                tramos_interiores += 1

            if r + 1 < n:

                conectar_bidireccionalmente(
                    actual,
                    id_interior(r + 1, c)
                )

                tramos_interiores += 1


    # 3. Crear flecos exteriores
    flecos = 0

    # Norte y sur
    for c in range(n):

        for lado, fila, dy in (
            ("n", 0, longitud),
            ("s", n - 1, -longitud)
        ):

            x, y = xy_interior(fila, c)

            exterior = f"ext-{lado}-{c}"

            agregar_nodo(
                exterior,
                x,
                y + dy,
                exterior=True
            )

            conectar_bidireccionalmente(
                id_interior(fila, c),
                exterior
            )

            flecos += 1


    # Oeste y este
    for r in range(n):

        for lado, columna, dx in (
            ("o", 0, -longitud),
            ("e", n - 1, longitud)
        ):

            x, y = xy_interior(r, columna)

            exterior = f"ext-{lado}-{r}"

            agregar_nodo(
                exterior,
                x + dx,
                y,
                exterior=True
            )

            conectar_bidireccionalmente(
                id_interior(r, columna),
                exterior
            )

            flecos += 1


    # 4. Crear conexiones sin giros de 180 grados
    conexiones = 0

    for r in range(n):

        for c in range(n):

            interseccion = id_interior(r, c)

            for entrada in entradas[interseccion]:

                origen_entrada, _ = extremos[entrada]

                for salida_arista in salidas[interseccion]:

                    _, destino_salida = extremos[salida_arista]

                    if origen_entrada == destino_salida:
                        continue

                    ET.SubElement(
                        xml_conexiones,
                        "connection",
                        {
                            "from": entrada,
                            "to": salida_arista,
                            "fromLane": "0",
                            "toLane": "0"
                        }
                    )

                    conexiones += 1


    # 5. Guardar archivos XML
    guardar_xml(xml_nodos, archivo_nodos)
    guardar_xml(xml_aristas, archivo_aristas)
    guardar_xml(xml_conexiones, archivo_conexiones)


    print(f"\nRed sintética V3: {n}x{n}")
    print(f"Intersecciones: {n*n}")
    print(f"Tramos interiores: {tramos_interiores}")
    print(f"Flecos exteriores: {flecos}")
    print(f"Aristas dirigidas: {len(extremos)}")
    print(f"Conexiones: {conexiones}")
    print(f"Longitud: {longitud:g} metros")
    print(f"Directorio: {salida.resolve()}")


    # 6. Generar red final con netconvert
    netconvert = shutil.which("netconvert")

    if netconvert is None:

        print("ERROR: netconvert no está instalado.")
        sys.exit(1)


    orden = [

        netconvert,

        "--node-files", str(archivo_nodos),

        "--edge-files", str(archivo_aristas),

        "--connection-files", str(archivo_conexiones),

        "--output-file", str(archivo_red),

        "--no-turnarounds", "true",

        "--no-turnarounds.fringe", "true",

        "--default.junctions.type", "right_before_left",

        "--no-internal-links", "true"

    ]


    print("\nEjecutando netconvert...")

    try:

        subprocess.run(orden, check=True)

    except subprocess.CalledProcessError as exc:

        print("ERROR al generar la red.", file=sys.stderr)

        sys.exit(exc.returncode)


    print(f"\nRed SUMO generada: {archivo_red.resolve()}")


# Programa principal
def main():

    parser = argparse.ArgumentParser(
        description="Mapa sintético V3: malla bidireccional NxN"
    )

    parser.add_argument(
        "-n",
        "--n",
        type=int,
        default=5,
        help="Número de filas y columnas (por defecto 5)"
    )

    parser.add_argument(
        "--longitud",
        type=float,
        default=200.0,
        help="Longitud de las calles en metros (por defecto 200)"
    )

    parser.add_argument(
        "--salida",
        type=Path,
        default=None,
        help="Carpeta de salida"
    )

    args = parser.parse_args()

    if args.n < 3:
        parser.error("N debe ser al menos 3")

    if args.longitud < 20:
        parser.error("La longitud mínima es de 20 metros")

    generar(
        args.n,
        args.longitud,
        args.salida if args.salida else Path(f"red_{args.n}x{args.n}")
    )


if __name__ == "__main__":
    main()
