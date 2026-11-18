#!/usr/bin/env python3
"""Genera las 28 rutas rectas de referencia para coordinar semaforos en V4.

Las rutas de este archivo se usan SOLO como entrada de tlsCoordinator.py.
No sustituyen las rutas de randomTrips para las simulaciones de 3000 coches.
"""

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


N = 7  # 7 filas y 7 columnas de intersecciones semaforizadas


def construir_recorridos():
    """Devuelve (identificador, nodos) para 14 horizontales y 14 verticales."""
    recorridos = []

    for fila in range(N):
        cruces = [f"j-{fila}-{col}" for col in range(N)]
        recorridos.append((
            f"recta_oeste_este_fila_{fila}",
            [f"ext-o-{fila}", *cruces, f"ext-e-{fila}"],
        ))
        recorridos.append((
            f"recta_este_oeste_fila_{fila}",
            [f"ext-e-{fila}", *reversed(cruces), f"ext-o-{fila}"],
        ))

    for columna in range(N):
        cruces = [f"j-{fila}-{columna}" for fila in range(N)]
        recorridos.append((
            f"recta_norte_sur_columna_{columna}",
            [f"ext-n-{columna}", *cruces, f"ext-s-{columna}"],
        ))
        recorridos.append((
            f"recta_sur_norte_columna_{columna}",
            [f"ext-s-{columna}", *reversed(cruces), f"ext-n-{columna}"],
        ))

    assert len(recorridos) == 28
    return recorridos


def leer_red(ruta_red):
    """Extrae nodos, aristas dirigidas y conexiones permitidas de SUMO."""
    raiz = ET.parse(ruta_red).getroot()

    nodos = {
        j.attrib["id"]: (float(j.attrib["x"]), float(j.attrib["y"]))
        for j in raiz.findall("junction")
    }

    aristas = {}
    for e in raiz.findall("edge"):
        if e.get("function") or not e.get("from") or not e.get("to"):
            continue  # Descarta conexiones internas y edges auxiliares
        clave = (e.get("from"), e.get("to"))
        if clave in aristas:
            raise ValueError(f"Hay dos carreteras para el mismo recorrido: {clave}")
        carril = e.find("lane")
        aristas[clave] = (
            e.get("id"),
            float(carril.get("speed")) if carril is not None else None,
            float(carril.get("length")) if carril is not None else None,
        )

    conexiones = {
        (c.get("from"), c.get("to"))
        for c in raiz.findall("connection")
    }

    return nodos, aristas, conexiones


def obtener_aristas(recorrido, nodos, aristas, conexiones):
    """Comprueba geometria, direccion de cada carretera y giros prohibidos."""
    nombre, sucesion = recorrido

    for nodo in sucesion:
        if nodo not in nodos:
            raise ValueError(f"{nombre}: no existe el nodo {nodo}")

    coords = [nodos[nodo] for nodo in sucesion]
    es_horizontal = all(abs(y - coords[0][1]) < 0.01 for _, y in coords)
    es_vertical = all(abs(x - coords[0][0]) < 0.01 for x, _ in coords)
    if not (es_horizontal or es_vertical):
        raise ValueError(f"{nombre}: el recorrido no es recto")

    edges = []
    velocidades = []
    longitudes = []
    for origen, destino in zip(sucesion[:-1], sucesion[1:]):
        if (origen, destino) not in aristas:
            raise ValueError(f"{nombre}: falta carretera {origen} -> {destino}")
        edge_id, velocidad, longitud = aristas[(origen, destino)]
        edges.append(edge_id)
        if velocidad is not None:
            velocidades.append(velocidad)
        if longitud is not None:
            longitudes.append(longitud)

    for anterior, siguiente in zip(edges[:-1], edges[1:]):
        if (anterior, siguiente) not in conexiones:
            raise ValueError(
                f"{nombre}: SUMO no permite pasar de {anterior} a {siguiente}"
            )

    return edges, velocidades, longitudes


def main():
    parser = argparse.ArgumentParser(
        description="Rutas rectas para onda verde V4: 7x7, 28 rutas de referencia"
    )
    parser.add_argument(
        "-n", "--red", type=Path,
        default=Path("red_7x7/red_7x7.net.xml"),
        help="Red SUMO existente (.net.xml)",
    )
    parser.add_argument(
        "-o", "--salida", type=Path,
        default=Path("red_7x7/coordinacion_rectas.rou.xml"),
        help="Archivo de referencia para tlsCoordinator.py",
    )
    args = parser.parse_args()

    nodos, aristas, conexiones = leer_red(args.red)
    esperados = {f"j-{fila}-{col}" for fila in range(N) for col in range(N)}
    if not esperados.issubset(nodos):
        raise ValueError("La red no contiene las 49 intersecciones j-fila-columna")

    raiz = ET.Element("routes")
    velocidades = []
    longitudes = []
    recorridos = construir_recorridos()
    for nombre, nodos_recorrido in recorridos:
        edges, v, distancias = obtener_aristas(
            (nombre, nodos_recorrido), nodos, aristas, conexiones
        )
        vehiculo = ET.SubElement(raiz, "vehicle", {
            "id": nombre,
            "depart": "0.00",
        })
        ET.SubElement(vehiculo, "route", {"edges": " ".join(edges)})
        velocidades.extend(v)
        longitudes.extend(distancias)

    ET.indent(raiz, space="    ")
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(raiz).write(args.salida, encoding="utf-8", xml_declaration=True)

    print("Rutas rectas generadas: 28")
    print("  Horizontales: 14 (7 por sentido)")
    print("  Verticales:   14 (7 por sentido)")
    print("  Giros:         0")
    if velocidades:
        print(f"Velocidad maxima de referencia: {velocidades[0]:.2f} m/s "
              f"({velocidades[0] * 3.6:.1f} km/h)")
    if longitudes:
        print(f"Longitud de tramo de referencia: {longitudes[0]:.2f} m")
    print("Todas las rutas y conexiones verificadas con el archivo .net.xml")
    print(f"Archivo generado: {args.salida.resolve()}")


if __name__ == "__main__":
    main()
