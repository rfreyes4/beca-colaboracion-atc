
#!/usr/bin/env python3

"""
Genera los programas semaforicos del MAPA SINTETICO V4.

Cada interseccion tiene cuatro fases principales:

1. Norte-Sur:
   - Recto y derecha: verde con prioridad (G).
   - Izquierda: verde sin prioridad (g).
     Puede girar si no hay trafico contrario.

2. Norte-Sur izquierda:
   - Izquierda: verde protegido (G).
   - Recto y derecha: rojo (r).

3. Este-Oeste:
   - Recto y derecha: verde con prioridad (G).
   - Izquierda: verde sin prioridad (g).

4. Este-Oeste izquierda:
   - Izquierda: verde protegido (G).
   - Recto y derecha: rojo (r).

Entre las fases principales:
- Amarillo: 3 segundos.
- Rojo general: 2 segundos.
"""

from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


# ============================================================
# ARCHIVOS
# ============================================================

ARCHIVO_RED = Path("red_7x7/red_7x7.net.xml")
ARCHIVO_SALIDA = Path("red_7x7/semaforos.add.xml")


# ============================================================
# TIEMPOS SEMAFORICOS
# ============================================================

TIEMPO_RECTO_DERECHA = 30
TIEMPO_IZQUIERDA = 8
TIEMPO_AMARILLO = 3
TIEMPO_ROJO_TOTAL = 2


# ============================================================
# FASES
# ============================================================

# Cada fase indica:
# (nombre, procedencias, tipo de fase, duracion)

FASES = (
    (
        "Norte-Sur recto, derecha e izquierda permitida",
        {"N", "S"},
        "mixta",
        TIEMPO_RECTO_DERECHA
    ),
    (
        "Norte-Sur izquierda protegida",
        {"N", "S"},
        "izquierda",
        TIEMPO_IZQUIERDA
    ),
    (
        "Este-Oeste recto, derecha e izquierda permitida",
        {"E", "O"},
        "mixta",
        TIEMPO_RECTO_DERECHA
    ),
    (
        "Este-Oeste izquierda protegida",
        {"E", "O"},
        "izquierda",
        TIEMPO_IZQUIERDA
    ),
)


# ============================================================
# DETERMINAR PROCEDENCIA
# ============================================================

def procedencia(nodos, origen, cruce):
    """Determina desde que lado llega un vehiculo."""

    x_origen, y_origen = nodos[origen]
    x_cruce, y_cruce = nodos[cruce]

    dx = x_origen - x_cruce
    dy = y_origen - y_cruce

    if abs(dx) < 0.01 and abs(dy) > 0.01:
        return "N" if dy > 0 else "S"

    if abs(dy) < 0.01 and abs(dx) > 0.01:
        return "E" if dx > 0 else "O"

    raise ValueError(
        f"Arista no ortogonal hacia {cruce}: origen {origen}"
    )


# ============================================================
# LEER CONEXIONES DE LA RED
# ============================================================

def leer_conexiones(raiz):
    """
    Asocia cada indice semaforico con su procedencia
    y movimiento: recto, derecha o izquierda.
    """

    nodos = {
        j.get("id"): (
            float(j.get("x")),
            float(j.get("y"))
        )
        for j in raiz.findall("junction")
    }

    aristas = {
        e.get("id"): (
            e.get("from"),
            e.get("to")
        )
        for e in raiz.findall("edge")
        if e.get("from") is not None
        and e.get("to") is not None
    }

    semaforos = {
        j.get("id")
        for j in raiz.findall("junction")
        if j.get("type") == "traffic_light"
    }

    conexiones = defaultdict(dict)

    for c in raiz.findall("connection"):

        cruce = c.get("tl")

        if cruce is None:
            continue

        if cruce not in semaforos:
            raise ValueError(
                f"Semaforo desconocido: {cruce}"
            )

        indice = int(c.get("linkIndex"))
        id_entrada = c.get("from")

        if id_entrada not in aristas:
            raise ValueError(
                f"No existe la arista: {id_entrada}"
            )

        origen, destino = aristas[id_entrada]

        if destino != cruce:
            raise ValueError(
                f"Conexion inesperada en {cruce}"
            )

        lado = procedencia(
            nodos,
            origen,
            cruce
        )

        giro = c.get("dir", "").lower()

        if giro not in {"s", "r", "l"}:
            raise ValueError(
                f"Giro inesperado en {cruce}: {giro!r}"
            )

        if indice in conexiones[cruce]:
            raise ValueError(
                f"Indice {indice} repetido en {cruce}"
            )

        conexiones[cruce][indice] = (
            lado,
            giro
        )

    if semaforos != set(conexiones):
        raise ValueError(
            "Hay semaforos sin conexiones controladas"
        )

    return conexiones


# ============================================================
# CONSTRUIR ESTADOS DE LOS SEMAFOROS
# ============================================================

def crear_estado(indices, movimientos, lados, tipo):
    """
    Construye el estado de una fase.

    G = Verde con prioridad.
    g = Verde sin prioridad (ceder el paso).
    r = Rojo.
    """

    estados = []

    for indice in indices:

        lado, giro = movimientos[indice]

        # Los movimientos de otros sentidos permanecen en rojo.
        if lado not in lados:
            estados.append("r")
            continue

        if tipo == "mixta":

            # Recto y derecha tienen prioridad.
            if giro in {"s", "r"}:
                estados.append("G")

            # Izquierda puede avanzar si no hay trafico contrario.
            elif giro == "l":
                estados.append("g")

        elif tipo == "izquierda":

            # Verde protegido para girar a la izquierda.
            if giro == "l":
                estados.append("G")

            # Recto y derecha permanecen en rojo.
            else:
                estados.append("r")

        else:
            raise ValueError(
                f"Tipo de fase desconocido: {tipo}"
            )

    return "".join(estados)


# ============================================================
# CREAR PROGRAMA SEMAFORICO
# ============================================================

def crear_programa(raiz_salida, id_semaforo, movimientos):
    """
    Crea el programa de cuatro fases principales
    con sus correspondientes amarillos y rojos.
    """

    indices = sorted(movimientos)

    if indices != list(range(12)):
        raise ValueError(
            f"{id_semaforo}: se esperaban 12 conexiones "
            f"con indices 0..11; se encontraron {indices}"
        )

    programa = ET.SubElement(
        raiz_salida,
        "tlLogic",
        {
            "id": id_semaforo,
            "type": "static",
            "programID": "manual_giro_permitido",
            "offset": "0",
        }
    )

    todos_rojos = "r" * len(indices)

    # Contamos cuantas fases permiten cada movimiento.
    cobertura = {i: 0 for i in indices}

    for nombre, lados, tipo, duracion in FASES:

        # ----------------------------------------------------
        # FASE PRINCIPAL
        # ----------------------------------------------------

        verde = crear_estado(
            indices,
            movimientos,
            lados,
            tipo
        )

        if not any(estado in {"G", "g"} for estado in verde):
            raise ValueError(
                f"{id_semaforo}: fase sin movimientos: {nombre}"
            )

        for indice, estado in zip(indices, verde):
            if estado in {"G", "g"}:
                cobertura[indice] += 1

        ET.SubElement(
            programa,
            "phase",
            {
                "duration": str(duracion),
                "state": verde,
                "name": nombre,
            }
        )

        # ----------------------------------------------------
        # FASE DE AMARILLO
        # ----------------------------------------------------

        # Los movimientos que tenian verde pasan a amarillo.
        # Los que estaban en rojo permanecen en rojo.

        amarillo = "".join(
            "y" if estado in {"G", "g"} else "r"
            for estado in verde
        )

        ET.SubElement(
            programa,
            "phase",
            {
                "duration": str(TIEMPO_AMARILLO),
                "state": amarillo,
                "name": "Amarillo",
            }
        )

        # ----------------------------------------------------
        # ROJO GENERAL
        # ----------------------------------------------------

        ET.SubElement(
            programa,
            "phase",
            {
                "duration": str(TIEMPO_ROJO_TOTAL),
                "state": todos_rojos,
                "name": "Rojo general",
            }
        )

    # ========================================================
    # COMPROBACION DE MOVIMIENTOS
    # ========================================================

    for indice, (_, giro) in movimientos.items():

        # Los giros a la izquierda aparecen en dos fases:
        # 1. Permitido, cediendo el paso.
        # 2. Protegido, con prioridad.
        #
        # Recto y derecha aparecen una sola vez.

        esperado = 2 if giro == "l" else 1

        if cobertura[indice] != esperado:
            raise ValueError(
                f"{id_semaforo}: movimiento {indice} "
                f"aparece {cobertura[indice]} veces; "
                f"se esperaban {esperado}"
            )


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    if not ARCHIVO_RED.is_file():
        raise SystemExit(
            f"No se encuentra la red: {ARCHIVO_RED}"
        )

    raiz_red = ET.parse(
        ARCHIVO_RED
    ).getroot()

    conexiones = leer_conexiones(
        raiz_red
    )

    raiz_salida = ET.Element(
        "additional"
    )

    for id_semaforo in sorted(conexiones):

        crear_programa(
            raiz_salida,
            id_semaforo,
            conexiones[id_semaforo]
        )

    ET.indent(
        raiz_salida,
        space="  "
    )

    ET.ElementTree(
        raiz_salida
    ).write(
        ARCHIVO_SALIDA,
        encoding="utf-8",
        xml_declaration=True
    )

    # ========================================================
    # CALCULAR DURACION TOTAL DEL CICLO
    # ========================================================

    ciclo = (
        2 * TIEMPO_RECTO_DERECHA
        + 2 * TIEMPO_IZQUIERDA
        + 4 * (
            TIEMPO_AMARILLO
            + TIEMPO_ROJO_TOTAL
        )
    )

    print()
    print("==========================================")
    print("SEMAFOROS MAPA SINTETICO V4")
    print("==========================================")
    print(f"Semaforos configurados: {len(conexiones)}")
    print("Fases principales: 4")
    print()
    print(f"Recto y derecha: {TIEMPO_RECTO_DERECHA} s")
    print("Izquierda permitida durante verde de recto")
    print(f"Izquierda protegida: {TIEMPO_IZQUIERDA} s")
    print(f"Amarillo: {TIEMPO_AMARILLO} s")
    print(f"Rojo general: {TIEMPO_ROJO_TOTAL} s")
    print()
    print(f"Duracion del ciclo: {ciclo} segundos")
    print(f"Archivo generado: {ARCHIVO_SALIDA.resolve()}")
    print("==========================================")


if __name__ == "__main__":
    main()
