#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import xml.etree.ElementTree as ET

from collections import defaultdict
from math import hypot
from pathlib import Path


# ============================================================
# MAPA SINTETICO V5
#
# Red de 7x7 intersecciones
# Carreteras de 200 metros
# Velocidad maxima: 50 km/h
#
# DISEÑO:
#
# - Un carril principal por sentido.
# - Carriles principales completamente rectos.
# - Separacion central de 6.4 metros.
# - Bolsillos izquierdos de 40 metros.
# - Carril 0: recto o derecha.
# - Carril 1: solamente izquierda.
# - Sin adelantamientos dentro de los bolsillos.
#
# ============================================================


# ============================================================
# GUARDAR ARCHIVOS XML
# ============================================================

def guardar_xml(raiz, ruta):

    ET.indent(raiz, space="  ")

    ET.ElementTree(raiz).write(
        ruta,
        encoding="utf-8",
        xml_declaration=True
    )


# ============================================================
# GENERADOR PRINCIPAL
# ============================================================

def generar(n, longitud, bolsillo, salida):

    salida.mkdir(parents=True, exist_ok=True)

    prefijo = f"red_{n}x{n}"

    ruta_nodos = salida / f"{prefijo}.nod.xml"
    ruta_aristas = salida / f"{prefijo}.edg.xml"
    ruta_conexiones = salida / f"{prefijo}.con.xml"
    ruta_red = salida / f"{prefijo}.net.xml"

    nodos = ET.Element("nodes")
    aristas = ET.Element("edges")
    conexiones = ET.Element("connections")

    posiciones = {}

    entradas = defaultdict(list)
    salidas = defaultdict(list)

    nombres_aristas = set()
    calles = []

    numero_bolsillos = 0
    numero_conexiones = 0

    # ========================================================
    # CREAR NODOS
    # ========================================================

    def nodo(identificador, x, y, clase="interior"):

        if identificador in posiciones:

            raise ValueError(
                f"Nodo repetido: {identificador}"
            )

        posiciones[identificador] = (x, y)

        datos = {
            "id": identificador,
            "x": f"{x:.2f}",
            "y": f"{y:.2f}"
        }

        if clase == "interior":

            datos.update(
                type="traffic_light",
                tlType="static",
                tlLayout="opposites",
                keepClear="true"
            )

        elif clase == "exterior":

            datos["fringe"] = "outer"

        else:

            datos["type"] = "priority"

        ET.SubElement(
            nodos,
            "node",
            datos
        )

    # ========================================================
    # CREAR ARISTAS
    # ========================================================

    def arista(
        identificador,
        origen,
        destino,
        carriles=1,
        forma=None
    ):

        if identificador in nombres_aristas:

            raise ValueError(
                f"Arista repetida: {identificador}"
            )

        nombres_aristas.add(identificador)

        x0, y0 = posiciones[origen]
        x1, y1 = posiciones[destino]

        datos = {
            "id": identificador,
            "from": origen,
            "to": destino,
            "priority": "1",
            "numLanes": str(carriles),
            "speed": "13.89",
            "spreadType": "right",
            "length": f"{hypot(x1-x0, y1-y0):.2f}"
        }

        # Geometria personalizada
        if forma is not None:

            datos["shape"] = forma

        elemento = ET.SubElement(
            aristas,
            "edge",
            datos
        )

        # ====================================================
        # CARRILES EXCLUSIVOS DE GIRO A LA IZQUIERDA
        # ====================================================

        if carriles == 2:

            # Carril 0:
            # Continuar recto o girar a la derecha.
            #
            # Los vehiculos normales no pueden cambiar
            # al carril izquierdo dentro del bolsillo.

            ET.SubElement(
                elemento,
                "lane",
                {
                    "index": "0",
                    "changeLeft": "authority emergency"
                }
            )

            # Carril 1:
            # Exclusivamente giro a la izquierda.
            #
            # Los vehiculos normales no pueden cambiar
            # al carril derecho dentro del bolsillo.

            ET.SubElement(
                elemento,
                "lane",
                {
                    "index": "1",
                    "changeRight": "authority emergency"
                }
            )

    # ========================================================
    # CREAR CONEXIONES
    # ========================================================

    def conexion(
        origen,
        destino,
        carril_origen,
        carril_destino
    ):

        nonlocal numero_conexiones

        ET.SubElement(
            conexiones,
            "connection",
            {
                "from": origen,
                "to": destino,
                "fromLane": str(carril_origen),
                "toLane": str(carril_destino)
            }
        )

        numero_conexiones += 1

    # ========================================================
    # IDENTIFICADORES Y COORDENADAS
    # ========================================================

    def id_cruce(r, c):

        return f"j-{r}-{c}"

    def xy_cruce(r, c):

        x = c * longitud
        y = (n - 1 - r) * longitud

        return x, y

    # ========================================================
    # CREAR INTERSECCIONES INTERIORES
    # ========================================================

    for r in range(n):

        for c in range(n):

            nodo(
                id_cruce(r, c),
                *xy_cruce(r, c)
            )

            # Carretera horizontal
            if c + 1 < n:

                calles.append(
                    (
                        id_cruce(r, c),
                        id_cruce(r, c + 1)
                    )
                )

            # Carretera vertical
            if r + 1 < n:

                calles.append(
                    (
                        id_cruce(r, c),
                        id_cruce(r + 1, c)
                    )
                )

    # ========================================================
    # NODOS EXTERIORES: NORTE Y SUR
    # ========================================================

    for c in range(n):

        for lado, fila, dy in (
            ("n", 0, longitud),
            ("s", n - 1, -longitud)
        ):

            exterior = f"ext-{lado}-{c}"

            x, y = xy_cruce(fila, c)

            nodo(
                exterior,
                x,
                y + dy,
                "exterior"
            )

            calles.append(
                (
                    id_cruce(fila, c),
                    exterior
                )
            )

    # ========================================================
    # NODOS EXTERIORES: OESTE Y ESTE
    # ========================================================

    for r in range(n):

        for lado, columna, dx in (
            ("o", 0, -longitud),
            ("e", n - 1, longitud)
        ):

            exterior = f"ext-{lado}-{r}"

            x, y = xy_cruce(r, columna)

            nodo(
                exterior,
                x + dx,
                y,
                "exterior"
            )

            calles.append(
                (
                    id_cruce(r, columna),
                    exterior
                )
            )

    # ========================================================
    # GEOMETRIA RECTA CON SEPARACION CENTRAL
    # ========================================================

    def forma_recta(origen, destino):

        """
        Mantiene completamente recto el carril principal.

        Cada sentido se desplaza lateralmente 3.2 metros
        respecto al eje central de la carretera.

        Como spreadType es 'right', el centro del carril
        queda otros 1.6 metros hacia la derecha.

        Resultado:

        - Carril principal: 4.8 m del eje central.
        - Separacion libre entre sentidos: 6.4 m.

        En los ultimos 40 metros, el segundo carril
        ocupa una parte de esta separacion central.

        No hay zigzags ni cambios de trayectoria.
        """

        x0, y0 = posiciones[origen]
        x1, y1 = posiciones[destino]

        dx = x1 - x0
        dy = y1 - y0

        distancia = hypot(dx, dy)

        # Vector perpendicular hacia la derecha
        nx = dy / distancia
        ny = -dx / distancia

        # Desplazamiento lateral del eje
        separacion = 3.20

        # Punto inicial
        inicio_x = x0 + nx * separacion
        inicio_y = y0 + ny * separacion

        # Punto final
        final_x = x1 + nx * separacion
        final_y = y1 + ny * separacion

        # Solamente dos puntos:
        # la carretera sera completamente recta.

        return (
            f"{inicio_x:.3f},{inicio_y:.3f} "
            f"{final_x:.3f},{final_y:.3f}"
        )

    # ========================================================
    # CREAR CARRETERAS
    # ========================================================

    def carretera(origen, destino):

        nonlocal numero_bolsillos

        principal = f"e-{origen}-a-{destino}"

        salidas[origen].append(
            (
                principal,
                destino
            )
        )

        # ====================================================
        # CARRETERA QUE TERMINA EN UNA INTERSECCION
        # ====================================================

        if destino.startswith("j-"):

            x0, y0 = posiciones[origen]
            x1, y1 = posiciones[destino]

            proporcion = bolsillo / longitud

            # Nodo situado 40 metros antes del cruce
            previo = f"p-{origen}-a-{destino}"

            nodo(
                previo,
                x1 + (x0 - x1) * proporcion,
                y1 + (y0 - y1) * proporcion,
                "intermedio"
            )

            final = principal + "-fin"

            # =================================================
            # PRIMER TRAMO: UN CARRIL RECTO
            # =================================================

            arista(
                principal,
                origen,
                previo,
                carriles=1,
                forma=forma_recta(
                    origen,
                    previo
                )
            )

            # =================================================
            # ULTIMOS 40 METROS: DOS CARRILES
            # =================================================

            # El carril derecho conserva su trayectoria.
            #
            # El izquierdo utiliza el espacio central.
            #
            # Por eso aqui NO desplazamos la geometria.

            arista(
                final,
                previo,
                destino,
                carriles=2
            )

            # =================================================
            # CONEXIONES DE ENTRADA AL BOLSILLO
            # =================================================

            # Acceso al carril derecho
            conexion(
                principal,
                final,
                0,
                0
            )

            # Acceso al carril izquierdo
            conexion(
                principal,
                final,
                0,
                1
            )

            entradas[destino].append(
                (
                    final,
                    origen
                )
            )

            numero_bolsillos += 1

        # ====================================================
        # CARRETERA QUE SALE HACIA EL EXTERIOR
        # ====================================================

        else:

            arista(
                principal,
                origen,
                destino,
                carriles=1,
                forma=forma_recta(
                    origen,
                    destino
                )
            )

    # ========================================================
    # GENERAR CARRETERAS EN AMBOS SENTIDOS
    # ========================================================

    for a, b in calles:

        carretera(a, b)
        carretera(b, a)

    # ========================================================
    # CREAR CONEXIONES EN LAS INTERSECCIONES
    # ========================================================

    for r in range(n):

        for c in range(n):

            cruce = id_cruce(r, c)

            x, y = posiciones[cruce]

            movimientos = 0

            for entrada, origen in entradas[cruce]:

                x0, y0 = posiciones[origen]

                vin = (
                    x - x0,
                    y - y0
                )

                for salida, destino in salidas[cruce]:

                    # Prohibir giros de 180 grados
                    if origen == destino:
                        continue

                    x2, y2 = posiciones[destino]

                    vsal = (
                        x2 - x,
                        y2 - y
                    )

                    # Determinar el movimiento
                    producto_cruzado = (
                        vin[0] * vsal[1]
                        - vin[1] * vsal[0]
                    )

                    # =================================================
                    # GIRO A LA IZQUIERDA
                    # =================================================

                    if producto_cruzado > 0:

                        carril = 1

                    # =================================================
                    # RECTO O GIRO A LA DERECHA
                    # =================================================

                    else:

                        carril = 0

                    conexion(
                        entrada,
                        salida,
                        carril,
                        0
                    )

                    movimientos += 1

            # Cuatro accesos con tres movimientos cada uno
            if movimientos != 12:

                raise ValueError(
                    f"{cruce}: se esperaban 12 movimientos, "
                    f"pero hay {movimientos}"
                )

    # ========================================================
    # GUARDAR ARCHIVOS XML
    # ========================================================

    guardar_xml(
        nodos,
        ruta_nodos
    )

    guardar_xml(
        aristas,
        ruta_aristas
    )

    guardar_xml(
        conexiones,
        ruta_conexiones
    )

    # ========================================================
    # INFORMACION DE LA RED
    # ========================================================

    print()
    print(f"Red sintetica V5: {n}x{n}")
    print(f"Longitud por carretera: {longitud:g} m")
    print(f"Tramo de un carril: {longitud - bolsillo:g} m")
    print(f"Bolsillo izquierdo: {bolsillo:g} m")
    print(f"Separacion central: 6.4 m")
    print(f"Intersecciones semaforizadas: {n * n}")
    print(f"Bolsillos de giro: {numero_bolsillos}")
    print(f"Aristas dirigidas: {len(nombres_aristas)}")
    print(f"Conexiones: {numero_conexiones}")
    print()

    # ========================================================
    # GENERAR RED SUMO
    # ========================================================

    programa = shutil.which("netconvert")

    if programa is None:

        raise SystemExit(
            "ERROR: No se encuentra netconvert."
        )

    orden = [
        programa,

        "--node-files",
        str(ruta_nodos),

        "--edge-files",
        str(ruta_aristas),

        "--connection-files",
        str(ruta_conexiones),

        "--output-file",
        str(ruta_red),

        "--no-turnarounds",
        "true",

        "--no-turnarounds.fringe",
        "true",

        "--no-internal-links",
        "true"
    ]

    print("Ejecutando netconvert...")

    subprocess.run(
        orden,
        check=True
    )

    print()
    print(f"Red SUMO generada: {ruta_red.resolve()}")


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generador V5: carriles rectos y "
            "bolsillos izquierdos centrales"
        )
    )

    parser.add_argument(
        "-n",
        type=int,
        default=7,
        help="Numero de filas y columnas"
    )

    parser.add_argument(
        "--longitud",
        type=float,
        default=200.0,
        help="Longitud de las carreteras en metros"
    )

    parser.add_argument(
        "--bolsillo",
        type=float,
        default=40.0,
        help="Longitud del bolsillo de giro izquierdo"
    )

    parser.add_argument(
        "--salida",
        type=Path,
        default=None,
        help="Carpeta donde se guarda la red"
    )

    args = parser.parse_args()

    if (
        args.n < 3
        or args.longitud <= 0
        or not (0 < args.bolsillo < args.longitud / 2)
    ):

        parser.error(
            "Se requiere n >= 3 y "
            "0 < bolsillo < longitud/2"
        )

    salida = (
        args.salida
        or Path(f"red_{args.n}x{args.n}")
    )

    generar(
        args.n,
        args.longitud,
        args.bolsillo,
        salida
    )


if __name__ == "__main__":

    main()
