# Mapa sintético V2 — Red bidireccional y simulación microscópica con SUMO

Documentación de la segunda versión de la red sintética utilizada para estudiar el comportamiento del tráfico y comparar modelos de simulación en **SUMO 1.28.0**.

## 1. Diseño y generación del mapa

La red se construye mediante el script Python **[mapa_sintetico_v2.py](./mapa_sintetico_v2.py)**. Permite generar una malla de tamaño `N × N` y establecer la distancia entre intersecciones.

Para el experimento se ha utilizado una **malla de 5 × 5 (25 intersecciones)** con las siguientes características:

| Característica | Configuración |
|---|---|
| Intersecciones | 25, distribuidas en una malla 5 × 5 |
| Separación entre intersecciones | 100 m |
| Circulación | Bidireccional; un carril por sentido |
| Velocidad máxima | 13,89 m/s (aprox. 50 km/h) |
| Regulación | Prioridad por la derecha (`right_before_left`), sin semáforos |
| Accesos exteriores | 20 tramos adicionales (*flecos*), de 100 m cada uno |
| Giros | Recto, izquierda o derecha según la conexión; sin giros en U |

### Principales diferencias respecto a la V1

- **Calles bidireccionales:** cada tramo puede recorrerse en los dos sentidos, con una arista dirigida y un carril para cada sentido.
- **Entradas y salidas exteriores:** se añaden 20 flecos perpendiculares al perímetro de la malla. Sus nodos tienen `fringe="outer"` y sirven como límites de entrada y salida del tráfico.
- **Prioridad por la derecha:** las intersecciones usan `type="right_before_left"`, en lugar de depender de prioridades asignadas a distintas calles.
- **Prevención de bloqueo dentro del cruce:** `keepClear="true"` activa la heurística que intenta evitar que un vehículo entre si probablemente quedará detenido y bloqueará la intersección. **No elimina todos los atascos.**
- **Sin giros en U:** el generador no crea conexiones que devuelvan al vehículo inmediatamente por la vía de la que viene. Además, `netconvert` se ejecuta con `--no-turnarounds true` y `--no-turnarounds.fringe true`; este último evita construir retornos en los extremos marcados como `fringe="outer"`.

La red se genera en tres archivos XML editables (`.nod.xml`, `.edg.xml`, `.con.xml`); **`netconvert`** los transforma en `red_5x5.net.xml`, utilizado por SUMO.

### Comando de generación

Ejecutar desde la carpeta `MAPA SINTETICO V2`:

```bash
python3 mapa_sintetico_v2.py -n 5 --longitud 100
```

- `-n 5`: crea cinco filas y cinco columnas de intersecciones.
- `--longitud 100`: fija 100 metros entre intersecciones y para los flecos.
- **Salida por defecto:** carpeta `red_5x5/` (se puede cambiar con `--salida`).

### Visualización del mapa

```bash
sumo-gui -n red_5x5/red_5x5.net.xml
```

<!-- Cuando se suba la captura a imagenes/mapa_sintetico_v2.png, se puede activar esta línea:
![Vista de la red sintética V2](imagenes/mapa_sintetico_v2.png)
-->

## 2. Generación de rutas con `randomTrips.py`

Se generan viajes con origen y destino en los **flecos exteriores** para evaluar distintos niveles de demanda durante **3600 segundos (una hora simulada)**. Se emplea la misma semilla para que las pruebas sean reproducibles.

Los cuatro comandos siguientes muestran cuatro niveles representativos de las pruebas. Cada uno guarda sus viajes y rutas en una carpeta independiente.

### 2000 vehículos (demanda nominal)

```bash
mkdir -p red_5x5/2000_rutas
python3 /usr/share/sumo/tools/randomTrips.py \
  -n red_5x5/red_5x5.net.xml \
  -b 0 -e 3600 -p 1.8 \
  --random-depart --seed 42 \
  --fringe-factor max --fringe-junctions \
  --min-distance 200 \
  -o red_5x5/2000_rutas/viajes_2000.trips.xml \
  --route-file red_5x5/2000_rutas/rutas_2000.rou.xml
```

### 3000 vehículos (demanda nominal)

```bash
mkdir -p red_5x5/3000_rutas
python3 /usr/share/sumo/tools/randomTrips.py \
  -n red_5x5/red_5x5.net.xml \
  -b 0 -e 3600 -p 1.2 \
  --random-depart --seed 42 \
  --fringe-factor max --fringe-junctions \
  --min-distance 200 \
  -o red_5x5/3000_rutas/viajes_3000.trips.xml \
  --route-file red_5x5/3000_rutas/rutas_3000.rou.xml
```

### 4500 vehículos (demanda nominal)

```bash
mkdir -p red_5x5/4500_rutas
python3 /usr/share/sumo/tools/randomTrips.py \
  -n red_5x5/red_5x5.net.xml \
  -b 0 -e 3600 -p 0.8 \
  --random-depart --seed 42 \
  --fringe-factor max --fringe-junctions \
  --min-distance 200 \
  -o red_5x5/4500_rutas/viajes_4500.trips.xml \
  --route-file red_5x5/4500_rutas/rutas_4500.rou.xml
```

### 5000 vehículos (demanda nominal)

```bash
mkdir -p red_5x5/5000_rutas
python3 /usr/share/sumo/tools/randomTrips.py \
  -n red_5x5/red_5x5.net.xml \
  -b 0 -e 3600 -p 0.72 \
  --random-depart --seed 42 \
  --fringe-factor max --fringe-junctions \
  --min-distance 200 \
  -o red_5x5/5000_rutas/viajes_5000.trips.xml \
  --route-file red_5x5/5000_rutas/rutas_5000.rou.xml
```

### Significado de los parámetros

| Parámetro | Función |
|---|---|
| `-n` | Archivo de la red sobre la que se crean los viajes. |
| `-b 0` / `-e 3600` | Intervalo de salidas: del segundo 0 al 3600 (límite superior). |
| `-p` | Intervalo nominal entre viajes, en segundos: cuanto menor, mayor demanda. |
| `--random-depart` | Distribuye aleatoriamente los instantes de salida dentro del intervalo. |
| `--seed 42` | Hace reproducible la generación aleatoria. |
| `--fringe-factor max` | Fuerza que los viajes comiencen y terminen en la periferia de la red. |
| `--fringe-junctions` | Utiliza el atributo `fringe` de los nodos para identificar los accesos exteriores. |
| `--min-distance 200` | Exige una separación mínima de 200 m entre origen y destino. |
| `-o` | Guarda los viajes propuestos (`.trips.xml`). |
| `--route-file` | Calcula y guarda las rutas válidas (`.rou.xml`). |

También se probaron demandas nominales de **2500, 3500 y 4000 vehículos**. Para reproducirlas, se emplea el mismo comando cambiando `-p` a **1,44**, **3600/3500 ≈ 1,02857** y **0,9**, respectivamente, y ajustando los nombres de las carpetas y archivos.

> **Nota:** la demanda nominal no tiene por qué coincidir exactamente con el número de vehículos generado. Por ejemplo, con `-p 0.72` se obtuvieron **5001 vehículos**, comprobados en el archivo de rutas. Asimismo, los coches con salida programada cerca del segundo 3600 pueden no alcanzar su destino antes de terminar la simulación.

## 3. Simulación microscópica

El modelo microscópico representa individualmente los vehículos y su interacción con el resto del tráfico, incluidas las decisiones de ceder el paso.

### Ejecución y medición del tiempo

Ejemplo para la demanda nominal de 5000 vehículos:

```bash
time sumo \
  -n red_5x5/red_5x5.net.xml \
  -r red_5x5/5000_rutas/rutas_5000.rou.xml \
  --begin 0 --end 3600 \
  --time-to-teleport 300 \
  --duration-log.statistics \
  --statistic-output red_5x5/5000_rutas/micro_5000_stats.xml \
  --log red_5x5/5000_rutas/micro_5000.log
```

- `time sumo`: mide cuánto tarda el ordenador en ejecutar la simulación.
- `--begin` / `--end`: fija la hora simulada.
- `--time-to-teleport 300`: permite teletransportar vehículos después de ciertas esperas prolongadas (300 s), para resolver bloqueos.
- `--duration-log.statistics`: muestra estadísticas al finalizar.
- `--statistic-output` y `--log`: guardan estadísticas y mensajes de ejecución.

### Resultados generales

Experimentos de **3600 s simulados**, con la misma red V2:

| Demanda nominal | Insertados | Finalizados | Pendientes de entrar | Velocidad media (m/s) | Espera media (s) | Teleports | Tiempo real (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2000 | 2000 | 1962 | 0 | 9,49 | 3,77 | — | 0,506 |
| 2500 | 2500 | 2447 | 0 | 8,98 | 6,77 | 0 | 0,652 |
| 3000 | 3001 | 2925 | 0 | 8,43 | 10,56 | 0 | 0,782 |
| 3500 | 3500 | 3406 | 0 | 7,66 | 17,82 | 0 | 0,984 |
| 4000 | 4000 | 3865 | 0 | 6,56 | 32,62 | 0 | 1,476 |
| 4500 | 4481 | 4316 | 19 | 5,42 | 56,11 | 0 | 2,106 |
| **5000** | **3180** | **2511** | **1821** | **3,96** | **229,07** | **130** | **6,976** |

**Qué representa cada columna:**

- **Demanda nominal:** número aproximado de viajes que se pretende generar en una hora.
- **Insertados:** vehículos que lograron entrar físicamente en la red antes del segundo 3600.
- **Finalizados:** vehículos que completaron su recorrido dentro del intervalo.
- **Pendientes de entrar:** vehículos con salida prevista que no pudieron incorporarse por falta de espacio.
- **Velocidad media:** velocidad media informada por SUMO para los recorridos finalizados.
- **Espera media:** tiempo medio de espera en esos recorridos finalizados; no incluye la espera final de todos los vehículos aún sin terminar.
- **Teleports:** teletransportaciones utilizadas por SUMO para resolver esperas prolongadas; `—` significa dato no verificado.
- **Tiempo real:** tiempo de ejecución del comando, medido por la utilidad `time` (`real`), en segundos; **no** equivale al tiempo simulado.

**Interpretación:** hasta 4500 vehículos, casi toda la demanda logra incorporarse. En la prueba nominal de **5000**, solo entran **3180 de 5001** vehículos; quedan **1821 esperando**, la espera media aumenta hasta **229,07 s** y se registran **130 teletransportaciones**: **109 por `yield`** (espera al ceder el paso) y **21 por `jam`** (atasco). Son indicadores claros de **saturación severa en este escenario**. No implican que todas las intersecciones estén bloqueadas ni prueban, por sí solos, un bloqueo circular.

## 4. Bloqueo circular: «la pescadilla que se muerde la cola»

### 4.1. ¿Cómo se produce?

En un cruce sin semáforos y con **prioridad por la derecha**, pueden llegar cuatro vehículos al mismo tiempo. Supongamos que sus movimientos entran en conflicto y que todos quieren seguir recto:

```text
                       NORTE
                         A
                         ↓
                         │
        OESTE      B →───┼───← D      ESTE
                         │
                         ↑
                         C
                         SUR
```

Según la prioridad por la derecha:

| Vehículo | Procedencia | Espera al vehículo |
|---|---|---|
| **A** | Norte | **B**, que llega por su derecha (oeste) |
| **B** | Oeste | **C**, que llega por su derecha (sur) |
| **C** | Sur | **D**, que llega por su derecha (este) |
| **D** | Este | **A**, que llega por su derecha (norte) |

Se forma la dependencia **A → B → C → D → A**: todos esperan a otro y nadie encuentra inicialmente una oportunidad para pasar. A este fenómeno lo denominamos **bloqueo circular de cesión de paso** (*circular yielding*).

### 4.2. ¿Cómo intenta resolverlo SUMO 1.28.0?

El mecanismo está implementado en el archivo **`MSVehicle.cpp` del código fuente oficial**, dentro de la evaluación de movimientos en intersecciones:

**[Ver el código fuente de SUMO 1.28.0: `MSVehicle.cpp`, líneas 2999–3019](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/src/microsim/MSVehicle.cpp#L2999-L3019)**.

En términos sencillos, SUMO:

1. **Comprueba las condiciones** del vehículo que está evaluando: una conexión de prioridad equivalente (`LINKSTATE_EQUAL`) y tiempo de espera acumulado (`myWaitingTime > 0`).
2. **Busca dependencias** entre vehículos que se aproximan a movimientos conflictivos mediante `getFirstApproachingFoe(...)`. Si la cadena regresa a la conexión inicial, reconoce un posible bloqueo circular.
3. **Calcula un umbral** según la maniobra: `0.25` si va recto y `0.75` si gira.
4. **Genera un número pseudoaleatorio**; si es menor que el umbral, ejecuta `setRequest = false` y el vehículo retira **temporalmente** su solicitud de paso para ese cálculo.

En el código aparece:

```cpp
if (blocker.second == *link) {
    const double threshold =
        (*link)->getDirection() == LinkDirection::STRAIGHT ? 0.25 : 0.75;

    if (RandHelper::rand(getRNG()) < threshold) {
        setRequest = false;
    }
}
```

### 4.3. ¿Qué significan el 25 % y el 75 %?

| Maniobra del vehículo evaluado | Probabilidad de **retirar** su solicitud |
|---|---:|
| Continuar recto | **25 %** |
| Girar a izquierda o derecha | **75 %** |

Son **probabilidades de renunciar temporalmente a solicitar el paso**, **no** probabilidades de cruzar primero. Solo se aplican cuando se cumplen las condiciones del mecanismo de detección de bloqueo circular.

**Ejemplo:** A, B, C y D están atrapados en la dependencia circular. Supongamos que todos quieren seguir recto:

- SUMO evalúa **A**. Detecta el círculo, genera `0.68` y lo compara con `0.25`. Como `0.68 > 0.25`, **A mantiene** su solicitud.
- Más adelante evalúa **B** mientras el círculo sigue existiendo. Genera `0.12`; como `0.12 < 0.25`, **B retira** temporalmente su solicitud.
- Al dejar B de reclamar el cruce, **A podría dejar de esperar a B** y encontrar una oportunidad para avanzar. Si A cruza, se abre la posibilidad de que avancen los siguientes.

**Matices importantes:** SUMO **no elige directamente un ganador entre los cuatro** ni está obligado a retirar exactamente una solicitud. Evalúa vehículos individualmente; si el círculo desaparece, los demás pueden dejar de cumplir la condición necesaria para hacer esa comprobación. Retirar la solicitud tampoco garantiza que otro coche avance inmediatamente: siguen importando sus conflictos y el espacio disponible.

### 4.4. Relación con nuestros experimentos

Este mecanismo ayuda a entender por qué algunas situaciones de espera circular pueden desbloquearse sin teletransportación. **No debe confundirse** con `keepClear="true"` (prevención de bloqueo físico del cruce) ni con `--time-to-teleport 300` (reubicación tras determinadas esperas prolongadas).

En las pruebas de 5000 vehículos se registraron **130 teletransportaciones**, pero eso **no demuestra** que cada una fuera provocada por un bloqueo circular ni que este mecanismo se activara para los vehículos concretos observados. Para confirmarlo en un caso individual sería necesario registrar directamente cuándo se ejecuta el bloque de código correspondiente.

## 5. Referencias

- [Script generador de esta red: `mapa_sintetico_v2.py`](./mapa_sintetico_v2.py).
- [Documentación oficial de `randomTrips.py`](https://sumo.dlr.de/docs/Tools/Trip.html).
- [Documentación oficial de intersecciones y `keepClear`](https://sumo.dlr.de/docs/Simulation/Intersections.html).
- [Documentación oficial de retornos (`--no-turnarounds.fringe`)](https://sumo.dlr.de/docs/Simulation/Turnarounds.html).
- [SUMO 1.28.0: detección de bloqueo circular en `MSVehicle.cpp`](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/src/microsim/MSVehicle.cpp#L2999-L3019).
