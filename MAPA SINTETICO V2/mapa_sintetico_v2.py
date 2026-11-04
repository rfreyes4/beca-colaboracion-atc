import argparse
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def guardar_xml(raiz, ruta):
    ET.indent(raiz, space="  ")
    ET.ElementTree(raiz).write(ruta, encoding="utf-8", xml_declaration=True)


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

    # Mapa de IDs de aristas dirigidas a sus nodos (origen, destino).
    extremos = {}
    entradas = defaultdict(list)  # destino -> ids de aristas entrantes
    salidas = defaultdict(list)   # origen  -> ids de aristas salientes

    def agregar_nodo(id_nodo, x, y, exterior=False):
        datos = {"id": id_nodo, "x": f"{x:.2f}", "y": f"{y:.2f}"}
        if exterior:
            # Son finales de red, NO intersecciones de la malla NxN.
            datos["fringe"] = "outer"
        else:
            datos["type"] = "right_before_left"
            datos["keepClear"] = "true"
        ET.SubElement(xml_nodos, "node", datos)

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
            "priority": "1",  # igual para todas; manda right_before_left
            "numLanes": "1",
            "speed": "13.89",
            "spreadType": "right",
        })

    def conectar_bidireccionalmente(a, b):
        agregar_arista(f"e-{a}-a-{b}", a, b)
        agregar_arista(f"e-{b}-a-{a}", b, a)

    def id_interior(r, c):
        return f"j-{r}-{c}"

    def xy_interior(r, c):
        # La fila 0 corresponde a la parte superior.
        return c * longitud, (n - 1 - r) * longitud

    # 1. Los N*N nodos principales de la malla.
    for r in range(n):
        for c in range(n):
            agregar_nodo(id_interior(r, c), *xy_interior(r, c))

    # 2. Segmentos interiores: 2 sentidos por cada pareja vecina.
    tramos_interiores = 0
    for r in range(n):
        for c in range(n):
            actual = id_interior(r, c)
            if c + 1 < n:
                conectar_bidireccionalmente(actual, id_interior(r, c + 1))
                tramos_interiores += 1
            if r + 1 < n:
                conectar_bidireccionalmente(actual, id_interior(r + 1, c))
                tramos_interiores += 1

    # 3. Flecos en los cuatro lados, todos de la misma longitud.
    #    Los nodos de las esquinas tienen DOS flecos: uno por lado.
    flecos = 0
    for c in range(n):
        for lado, fila, dy in (("n", 0, longitud), ("s", n - 1, -longitud)):
            x, y = xy_interior(fila, c)
            exterior = f"ext-{lado}-{c}"
            agregar_nodo(exterior, x, y + dy, exterior=True)
            conectar_bidireccionalmente(id_interior(fila, c), exterior)
            flecos += 1

    for r in range(n):
        for lado, columna, dx in (("o", 0, -longitud), ("e", n - 1, longitud)):
            x, y = xy_interior(r, columna)
            exterior = f"ext-{lado}-{r}"
            agregar_nodo(exterior, x + dx, y, exterior=True)
            conectar_bidireccionalmente(id_interior(r, columna), exterior)
            flecos += 1

    # 4. Conexiones permitidas en las intersecciones de la malla.
    #    No se permite de A->B a B->A (giro de 180 grados).
    #    En los extremos exteriores NO creamos conexiones: así una ruta
    #    debe comenzar o terminar allí, nunca efectuar un giro en U.
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
                    ET.SubElement(xml_conexiones, "connection", {
                        "from": entrada,
                        "to": salida_arista,
                        "fromLane": "0",
                        "toLane": "0",
                    })
                    conexiones += 1

    guardar_xml(xml_nodos, archivo_nodos)
    guardar_xml(xml_aristas, archivo_aristas)
    guardar_xml(xml_conexiones, archivo_conexiones)

    print(f"\nRed sintética V2: {n}x{n}")
    print(f"Intersecciones de la malla: {n*n}")
    print(f"Tramos interiores bidireccionales: {tramos_interiores}")
    print(f"Flecos bidireccionales: {flecos}")
    print(f"Aristas dirigidas totales: {len(extremos)}")
    print(f"Conexiones sin giros en U: {conexiones}")
    print(f"Distancia centro a centro: {longitud:g} m")
    print(f"Directorio: {salida.resolve()}")

    # 5. Generación de la red final de SUMO.
    netconvert = shutil.which("netconvert")
    if netconvert is None:
        print("\nNo se encontró netconvert: los XML plain sí se han creado.")
        print("Instala SUMO para generar el archivo .net.xml.")
        return

    orden = [
        netconvert,
        "--node-files", str(archivo_nodos),
        "--edge-files", str(archivo_aristas),
        "--connection-files", str(archivo_conexiones),
        "--output-file", str(archivo_red),
        "--no-turnarounds", "true",
        "--no-turnarounds.fringe", "true",
        "--default.junctions.type", "right_before_left",
    ]
    print("\nEjecutando netconvert...")
    try:
        subprocess.run(orden, check=True)
    except subprocess.CalledProcessError as exc:
        print("ERROR: netconvert no pudo generar la red.", file=sys.stderr)
        sys.exit(exc.returncode)

    print(f"Red SUMO lista: {archivo_red.resolve()}")
    print(f"Visualízala: netedit -s '{archivo_red.resolve()}'")


def main():
    parser = argparse.ArgumentParser(
        description="Mapa sintético V2: malla NxN bidireccional con flecos"
    )
    parser.add_argument("-n", "--n", type=int, required=True,
                        help="Número de filas y columnas (N >= 3, par o impar)")
    parser.add_argument("--longitud", type=float, default=100.0,
                        help="Separación entre nodos de la malla o flecos (m)")
    parser.add_argument("--salida", type=Path, default=None,
                        help="Carpeta de salida (por defecto red_NxN)")
    args = parser.parse_args()
    if args.n < 3:
        parser.error("N debe ser al menos 3 (puede ser par o impar)")
    if args.longitud < 20:
        parser.error("La longitud mínima es de 20 metros")
    generar(args.n, args.longitud,
            args.salida if args.salida else Path(f"red_{args.n}x{args.n}"))


if __name__ == "__main__":
    main()
