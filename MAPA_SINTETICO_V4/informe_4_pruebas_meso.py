#!/usr/bin/env python3
"""Auditoria de las cuatro pruebas MESO progresivas frente a MICRO.

Colocar este archivo en la raiz de MAPA_SINTETICO_V4 y ejecutar:
    python3 informe_4_pruebas_meso.py

Solo anade instrumentos de salida. No modifica la red, las rutas, los
semaforos, el enrutamiento ni los parametros de las cuatro pruebas.
Requiere Python 3.9+ y SUMO disponible como comando `sumo`.
"""

import argparse
import csv
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from xml.sax.saxutils import quoteattr


DEMANDAS = (3000, 4000, 5000, 6000, 7000, 8000, 9000, 11000)
CASOS = {
    "micro": (False, None, None),
    "prueba_1_progresivos": (True, False, 200),
    "prueba_2_progresivos": (True, False, 100),
    "prueba_3_progresivos": (True, False, 50),
    "prueba_4_ltm_progresivos": (True, True, 100),
}
ETIQUETAS = {
    "micro": "MICRO referencia",
    "prueba_1_progresivos": "MESO 1: 200 m",
    "prueba_2_progresivos": "MESO 2: 100 m",
    "prueba_3_progresivos": "MESO 3: 50 m",
    "prueba_4_ltm_progresivos": "MESO 4: LTM 100 m",
}
# Valores del MICRO progresivo estatico anotados previamente en modelo.md.
# No se usan para simular; solo para verificar la reproduccion de la referencia.
MICRO_HISTORICO = {
    3000: (2649, 0), 4000: (3464, 0), 5000: (4070, 0),
    6000: (4403, 6), 7000: (4419, 46), 8000: (3804, 128),
    9000: (4068, 129), 11000: (3722, 249),
}
TELEPORT_RE = re.compile(
    r"Warning:\s+Teleporting vehicle\s+'[^']+';\s*(.*?),\s*from edge\s+'([^']+)'[^,]*,\s*time=([0-9]+(?:\.[0-9]+)?)"
)


def numero(value, fallback=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def entero(value):
    return int(numero(value))


def csv_guardar(ruta, campos, filas):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore", delimiter=";")
        writer.writeheader()
        writer.writerows(filas)


def texto_guardar(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")


def hash_archivo(ruta):
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def comprobar_entradas(proyecto, demandas):
    red = proyecto / "red_7x7"
    obligatorios = [
        red / "red_7x7.net.xml",
        red / "semaforos.add.xml",
        red / "semaforos_progresivos_rectas.add.xml",
    ]
    obligatorios += [red / f"{n}_rutas" / f"rutas_{n}.rou.xml" for n in demandas]
    faltantes = [str(x) for x in obligatorios if not x.is_file()]
    if faltantes:
        raise FileNotFoundError("Faltan entradas:\n" + "\n".join(faltantes))
    return obligatorios


def comando_sumo(proyecto, carpeta, caso, demanda):
    red = proyecto / "red_7x7"
    es_meso, ltm, longitud = CASOS[caso]
    originales = [red / "semaforos.add.xml", red / "semaforos_progresivos_rectas.add.xml"]
    # El detector de edgeData SOLO mide. No define semaforos ni modifica el trafico.
    xml_medidor = carpeta / "medidor_solo_salida.add.xml"
    ruta_edgedata = carpeta / "aristas_60s.xml"
    texto_guardar(
        xml_medidor,
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<additional>\n'
        f'  <edgeData id="diagnostico_60s" period="60" file={quoteattr(str(ruta_edgedata))} '
        'excludeEmpty="true"/>\n'
        '</additional>\n',
    )
    comando = [
        "sumo",
        "-n", str(red / "red_7x7.net.xml"),
        "-r", str(red / f"{demanda}_rutas" / f"rutas_{demanda}.rou.xml"),
        "-a", ",".join(str(x) for x in (*originales, xml_medidor)),
        "--begin", "0", "--end", "3600", "--seed", "42",
        "--time-to-teleport", "300",
        "--device.rerouting.probability", "0",
        "--no-step-log", "true",
        "--tripinfo-output", str(carpeta / "viajes.xml"),
        "--tripinfo-output.write-unfinished", "true",
        "--summary-output", str(carpeta / "evolucion_red.xml"),
        "--summary-output.period", "60",
        "--statistic-output", str(carpeta / "estadisticas.xml"),
        "--duration-log.statistics", "true",
    ]
    if es_meso:
        comando += [
            "--mesosim", "true",
            "--meso-ltm", "true" if ltm else "false",
            "--meso-edgelength", str(longitud),
            "--meso-junction-control", "true",
            "--meso-junction-control.limited", "false",
            "--meso-jam-threshold", "-1",
            "--meso-overtaking", "false",
        ]
    return comando


def leer_estadisticas(ruta):
    if not ruta.exists():
        return {}
    raiz = ET.parse(ruta).getroot()
    out = {}
    for etiqueta in ("vehicles", "teleports", "vehicleTripStatistics", "performance"):
        item = raiz.find(etiqueta)
        if item is not None:
            out[etiqueta] = dict(item.attrib)
    return out


def leer_viajes(ruta):
    terminados = []
    sin_terminar = []
    for _, elemento in ET.iterparse(ruta, events=("end",)):
        if elemento.tag != "tripinfo":
            continue
        attr = elemento.attrib
        viaje = {
            "id": attr.get("id", ""),
            "depart": numero(attr.get("depart")),
            "arrival": numero(attr.get("arrival"), -1),
            "duration": numero(attr.get("duration")),
            "routeLength": numero(attr.get("routeLength")),
            "waitingTime": numero(attr.get("waitingTime")),
            "timeLoss": numero(attr.get("timeLoss")),
            "departDelay": numero(attr.get("departDelay")),
        }
        (terminados if viaje["arrival"] >= 0 else sin_terminar).append(viaje)
        elemento.clear()
    return terminados, sin_terminar


def leer_teleports(ruta):
    encontrados = []
    with ruta.open(encoding="utf-8", errors="replace") as f:
        for linea in f:
            m = TELEPORT_RE.search(linea)
            if m:
                encontrados.append({
                    "motivo": m.group(1), "arista": m.group(2),
                    "segundo": numero(m.group(3)),
                })
    return encontrados


def leer_evolucion(ruta):
    filas = []
    for _, elemento in ET.iterparse(ruta, events=("end",)):
        if elemento.tag != "step":
            continue
        a = elemento.attrib
        filas.append({
            "segundo": numero(a.get("time")),
            "insertados": entero(a.get("inserted")),
            "circulando": entero(a.get("running")),
            "pendientes_entrada": entero(a.get("waiting")),
            "terminados_o_retirados": entero(a.get("ended")),
            "llegados": entero(a.get("arrived")) if "arrived" in a else "",
            "parados": entero(a.get("halting")) if "halting" in a else "",
            "velocidad_media_mps": numero(a.get("meanSpeed"), -1),
        })
        elemento.clear()
    return filas


def leer_aristas(ruta):
    """Generador de estadisticas por arista e intervalo, sin cargar todo en RAM."""
    inicio, final = 0.0, 0.0
    for evento, elemento in ET.iterparse(ruta, events=("start", "end")):
        if evento == "start" and elemento.tag == "interval":
            inicio = numero(elemento.get("begin"))
            final = numero(elemento.get("end"))
        elif evento == "end" and elemento.tag == "edge":
            a = elemento.attrib
            yield {
                "arista": a.get("id", ""),
                "inicio": inicio, "fin": final,
                "velocidad_mps": numero(a.get("speed"), -1),
                "densidad_veh_km": numero(a.get("density"), -1),
                "ocupacion_pct": numero(a.get("occupancy"), -1),
                "segundos_muestreados": numero(a.get("sampledSeconds")),
                "espera_total_s": numero(a.get("waitingTime")),
                "entraron": entero(a.get("entered")),
                "salieron": entero(a.get("left")),
            }
            elemento.clear()
        elif evento == "end" and elemento.tag == "interval":
            elemento.clear()


def detectar_bloqueos(ruta, teleports):
    # Criterio de ALERTA, no prueba de deadlock:
    # velocidad < 2 m/s y densidad >= 15 veh/km durante >= 3 minutos.
    # Como se agregan 60 s, el bloqueo puede ser intermitente entre rojos.
    por_arista = defaultdict(list)
    for x in leer_aristas(ruta):
        if x["segundos_muestreados"] > 0:
            por_arista[x["arista"]].append(x)
    teleports_por_arista = Counter(x["arista"] for x in teleports)
    focos = []
    for arista, serie in por_arista.items():
        serie.sort(key=lambda x: x["inicio"])
        tramo = []

        def cerrar_tramo():
            if not tramo:
                return
            duracion = tramo[-1]["fin"] - tramo[0]["inicio"]
            if duracion >= 180:
                focos.append({
                    "arista": arista,
                    "inicio_s": tramo[0]["inicio"],
                    "fin_s": tramo[-1]["fin"],
                    "duracion_s": duracion,
                    "velocidad_media_mps": round(mean(x["velocidad_mps"] for x in tramo), 3),
                    "densidad_max_veh_km": round(max(x["densidad_veh_km"] for x in tramo), 2),
                    "salidas_en_periodo": sum(x["salieron"] for x in tramo),
                    "teleports_total_en_arista": teleports_por_arista[arista],
                })

        for x in serie:
            lento = (x["velocidad_mps"] >= 0 and x["velocidad_mps"] < 2
                     and x["densidad_veh_km"] >= 15 and x["segundos_muestreados"] >= 30)
            if lento:
                if tramo and x["inicio"] != tramo[-1]["fin"]:
                    cerrar_tramo()
                    tramo = []
                tramo.append(x)
            else:
                cerrar_tramo()
                tramo = []
        cerrar_tramo()
    return sorted(focos, key=lambda x: (-x["duracion_s"], -x["densidad_max_veh_km"]))


def leer_log_antiguo(ruta):
    if not ruta.exists():
        return None
    contenido = ruta.read_text(encoding="utf-8", errors="replace")
    def extraer(patron):
        m = re.search(patron, contenido, re.MULTILINE)
        return entero(m.group(1)) if m else None
    return {
        "insertados": extraer(r"^\s*Inserted:\s*(\d+)"),
        "terminados": extraer(r"^\s*Statistics \(avg of (\d+)\)"),
        "circulando": extraer(r"^\s*Running:\s*(\d+)"),
        "pendientes": extraer(r"^\s*Waiting:\s*(\d+)"),
        "teleports": len(leer_teleports(ruta)),
    }


def analizar_ejecucion(salida, caso, demanda):
    carpeta = salida / caso / str(demanda)
    archivos = ("viajes.xml", "evolucion_red.xml", "estadisticas.xml", "aristas_60s.xml", "ejecucion.log")
    if not all((carpeta / x).exists() for x in archivos):
        raise FileNotFoundError(f"Resultados incompletos en {carpeta}")
    stats = leer_estadisticas(carpeta / "estadisticas.xml")
    terminados, no_terminados = leer_viajes(carpeta / "viajes.xml")
    tps = leer_teleports(carpeta / "ejecucion.log")
    evolucion = leer_evolucion(carpeta / "evolucion_red.xml")
    focos = detectar_bloqueos(carpeta / "aristas_60s.xml", tps)
    veh = stats.get("vehicles", {})
    tele = stats.get("teleports", {})
    ultima = evolucion[-1] if evolucion else {}
    datos = {
        "caso": caso, "demanda": demanda, "insertados": entero(veh.get("inserted")) if veh else ultima.get("insertados", 0),
        "terminados": len(terminados), "en_red_final": entero(veh.get("running")) if veh else ultima.get("circulando", 0),
        "sin_entrar_final": entero(veh.get("waiting")) if veh else ultima.get("pendientes_entrada", 0),
        "teleports": entero(tele.get("total")) if tele else len(tps),
        "teleports_detectados_en_log": len(tps),
        "duracion_terminados_s": round(mean(x["duration"] for x in terminados), 2) if terminados else None,
        "espera_terminados_s": round(mean(x["waitingTime"] for x in terminados), 2) if terminados else None,
        "perdida_terminados_s": round(mean(x["timeLoss"] for x in terminados), 2) if terminados else None,
        "duracion_incompletos_s": round(mean(x["duration"] for x in no_terminados), 2) if no_terminados else None,
        "viajes_incompletos_registrados": len(no_terminados),
        "focos_persistentes": len(focos),
        "max_circulando": max((x["circulando"] for x in evolucion), default=0),
        "max_sin_entrar": max((x["pendientes_entrada"] for x in evolucion), default=0),
    }
    return datos, evolucion, tps, focos


def comparar_aristas(salida, casos, demanda):
    """Comparacion por arista a lo largo de los 60 intervalos, ponderada por presencia."""
    por_caso = {}
    for caso in casos:
        ruta = salida / caso / str(demanda) / "aristas_60s.xml"
        acumulado = defaultdict(lambda: [0., 0., 0., 0., 0.])
        for e in leer_aristas(ruta):
            if e["velocidad_mps"] < 0 or e["segundos_muestreados"] <= 0:
                continue
            a = acumulado[e["arista"]]
            peso = e["segundos_muestreados"]
            a[0] += peso
            a[1] += peso * e["velocidad_mps"]
            a[2] += peso * max(e["densidad_veh_km"], 0)
            a[3] += e["salieron"]
            a[4] += e["espera_total_s"]
        por_caso[caso] = acumulado
    micro = por_caso.get("micro", {})
    diferencias = []
    for caso in casos:
        if caso == "micro":
            continue
        for edge, a in por_caso[caso].items():
            b = micro.get(edge)
            if not b or a[0] < 300 or b[0] < 300:
                continue  # poco trafico: comparacion inestable
            velocidad_meso = a[1] / a[0]
            velocidad_micro = b[1] / b[0]
            diferencias.append({
                "demanda": demanda, "caso": caso, "arista": edge,
                "velocidad_meso_mps": round(velocidad_meso, 3),
                "velocidad_micro_mps": round(velocidad_micro, 3),
                "delta_velocidad_mps": round(velocidad_meso - velocidad_micro, 3),
                "densidad_meso_veh_km": round(a[2] / a[0], 2),
                "densidad_micro_veh_km": round(b[2] / b[0], 2),
                "salidas_meso": int(a[3]), "salidas_micro": int(b[3]),
                "espera_total_meso_s": round(a[4], 2),
                "espera_total_micro_s": round(b[4], 2),
            })
    return sorted(diferencias, key=lambda x: abs(x["delta_velocidad_mps"]), reverse=True)


def crear_informes(salida, proyecto, demandas, casos, version):
    resumen = []
    teleports_todos = []
    bloqueos_todos = []
    evoluciones = []
    diferencias_aristas = []
    comprobacion = []
    por_demanda = defaultdict(dict)

    for demanda in demandas:
        for caso in casos:
            datos, evolucion, tps, focos = analizar_ejecucion(salida, caso, demanda)
            resumen.append(datos)
            por_demanda[demanda][caso] = datos
            for e in evolucion:
                evoluciones.append({"demanda": demanda, "caso": caso, **e})
            for tp in tps:
                teleports_todos.append({"demanda": demanda, "caso": caso, **tp})
            for foco in focos:
                bloqueos_todos.append({"demanda": demanda, "caso": caso, **foco})
            if caso != "micro":
                original = proyecto / "meso" / caso / f"meso_{demanda}.log"
                previo = leer_log_antiguo(original)
                if previo is not None:
                    comprobacion.append({
                        "demanda": demanda, "caso": caso,
                        "antiguos_insertados": previo["insertados"],
                        "auditoria_insertados": datos["insertados"],
                        "antiguos_terminados": previo["terminados"],
                        "auditoria_terminados": datos["terminados"],
                        "antiguos_teleports": previo["teleports"],
                        "auditoria_teleports": datos["teleports"],
                        "coinciden": (previo["insertados"] == datos["insertados"]
                                     and previo["terminados"] == datos["terminados"]
                                     and previo["teleports"] == datos["teleports"]),
                    })
        if "micro" in casos:
            diferencias_aristas.extend(comparar_aristas(salida, casos, demanda))

    csv_guardar(salida / "01_resumen_global.csv", list(resumen[0]), resumen)
    csv_guardar(salida / "02_evolucion_60s.csv",
               ["demanda", "caso", "segundo", "insertados", "circulando", "pendientes_entrada",
                "terminados_o_retirados", "llegados", "parados", "velocidad_media_mps"], evoluciones)
    csv_guardar(salida / "03_teleports_detallados.csv",
               ["demanda", "caso", "segundo", "arista", "motivo"], teleports_todos)
    csv_guardar(salida / "04_sospechas_bloqueo_persistente.csv",
               ["demanda", "caso", "arista", "inicio_s", "fin_s", "duracion_s", "velocidad_media_mps",
                "densidad_max_veh_km", "salidas_en_periodo", "teleports_total_en_arista"], bloqueos_todos)
    csv_guardar(salida / "05_diferencias_aristas_vs_micro.csv",
               ["demanda", "caso", "arista", "velocidad_meso_mps", "velocidad_micro_mps",
                "delta_velocidad_mps", "densidad_meso_veh_km", "densidad_micro_veh_km",
                "salidas_meso", "salidas_micro", "espera_total_meso_s", "espera_total_micro_s"], diferencias_aristas)
    csv_guardar(salida / "06_verificacion_con_logs_originales.csv",
               ["demanda", "caso", "antiguos_insertados", "auditoria_insertados",
                "antiguos_terminados", "auditoria_terminados", "antiguos_teleports",
                "auditoria_teleports", "coinciden"], comprobacion)
    comparar = []
    for d in demandas:
        micro = por_demanda[d].get("micro")
        for caso in casos:
            if caso == "micro" or micro is None:
                continue
            row = por_demanda[d][caso]
            comparar.append({
                "demanda": d, "caso": caso,
                "llegados_meso": row["terminados"], "llegados_micro": micro["terminados"],
                "diferencia_llegados": row["terminados"] - micro["terminados"],
                "teleports_meso": row["teleports"], "teleports_micro": micro["teleports"],
                "diferencia_teleports": row["teleports"] - micro["teleports"],
                "pendientes_entrada_meso": row["sin_entrar_final"],
                "pendientes_entrada_micro": micro["sin_entrar_final"],
                "diferencia_duracion_llegados_s": round(
                    row["duracion_terminados_s"] - micro["duracion_terminados_s"], 2
                ) if row["duracion_terminados_s"] is not None and micro["duracion_terminados_s"] is not None else None,
                "diferencia_espera_llegados_s": round(
                    row["espera_terminados_s"] - micro["espera_terminados_s"], 2
                ) if row["espera_terminados_s"] is not None and micro["espera_terminados_s"] is not None else None,
            })
    csv_guardar(salida / "07_diferencias_globales_vs_micro.csv",
               ["demanda", "caso", "llegados_meso", "llegados_micro", "diferencia_llegados",
                "teleports_meso", "teleports_micro", "diferencia_teleports",
                "pendientes_entrada_meso", "pendientes_entrada_micro",
                "diferencia_duracion_llegados_s", "diferencia_espera_llegados_s"], comparar)

    problemas_reproduccion = [x for x in comprobacion if not x["coinciden"]]
    micro_desvio = []
    if "micro" in casos:
        for d in demandas:
            observado = por_demanda[d]["micro"]
            ref = MICRO_HISTORICO.get(d)
            if ref and (observado["terminados"], observado["teleports"]) != ref:
                micro_desvio.append(
                    f"- {d}: MICRO historico {ref[0]} llegados/{ref[1]} teleports; "
                    f"auditoria {observado['terminados']}/{observado['teleports']}."
                )

    lineas = [
        "# Informe de diagnostico: cuatro MESO progresivos vs MICRO",
        "",
        f"Fecha: {datetime.now().isoformat(timespec='seconds')}  |  SUMO: {version}",
        "",
        "## Metodo y limites",
        "",
        "- Misma red, rutas y semaforos progresivos; seed 42; 0-3600 s; sin enrutamiento dinamico.",
        "- MESO 1 = convencional 200 m; MESO 2 = convencional 100 m; MESO 3 = convencional 50 m; MESO 4 = LTM 100 m.",
        "- MICRO se ejecuta de nuevo como referencia, con los mismos archivos y opciones comunes.",
        "- Unicamente se anaden salidas de observacion. Los resultados originales no se modifican.",
        "- **Importante**: medias de duracion/espera se calculan SOLO para viajes terminados. "
        "Los no terminados tambien aparecen en sus propios recuentos y XML.",
        "- **Sospecha de bloqueo** = velocidad de arista < 2 m/s y densidad >= 15 veh/km "
        "en >= 3 intervalos consecutivos de 60 s, con al menos 30 vehiculo-segundos/intervalo. "
        "No demuestra un deadlock: los semaforos rojos tambien producen colas.",
        "- Los tiempos de MICRO y MESO son modelos diferentes: la salida no permite atribuir "
        "por si sola una causa mecanica exacta a un semaforo o cruce.",
        "",
        "## Reproduccion de los datos anteriores",
        "",
        f"- Logs MESO anteriores encontrados: {len(comprobacion)} de {4 * len(demandas)}.",
        f"- Diferencias con logs MESO anteriores: {len(problemas_reproduccion)}.",
        f"- Diferencias con tabla MICRO historica: {len(micro_desvio)}.",
    ]
    if problemas_reproduccion:
        lineas.extend(["", "Las ejecuciones nuevas no reproducen estas cifras antiguas:"])
        lineas.extend(
            f"- {x['caso']} / {x['demanda']}: "
            f"llegados {x['antiguos_terminados']} -> {x['auditoria_terminados']}; "
            f"teleports {x['antiguos_teleports']} -> {x['auditoria_teleports']}."
            for x in problemas_reproduccion
        )
    if micro_desvio:
        lineas.extend(["", "La referencia MICRO no coincide con el historico. "
                       "Antes de atribuir diferencias a MESO, verificar version y comando de MICRO:"] + micro_desvio)

    lineas.extend(["", "## Llegados al final de la simulacion", "",
                   "| Demanda | MICRO | MESO 1 (200) | MESO 2 (100) | MESO 3 (50) | MESO 4 (LTM) |",
                   "|---:|---:|---:|---:|---:|---:|"])
    orden = list(CASOS)
    for d in demandas:
        v = por_demanda[d]
        lineas.append("| " + str(d) + " | " + " | ".join(
            str(v[c]["terminados"]) if c in v else "—" for c in orden
        ) + " |")
    lineas.extend(["", "## Teletransportes", "",
                   "| Demanda | MICRO | MESO 1 | MESO 2 | MESO 3 | MESO 4 LTM |",
                   "|---:|---:|---:|---:|---:|---:|"])
    for d in demandas:
        v = por_demanda[d]
        lineas.append("| " + str(d) + " | " + " | ".join(
            str(v[c]["teleports"]) if c in v else "—" for c in orden
        ) + " |")

    lineas.extend(["", "## Indicios que permiten investigar el desacuerdo", ""])
    for d in demandas:
        v = por_demanda[d]
        lineas.append(f"### Demanda {d}")
        if "micro" in v:
            micro = v["micro"]
            lineas.append(
                f"MICRO: {micro['terminados']} terminados; {micro['sin_entrar_final']} pendientes "
                f"de insercion; {micro['en_red_final']} circulando al llegar a 3600 s; "
                f"{micro['teleports']} teleports."
            )
        for c in casos:
            if c == "micro":
                continue
            x = v[c]
            delta = f" (diferencia de {x['terminados'] - v['micro']['terminados']:+d} con MICRO)" if "micro" in v else ""
            lineas.append(
                f"- {ETIQUETAS[c]}: {x['terminados']} terminados{delta}; "
                f"{x['en_red_final']} en red, {x['sin_entrar_final']} esperando entrar, "
                f"{x['teleports']} teleports, {x['focos_persistentes']} focos candidatos."
            )
        por_tp = Counter(x["arista"] for x in teleports_todos if x["demanda"] == d and x["caso"] != "micro")
        if por_tp:
            lineas.append("- Aristas con mas teleports MESO combinados: " + ", ".join(
                f"`{arista}` ({count})" for arista, count in por_tp.most_common(5)
            ) + ".")
        por_foco = [x for x in bloqueos_todos if x["demanda"] == d]
        if por_foco:
            por_foco.sort(key=lambda x: x["duracion_s"], reverse=True)
            lineas.append("- Alertas de congestion prolongada: " + ", ".join(
                f"`{x['arista']}` [{x['caso']}, {int(x['inicio_s'])}-{int(x['fin_s'])} s]"
                for x in por_foco[:5]
            ) + ".")
        lineas.append("")

    lineas.extend([
        "## Como interpretar las causas", "",
        "1. **Diferente insercion:** comparar `insertados`, `pendientes_entrada` y la evolucion "
        "en `02_evolucion_60s.csv`. Si MICRO no puede insertar vehiculos que MESO si, "
        "las medias de viajes completados tienen poblaciones distintas.",
        "2. **Cuellos de botella concretos:** agrupar `03_teleports_detallados.csv` por arista y "
        "tiempo. Coincidencias con `04_sospechas_bloqueo_persistente.csv` son fuertes "
        "indicios de congestion recurrente, no necesariamente error de configuracion.",
        "3. **Diferencias de flujo locales:** buscar las aristas mas discordantes "
        "en `05_diferencias_aristas_vs_micro.csv`. Revisar velocidades, densidades "
        "y salidas por arista; estas ultimas pueden estar afectadas por teleports.",
        "4. **Dinamica del modelo:** el MESO convencional representa colas por segmentos; "
        "LTM propaga los huecos hacia atras. Incluso con igual semaforizacion pueden "
        "formarse y disiparse colas de otra manera.",
        "5. **Sesgo de viajes terminados:** a 3600 s no todos llegan. Una media menor "
        "puede deberse a que los mas lentos no terminaron. Hay viajes sin terminar "
        "en cada `viajes.xml` y contadores en `01_resumen_global.csv`.",
        "",
        "## Estructura de archivos", "",
        f"- `01_resumen_global.csv`: estadisticas de las {len(casos) * len(demandas)} combinaciones analizadas.",
        "- `02_evolucion_60s.csv`: evolucion de inserciones, circulantes y pendientes.",
        "- `03_teleports_detallados.csv`: carretera y segundo de cada teleport.",
        "- `04_sospechas_bloqueo_persistente.csv`: alertas de congestion prolongada.",
        "- `05_diferencias_aristas_vs_micro.csv`: diferencia en velocidad, densidad, flujo y espera por carretera.",
        "- `06_verificacion_con_logs_originales.csv`: comprobacion de reproducibilidad.",
        "- `07_diferencias_globales_vs_micro.csv`: diferencias globales por demanda.",
        "- `CASO/DEMANDA/`: comando, log de ejecucion, viajes, resumen temporal, aristas, estadisticas.",
        "",
        "Fuentes: https://sumo.dlr.de/docs/Simulation/Meso.html ; "
        "https://sumo.dlr.de/docs/Simulation/Output/StatisticOutput.html ; "
        "https://sumo.dlr.de/docs/Simulation/Output/Lane-_or_Edge-based_Traffic_Measures.html",
        "",
    ])
    texto_guardar(salida / "INFORME_GENERAL.md", "\n".join(lineas))
    print(f"\nINFORME COMPLETADO: {salida / 'INFORME_GENERAL.md'}")
    print("CSV principales:", ", ".join(str(i).zfill(2) for i in range(1, 8)))
    if problemas_reproduccion or micro_desvio:
        print("ATENCION: hay diferencias de reproduccion; comprobar el apartado del informe.")


def ejecutar(proyecto, salida, demandas, casos):
    print("SUMO:", subprocess.run(["sumo", "--version"], capture_output=True,
                                    text=True, check=True).stdout.splitlines()[0])
    archivos = comprobar_entradas(proyecto, demandas)
    salida.mkdir(parents=True, exist_ok=False)
    hashes = {str(x.relative_to(proyecto)): hash_archivo(x) for x in archivos}
    (salida / "huellas_entradas.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    n_total = len(demandas) * len(casos)
    progreso = 0
    for demanda in demandas:
        for caso in casos:
            progreso += 1
            carpeta = salida / caso / str(demanda)
            carpeta.mkdir(parents=True, exist_ok=True)
            comando = comando_sumo(proyecto, carpeta, caso, demanda)
            texto_guardar(carpeta / "comando.txt", shlex.join(comando) + "\n")
            print(f"[{progreso:02d}/{n_total}] {ETIQUETAS[caso]} - {demanda}", flush=True)
            with (carpeta / "ejecucion.log").open("w", encoding="utf-8") as log:
                p = subprocess.run(comando, cwd=proyecto, stdout=log, stderr=subprocess.STDOUT, check=False)
            if p.returncode:
                raise RuntimeError(
                    f"SUMO fallo (codigo {p.returncode}). Revisar: {carpeta / 'ejecucion.log'}\n"
                    "Puedes continuar el analisis de ejecuciones completadas despues de corregirlo."
                )


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proyecto", type=Path, default=Path(__file__).resolve().parent,
                   help="Carpeta MAPA_SINTETICO_V4 (por defecto: carpeta del script)")
    p.add_argument("--demandas", type=int, nargs="+", default=list(DEMANDAS), choices=DEMANDAS)
    p.add_argument("--sin-micro", action="store_true", help="Solo los 4 MESO; sin comparacion local con MICRO")
    p.add_argument("--analizar", type=Path, metavar="CARPETA",
                   help="No ejecuta SUMO; regenera los CSV y el informe desde una auditoria ya hecha")
    args = p.parse_args()
    proyecto = args.proyecto.expanduser().resolve()
    casos = [x for x in CASOS if x != "micro"] if args.sin_micro else list(CASOS)
    if args.analizar:
        salida = args.analizar.expanduser().resolve()
        if not salida.is_dir():
            p.error("--analizar necesita una carpeta existente")
    else:
        if shutil.which("sumo") is None:
            p.error("No encuentro 'sumo' en el PATH. Comprueba con: sumo --version")
        sello = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        salida = proyecto / "meso" / f"auditoria_4_pruebas_{sello}"
        ejecutar(proyecto, salida, args.demandas, casos)
    version = "desconocida"
    if shutil.which("sumo"):
        s = subprocess.run(["sumo", "--version"], capture_output=True, text=True, check=False)
        version = (s.stdout.splitlines() or ["desconocida"])[0]
    crear_informes(salida, proyecto, args.demandas, casos, version)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ET.ParseError, RuntimeError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)
