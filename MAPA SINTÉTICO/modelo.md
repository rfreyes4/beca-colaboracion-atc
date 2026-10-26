# Generación de mapa sintético en SUMO

## Descripción

El script `mapa_sintetico.py` genera una red sintética de carreteras en forma de cuadrícula NxN, permitiendo configurar el número de intersecciones, la distancia entre ellas y la semilla aleatoria.

## Comando utilizado

```bash
python3 mapa_sintetico.py -n 5 --longitud 100 --semilla 42
```

**Parámetros:**
- `-n 5`: genera una red de 5×5 intersecciones.
- `--longitud 100`: distancia de 100 metros entre intersecciones.
- `--semilla 42`: fija la semilla para obtener resultados reproducibles.

## Visualización en SUMO

Para abrir la red generada:

```bash
sumo-gui -n red_5x5/red_5x5.net.xml
```

Este comando abre SUMO-GUI y carga el archivo `.net.xml`, que contiene la red de carreteras generada. Permite visualizar las intersecciones y las conexiones entre ellas.

## Resultado

Red sintética de **25 intersecciones y 16 manzanas**, visualizada en SUMO-GUI.

![Red sintética 5x5](imagenes/resultado.png)

---

## Generación de tráfico

Para generar vehículos se utiliza `randomTrips.py`, una herramienta de SUMO que crea viajes aleatorios sobre la red de carreteras.

Como ejemplo, se generan aproximadamente **1.000 vehículos durante una hora simulada (3.600 segundos)**.

Primero se crea una carpeta para guardar los archivos correspondientes:

```bash
mkdir -p red_5x5/1000_rutas
```

Después se generan los viajes y las rutas:

```bash
python3 /usr/share/sumo/tools/randomTrips.py \
  -n red_5x5/red_5x5.net.xml \
  -b 0 \
  -e 3600 \
  -p 3.6 \
  --random-depart \
  --seed 42 \
  -o red_5x5/1000_rutas/trips_1000.trips.xml \
  -r red_5x5/1000_rutas/rutas_1000.rou.xml
```

Este comando genera los vehículos y asigna sus recorridos dentro de la red.

Los parámetros principales son:

- `-n`: indica la red de carreteras utilizada.
- `-b 0` y `-e 3600`: establecen el periodo de generación de los vehículos.
- `-p 3.6`: determina el intervalo de generación para obtener aproximadamente 1.000 vehículos.
- `--random-depart`: distribuye aleatoriamente los tiempos de salida.
- `--seed 42`: permite reproducir la generación.
- `-o`: guarda los viajes generados.
- `-r`: guarda las rutas que utilizará SUMO.

Para generar diferentes cantidades de vehículos, se modifica el parámetro `-p` y los nombres de los archivos correspondientes.

## Visualización de la simulación

Una vez generadas las rutas, se utiliza SUMO-GUI para observar cómo circulan los vehículos por la red.

```bash
sumo-gui \
  -n red_5x5/red_5x5.net.xml \
  -r red_5x5/1000_rutas/rutas_1000.rou.xml \
  --begin 0 \
  --end 3600 \
  --delay 20
```

Este comando carga la red y las rutas generadas, ejecutando una simulación de una hora.

- `-n`: carga la red de carreteras.
- `-r`: carga las rutas de los vehículos.
- `--begin` y `--end`: establecen el inicio y final de la simulación.
- `--delay 20`: introduce un pequeño retardo para facilitar la visualización.

De esta forma, se puede observar el movimiento de los vehículos, las intersecciones y las posibles acumulaciones de tráfico.

## Medición del rendimiento

Para medir el tiempo de ejecución y obtener estadísticas, se utiliza SUMO sin interfaz gráfica.

```bash
time sumo \
  -n red_5x5/red_5x5.net.xml \
  -r red_5x5/1000_rutas/rutas_1000.rou.xml \
  --begin 0 \
  --end 3600 \
  --duration-log.statistics \
  --statistic-output red_5x5/1000_rutas/micro_1000_stats.xml \
  --log red_5x5/1000_rutas/micro_1000.log
```

Este comando ejecuta la simulación y permite analizar tanto su rendimiento como el comportamiento del tráfico.

- `time`: mide el tiempo real necesario para ejecutar SUMO.
- `--duration-log.statistics`: muestra estadísticas generales al finalizar.
- `--statistic-output`: guarda las estadísticas de la simulación en un archivo XML.
- `--log`: guarda el registro de ejecución, incluidos los posibles avisos.

Entre los resultados obtenidos se encuentran el número de vehículos insertados, los que finalizan sus recorridos, los vehículos pendientes de incorporarse, los tiempos medios de viaje y espera, y los posibles teletransportes.

Los archivos generados se almacenan en la carpeta correspondiente para facilitar su posterior análisis y comparación.


