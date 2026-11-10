# Mapa sintético V3

En esta tercera versión se ha modificado la red de carreteras sintética utilizada para realizar simulaciones de tráfico con **SUMO 1.28.0**.

El mapa se genera mediante el script `mapa_sintetico_v3.py`, que permite modificar el número de intersecciones y la longitud de las carreteras.

Para nuestras pruebas se ha utilizado una red de **5 × 5 intersecciones**, con calles de **200 metros**.

El objetivo es estudiar cómo afecta el aumento de vehículos a la congestión de la red y al rendimiento computacional del simulador.

## 1. Características del mapa

La red presenta las siguientes características:

- **25 intersecciones principales**, separadas 200 metros.
- **Carreteras bidireccionales**, con un carril por sentido.
- **Velocidad máxima de 13,89 m/s**, aproximadamente 50 km/h.
- **Prioridad por la derecha**, sin semáforos.
- **20 tramos exteriores**, denominados flecos, para permitir la entrada y salida de vehículos.
- **Sin giros en U**.
- **Sin carriles internos en las intersecciones**.
- Configuración `keepClear="true"` para intentar evitar que los vehículos bloqueen las intersecciones.

La red está formada por **40 tramos interiores bidireccionales y 20 flecos exteriores**. En total, se generan 120 aristas dirigidas.

### Diferencias respecto a V2

Los principales cambios realizados son:

| Característica | V2 | V3 |
|---|---|---|
| Intersecciones | 5 × 5 | 5 × 5 |
| Longitud de calles | 100 m | 200 m |
| Carreteras | Bidireccionales | Bidireccionales |
| Carriles por sentido | 1 | 1 |
| Prioridad | Por la derecha | Por la derecha |
| Carriles internos | Activados | Desactivados |
| Origen y destino | Flecos exteriores | Aleatorios por la red |
| Distancia mínima utilizada | 200 m | Sin mínimo adicional |

**¿Por qué se han realizado estos cambios?**

En primer lugar, al aumentar la longitud de las calles de 100 a 200 metros, existe más espacio entre intersecciones para almacenar vehículos.

En segundo lugar, se han eliminado los carriles internos mediante `--no-internal-links true`.

Esto simplifica la representación del desplazamiento dentro de los cruces, aunque **los vehículos siguen respetando las reglas de prioridad**.

Por último, se ha modificado la generación de los viajes. En lugar de obligar a los vehículos a comenzar y terminar en los flecos, ahora sus orígenes y destinos se seleccionan aleatoriamente entre las carreteras de la red.

---

## 2. Generación de la red

El mapa se crea ejecutando:

```bash
python3 mapa_sintetico_v3.py -n 5 --longitud 200 --semilla 42
```

Donde:

- **`-n 5`:** establece una red de 5 filas y 5 columnas.
- **`--longitud 200`:** indica una separación de 200 metros entre intersecciones y en los flecos.
- **`--semilla 42`:** permite reproducir la generación de la red.

El script crea automáticamente la carpeta `red_5x5`.

### Archivos generados

Antes de construir la red definitiva, Python genera tres archivos:

| Archivo | Contenido |
|---|---|
| `red_5x5.nod.xml` | Posición y configuración de las intersecciones. |
| `red_5x5.edg.xml` | Carreteras, sentidos de circulación, carriles y velocidades. |
| `red_5x5.con.xml` | Conexiones y movimientos permitidos. |

A partir de estos archivos, **`netconvert`** construye la red definitiva:

`red_5x5.net.xml`

Este archivo es el que posteriormente utiliza SUMO para realizar las simulaciones.

### Configuración de netconvert

Las opciones principales utilizadas son:

```bash
netconvert \
  --node-files red_5x5/red_5x5.nod.xml \
  --edge-files red_5x5/red_5x5.edg.xml \
  --connection-files red_5x5/red_5x5.con.xml \
  --output-file red_5x5/red_5x5.net.xml \
  --no-turnarounds true \
  --no-turnarounds.fringe true \
  --default.junctions.type right_before_left \
  --no-internal-links true
```

**¿Para qué sirve cada parámetro?**

- **`--node-files`:** carga los nodos creados por Python.
- **`--edge-files`:** carga las carreteras.
- **`--connection-files`:** indica qué movimientos están permitidos.
- **`--output-file`:** guarda la red definitiva.
- **`--no-turnarounds true`:** evita que se generen giros en U.
- **`--no-turnarounds.fringe true`:** evita estos giros también en los extremos exteriores.
- **`--default.junctions.type right_before_left`:** establece la prioridad por la derecha.
- **`--no-internal-links true`:** elimina los carriles internos de las intersecciones.

**No es necesario ejecutar manualmente este comando**, ya que el generador se encarga de construir la red.

### Visualización del mapa

Para abrir la red en SUMO-GUI:

```bash
sumo-gui -n red_5x5/red_5x5.net.xml
```

---

## 3. Generación de vehículos

Para generar los viajes utilizamos `randomTrips.py`, una herramienta incluida en SUMO.

En esta versión los vehículos pueden comenzar y terminar sus recorridos en diferentes carreteras de la red, sin obligarlos a utilizar los flecos exteriores.

Por ejemplo, para generar aproximadamente **5000 vehículos**:

```bash
mkdir -p red_5x5/5000_rutas/micro

python3 /usr/share/sumo/tools/randomTrips.py \
  -n red_5x5/red_5x5.net.xml \
  -b 0 \
  -e 3600 \
  -p 0.72 \
  --random-depart \
  --seed 42 \
  -o red_5x5/5000_rutas/trips_5000.trips.xml \
  -r red_5x5/5000_rutas/rutas_5000.rou.xml
```

### Parámetros utilizados

- **`-n`:** indica la red sobre la que se generan los viajes.
- **`-b 0 -e 3600`:** genera las salidas durante una hora simulada.
- **`-p 0.72`:** establece el periodo nominal de generación. Cuanto menor sea, más vehículos se generan.
- **`--random-depart`:** distribuye aleatoriamente los instantes de salida.
- **`--seed 42`:** permite reproducir la generación.
- **`-o`:** guarda los viajes generados.
- **`-r`:** calcula y guarda las rutas que seguirán los vehículos.

**Importante:** en la configuración definitiva no utilizamos `--min-distance 500`, `--fringe-junctions` ni `--fringe-factor max`.

Inicialmente se realizaron algunas pruebas con una distancia mínima de 500 metros, pero se descartaron para la comparación principal porque modificaban considerablemente los recorridos y la congestión observada.

### Cantidades generadas

Se han realizado seis pruebas, modificando principalmente el parámetro `-p`:

| Vehículos aproximados | Parámetro `-p` | Vehículos cargados |
|---|---:|---:|
| 3000 | 1.2 | 3001 |
| 3500 | 1.02857143 | 3500 |
| 4000 | 0.9 | 4000 |
| 4500 | 0.8 | 4500 |
| 5000 | 0.72 | 5001 |
| 5500 | 0.65454545 | 5501 |

El número real de vehículos puede variar ligeramente respecto a la cantidad nominal.

---

## 4. Simulación microscópica

Se han realizado seis simulaciones microscópicas para estudiar cómo cambia el comportamiento de la red al aumentar la cantidad de vehículos.

Todas las pruebas utilizan la misma red y tienen una duración de **3600 segundos simulados**.

Para cada cantidad de vehículos se realizan dos ejecuciones:

- **Simulación completa:** muestra estadísticas, advertencias y guarda los resultados.
- **Simulación limpia:** reduce la información mostrada por pantalla para medir el tiempo real de ejecución.

### 4.1. Simulación completa

Ejemplo para 5000 vehículos:

```bash
{ time sumo \
  -n red_5x5/red_5x5.net.xml \
  -r red_5x5/5000_rutas/rutas_5000.rou.xml \
  --begin 0 \
  --end 3600 \
  --time-to-teleport 300 \
  --duration-log.statistics true \
  --statistic-output red_5x5/5000_rutas/micro/stats.xml \
  --verbose true; } 2>&1 | tee red_5x5/5000_rutas/micro/micro_completo.log
```

**Parámetros utilizados:**

- **`time sumo`:** mide el tiempo real que tarda el ordenador en ejecutar la simulación.
- **`-n`:** indica la red utilizada.
- **`-r`:** carga las rutas generadas.
- **`--begin 0 --end 3600`:** establece una hora de simulación.
- **`--time-to-teleport 300`:** permite teletransportar vehículos en determinadas situaciones de espera prolongada.
- **`--duration-log.statistics true`:** muestra las estadísticas generales al finalizar.
- **`--statistic-output`:** guarda las estadísticas en un archivo XML.
- **`--verbose true`:** muestra información detallada.
- **`tee`:** guarda en un archivo el contenido mostrado por la terminal.

### 4.2. Simulación limpia

Para obtener una medición del tiempo real con menos salida por terminal:

```bash
time sumo \
  -n red_5x5/red_5x5.net.xml \
  -r red_5x5/5000_rutas/rutas_5000.rou.xml \
  --begin 0 \
  --end 3600 \
  --time-to-teleport 300 \
  --verbose false \
  --no-warnings true \
  --no-step-log true
```

**Parámetros adicionales:**

- **`--verbose false`:** desactiva la información detallada.
- **`--no-warnings true`:** evita mostrar las advertencias.
- **`--no-step-log true`:** elimina el registro del progreso de la simulación.

Estas opciones no modifican las reglas de tráfico ni desactivan los teletransportes.

En ambas ejecuciones utilizamos el valor **`real`** proporcionado por el comando `time` de Linux.

---

### 4.3. Resultados: vehículos cargados, insertados y finalizados

| Vehículos | Cargados | Insertados | Finalizados | Circulando | Pendientes de entrar |
|---:|---:|---:|---:|---:|---:|
| 3000 | 3001 | 2992 | 2897 | 95 | 9 |
| 3500 | 3500 | 3486 | 3368 | 118 | 14 |
| 4000 | 4000 | 3969 | 3792 | 177 | 31 |
| 4500 | 4500 | 4379 | 4124 | 255 | 121 |
| **5000** | **5001** | **3698** | **2684** | **1014** | **1303** |
| **5500** | **5501** | **3986** | **2888** | **1098** | **1515** |

**Significado de las columnas:**

- **Cargados (`Loaded`):** vehículos cargados desde el archivo de rutas.
- **Insertados (`Inserted`):** vehículos que consiguieron incorporarse a la red.
- **Finalizados:** vehículos que completaron su recorrido antes de terminar la simulación.
- **Circulando (`Running`):** vehículos que todavía estaban dentro de la red al llegar al segundo 3600.
- **Pendientes (`Waiting`):** vehículos que tenían prevista su salida, pero todavía no habían podido incorporarse a la red.

Se observa que, con 5000 y 5500 vehículos, aumenta considerablemente la cantidad de vehículos pendientes de entrar.

---

### 4.4. Resultados: velocidad, duración y tiempos medios

| Vehículos | Recorrido (m) | Velocidad (m/s) | Duración (s) | Detenido (s) | Tiempo perdido (s) | Retraso incorporación (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 3000 | 1102,87 | 10,81 | 105,98 | 9,77 | 25,57 | 4,03 |
| 3500 | 1099,53 | 10,04 | 117,03 | 17,29 | 36,88 | 6,64 |
| 4000 | 1106,50 | 9,00 | 138,14 | 31,07 | 57,44 | 13,44 |
| 4500 | 1097,62 | 7,87 | 173,00 | 56,62 | 92,71 | 34,05 |
| **5000** | **1096,76** | **7,25** | **248,06** | **127,11** | **165,64** | **32,58** |
| **5500** | **1088,74** | **6,71** | **262,23** | **134,09** | **179,94** | **60,07** |

**Significado de las columnas:**

- **Recorrido (`RouteLength`):** longitud media de las rutas que han completado los vehículos.
- **Velocidad (`Speed`):** velocidad media registrada para los viajes finalizados.
- **Duración (`Duration`):** tiempo medio desde que un vehículo se incorpora a la red hasta que llega a su destino.
- **Detenido (`WaitingTime`):** tiempo medio que los vehículos permanecieron prácticamente parados por circunstancias del tráfico.
- **Tiempo perdido (`TimeLoss`):** tiempo adicional empleado respecto a circular sin demoras a la velocidad deseada.
- **Retraso de incorporación (`DepartDelay`):** diferencia entre el instante en que un vehículo tenía programada su salida y el momento en que consiguió incorporarse realmente a la red.

**Importante:** estas medias corresponden a los vehículos que finalizaron sus recorridos. No incluyen los tiempos de los vehículos que continuaban circulando o estaban pendientes de entrar al finalizar la simulación.

Además, `DepartDelay` no representa el instante exacto de incorporación de cada vehículo, sino el **retraso medio respecto a su salida programada**.

### Observaciones

A medida que aumenta la cantidad de vehículos:

- La velocidad media disminuye progresivamente.
- Aumenta el tiempo necesario para completar los recorridos.
- Los vehículos permanecen más tiempo detenidos.
- Aumenta el tiempo perdido respecto a una circulación sin demoras.

El cambio más importante aparece entre **4500 y 5000 vehículos**.

Con 4500 vehículos, el tiempo detenido medio es de 56,62 segundos.

Con 5000 vehículos, aumenta hasta 127,11 segundos.

También se observa que el retraso de incorporación llega a **60,07 segundos con 5500 vehículos**, aunque la media corresponde únicamente a los viajes finalizados.

---

### 4.5. Resultados: teletransportes y frenadas de emergencia

| Vehículos | Teleports `yield` | Teleports `jam` | Total teleports | Frenadas de emergencia |
|---:|---:|---:|---:|---:|
| 3000 | 0 | 0 | 0 | 1 |
| 3500 | 0 | 0 | 0 | 1 |
| 4000 | 0 | 0 | 0 | 0 |
| 4500 | 0 | 0 | 0 | 1 |
| **5000** | **92** | **4** | **96** | **0** |
| **5500** | **110** | **12** | **122** | **1** |

**Significado de las columnas:**

- **`yield`:** teletransporte asociado a una espera prolongada al ceder el paso.
- **`jam`:** teletransporte asociado a una situación de atasco.
- **Total teleports:** número total de teletransportes registrados durante la simulación.
- **Frenadas de emergencia (`Emergency Braking`):** número de eventos en los que un vehículo necesitó desacelerar más bruscamente de lo deseado.

Una frenada de emergencia no implica necesariamente que se haya producido una colisión.

En las simulaciones de 3000 a 4500 vehículos no se registraron teletransportes.

Sin embargo, con 5000 vehículos aparecieron 96 teletransportes y con 5500 aumentaron hasta 122.

---

### 4.6. Resultados: tiempos reales de ejecución

Se han registrado los tiempos de ambas ejecuciones utilizando el comando `time` de Linux.

| Vehículos | Tiempo real completo (s) | Tiempo real limpio (s) |
|---:|---:|---:|
| 3000 | 0,674 | 0,673 |
| 3500 | 0,855 | 0,834 |
| 4000 | 1,152 | 1,099 |
| 4500 | 1,621 | 1,563 |
| **5000** | **5,330** | **4,339** |
| **5500** | **5,966** | **5,216** |

**Diferencia entre ambos tiempos:**

- **Tiempo completo:** corresponde a la ejecución con estadísticas y advertencias mostradas por pantalla.
- **Tiempo limpio:** corresponde a la ejecución con menos información mostrada y se utiliza como referencia principal para comparar el rendimiento computacional.

Ambos tiempos representan segundos reales de ejecución, no los 3600 segundos simulados.

Se observa que el tiempo de ejecución aumenta progresivamente con la cantidad de vehículos, especialmente a partir de 5000.
