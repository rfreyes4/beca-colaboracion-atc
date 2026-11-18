# Mapa sintético V4 — Red 7×7 con semáforos

Notas de las pruebas realizadas con **SUMO 1.28.0** sobre una red sintética de 7×7 intersecciones, con tramos de 200 m y un carril por sentido. Se compara la **simulación microscópica con rutas estáticas** frente al **reenrutamiento dinámico**.

## 1. Semaforización

La red 7×7 cuenta con 49 intersecciones reguladas por semáforos.
Cada semáforo utiliza un ciclo de 96 segundos, dividido en
cuatro fases principales y sus correspondientes transiciones.

### Funcionamiento

Durante el verde principal, los vehículos pueden circular
recto o girar a la derecha con prioridad.

También pueden girar a la izquierda, pero deben ceder el
paso a los vehículos que circulan de frente.

Después se activa una fase exclusiva para girar a la
izquierda, en la que estos vehículos tienen prioridad.

### Fases del semáforo

| Fase | Duración | Funcionamiento |
|---|---|---|
| 1. Norte-Sur | 30 s | Recto y derecha con prioridad. Izquierda permitida cediendo el paso. |
| 2. Izquierda Norte-Sur | 8 s | Giro a la izquierda con prioridad. |
| 3. Este-Oeste | 30 s | Recto y derecha con prioridad. Izquierda permitida cediendo el paso. |
| 4. Izquierda Este-Oeste | 8 s | Giro a la izquierda con prioridad. |

Entre cada fase se utilizan:
- Amarillo: 3 segundos.
- Rojo general: 2 segundos.

**Duración total del ciclo: 96 segundos.**

### Estados utilizados en SUMO

- `G` (verde): circulación permitida con prioridad.
- `g` (verde permisivo): circulación permitida, pero cediendo el paso.
- `y` (amarillo): transición antes del rojo.
- `r` (rojo): circulación prohibida.

El estado `g` permite que los vehículos giren a la izquierda
mientras otros circulan recto, siempre que exista un hueco
seguro para realizar el giro.

## 2. Simulación microscópica

La simulación microscópica representa el movimiento individual de cada vehículo, sus frenadas, esperas, cruces y posibles bloqueos. **Las dos modalidades utilizan la misma red, los mismos semáforos y el mismo fichero de rutas inicial para cada demanda.**

### Configuración utilizada

| Parámetro | Valor | Explicación |
|---|---|---|
| Red (`-n`) | `red_7x7/red_7x7.net.xml` | Red de calles por la que circulan los vehículos. |
| Rutas (`-r`) | `red_7x7/N_rutas/rutas_N.rou.xml` | Demanda `N` generada previamente con RandomTrips. |
| Semáforos (`-a`) | `red_7x7/semaforos.add.xml` | Carga el programa semafórico descrito arriba. |
| `--begin` / `--end` | `0` / `3600` | Se simula una hora; al llegar al segundo 3600 se detiene aunque queden vehículos por terminar. |
| `--seed` | `42` | Fija la semilla aleatoria de SUMO para facilitar la reproducción. |
| `--time-to-teleport` | `300` s | SUMO puede recolocar un vehículo tras un bloqueo prolongado de 300 s. |
| `--no-step-log` | `true` | Oculta el progreso de cada paso para reducir texto en la terminal. |
| `--duration-log.statistics` | `true` en prueba completa | Muestra promedios de recorrido, velocidad, duración y esperas al finalizar. |
| `--verbose` | `true` en prueba completa | Muestra información adicional de carga y rendimiento. |

Los ficheros de demanda se generaron con **RandomTrips**, semilla 42, entre los segundos 0 y 3600, con salidas aleatorias. El parámetro `-p` representa el intervalo medio entre vehículos solicitados: su valor disminuye cuando aumenta la demanda.

| Demanda nominal | `-p` (s) | Vehículos cargados en estas pruebas |
|---|---:|---:|
| 3000 | 1.2 | 3001 |
| 4000 | 0.9 | 4000 |
| 5000 | 0.72 | 5001 |
| 6000 | 0.6 | 6001 |
| 7000 | 0.514286 | 7000 |
| 8000 | 0.45 | 8001 |
| 9000 | 0.4 | 9000 |
| 11000 | 0.327273 | 11000 |

### Enrutamiento estático frente a dinámico

| Modalidad | Parámetros utilizados | Funcionamiento |
|---|---|---|
| **Estático** | `--device.rerouting.probability 0` | El vehículo sigue la ruta calculada inicialmente, sin recalcularla periódicamente durante el recorrido. |
| **Dinámico** | `--device.rerouting.probability 1` y `--device.rerouting.period 120` | Todos los vehículos reciben el dispositivo de reenrutamiento y pueden recalcular su ruta cada 120 segundos según los costes estimados de las vías. |

**Importante:** el enrutamiento dinámico **no garantiza una mejora**. Si muchos conductores escogen caminos alternativos, pueden hacer recorridos más largos y desplazar la congestión a otras calles.

### Qué significa cada resultado

| Métrica | Significado |
|---|---|
| **Loaded** | Vehículos definidos/cargados por la demanda. |
| **Inserted** | Vehículos que han logrado entrar físicamente en la red antes del segundo 3600. |
| **Finished** | Vehículos que han llegado a su destino antes del final de la simulación. En estos resultados equivale a `Inserted − Running`. |
| **Running** | Vehículos que seguían circulando al terminar la hora simulada. |
| **Waiting** | Vehículos aún **pendientes de entrar** en la red al final por falta de espacio. No equivale a `WaitingTime`. |
| **Teleports** | Recolocaciones para resolver bloqueos; **Jam** indica atasco y **Yield** dificultades prolongadas al ceder el paso. |
| **Emergency Braking** | Frenadas de emergencia detectadas durante la simulación. |
| **RouteLength** | Longitud media del trayecto de los vehículos incluidos en las estadísticas, en metros. |
| **Speed** | Velocidad media durante el viaje, en m/s. Para pasar a km/h se multiplica por 3,6. |
| **Duration** | Tiempo medio transcurrido desde que un vehículo entra hasta que acaba su recorrido. |
| **WaitingTime** | Tiempo medio que un vehículo permanece parado o casi parado durante su viaje. |
| **TimeLoss** | Tiempo medio perdido respecto a la circulación de referencia sin esas demoras. |
| **DepartDelay** | Retraso medio entre la salida prevista y la entrada efectiva en la red. |
| **Statistics (avg of …)** | Número de recorridos finalizados sobre los que se calculan las medias anteriores. |
| **Performance Duration** | Tiempo de cálculo informado por SUMO, en segundos; no es la duración de los viajes. |
| **`real` completo** | Tiempo de reloj de `time -p` cuando se muestran avisos y estadísticas. |
| **`real` limpio** | Tiempo de reloj con la salida suprimida mediante `> /dev/null 2>&1`. «Limpio» se refiere a la **salida de terminal**, no a una red sin tráfico. |
| **`user` / `sys`** | Tiempo de CPU ejecutando el programa / trabajando en el núcleo del sistema operativo. |
| **Dijkstra (consultas)** | Cantidad de búsquedas de rutas registradas al utilizar el reenrutamiento dinámico. |

En cada apartado se muestran **las mediciones completas** y, al final, **el tiempo limpio**. Los valores de velocidad, duración, espera y recorrido son promedios de los vehículos que finalizaron, no de los que permanecían dentro o esperando para entrar.

### 2.1. Demanda de 3000 vehículos

| Métrica | Estático | Dinámico |
|---|---:|---:|
| Cargados (Loaded) | 3001 | 3001 |
| Insertados | 2960 | 2964 |
| Finalizados | 2692 | 2702 |
| Circulando al finalizar | 268 | 262 |
| Pendientes de entrar | 41 | 37 |
| Teleports (Jam / Yield) | 0 (0 / 0) | 0 (0 / 0) |
| Frenadas de emergencia | 1 | 0 |
| Longitud media (m) | 1525.43 | 1538.72 |
| Velocidad media (m/s) | 5.60 | 5.63 |
| Duración media (s) | 283.28 | 284.48 |
| WaitingTime (s) | 134.65 | 130.69 |
| TimeLoss (s) | 171.90 | 172.08 |
| DepartDelay (s) | 37.22 | 26.27 |
| Performance Duration (s) | 1.27 | 1.51 |
| **Tiempo completo `real` (s)** | **1.34** | **1.58** |
| **Tiempo limpio `real` (s)** | **1.24** | **1.54** |
| Consultas Dijkstra | — | 8171 |
| Tiempo Dijkstra (s) | — | 0.09 |

### 2.2. Demanda de 4000 vehículos

| Métrica | Estático | Dinámico |
|---|---:|---:|
| Cargados (Loaded) | 4000 | 4000 |
| Insertados | 3869 | 3932 |
| Finalizados | 3498 | 3496 |
| Circulando al finalizar | 371 | 436 |
| Pendientes de entrar | 131 | 68 |
| Teleports (Jam / Yield) | 0 (0 / 0) | 0 (0 / 0) |
| Frenadas de emergencia | 0 | 1 |
| Longitud media (m) | 1523.20 | 1557.31 |
| Velocidad media (m/s) | 5.24 | 5.04 |
| Duración media (s) | 304.75 | 326.96 |
| WaitingTime (s) | 150.35 | 160.25 |
| TimeLoss (s) | 193.44 | 213.22 |
| DepartDelay (s) | 65.00 | 45.92 |
| Performance Duration (s) | 1.96 | 2.55 |
| **Tiempo completo `real` (s)** | **2.03** | **2.62** |
| **Tiempo limpio `real` (s)** | **1.92** | **2.72** |
| Consultas Dijkstra | — | 12502 |
| Tiempo Dijkstra (s) | — | 0.11 |

### 2.3. Demanda de 5000 vehículos

| Métrica | Estático | Dinámico |
|---|---:|---:|
| Cargados (Loaded) | 5001 | 5001 |
| Insertados | 4693 | 4824 |
| Finalizados | 4203 | 4229 |
| Circulando al finalizar | 490 | 595 |
| Pendientes de entrar | 308 | 177 |
| Teleports (Jam / Yield) | 0 (0 / 0) | 0 (0 / 0) |
| Frenadas de emergencia | 0 | 0 |
| Longitud media (m) | 1520.67 | 1590.64 |
| Velocidad media (m/s) | 4.77 | 4.38 |
| Duración media (s) | 344.73 | 396.07 |
| WaitingTime (s) | 180.15 | 209.85 |
| TimeLoss (s) | 233.54 | 279.83 |
| DepartDelay (s) | 81.78 | 74.02 |
| Performance Duration (s) | 3.58 | 4.90 |
| **Tiempo completo `real` (s)** | **3.65** | **4.97** |
| **Tiempo limpio `real` (s)** | **3.08** | **4.78** |
| Consultas Dijkstra | — | 18446 |
| Tiempo Dijkstra (s) | — | 0.20 |

### 2.4. Demanda de 6000 vehículos

| Métrica | Estático | Dinámico |
|---|---:|---:|
| Cargados (Loaded) | 6001 | 6001 |
| Insertados | 5316 | 5513 |
| Finalizados | 4578 | 4416 |
| Circulando al finalizar | 738 | 1097 |
| Pendientes de entrar | 685 | 488 |
| Teleports (Jam / Yield) | 5 (0 / 5) | 0 (0 / 0) |
| Frenadas de emergencia | 0 | 0 |
| Longitud media (m) | 1516.61 | 1652.15 |
| Velocidad media (m/s) | 4.43 | 3.72 |
| Duración media (s) | 385.89 | 506.83 |
| WaitingTime (s) | 213.04 | 291.95 |
| TimeLoss (s) | 275.06 | 386.14 |
| DepartDelay (s) | 112.95 | 121.72 |
| Performance Duration (s) | 6.13 | 9.46 |
| **Tiempo completo `real` (s)** | **6.21** | **9.53** |
| **Tiempo limpio `real` (s)** | **5.31** | **9.10** |
| Consultas Dijkstra | — | 26581 |
| Tiempo Dijkstra (s) | — | 0.31 |

### 2.5. Demanda de 7000 vehículos

| Métrica | Estático | Dinámico |
|---|---:|---:|
| Cargados (Loaded) | 7000 | 7000 |
| Insertados | 5737 | 5787 |
| Finalizados | 4635 | 4296 |
| Circulando al finalizar | 1102 | 1491 |
| Pendientes de entrar | 1263 | 1213 |
| Teleports (Jam / Yield) | 31 (8 / 23) | 0 (0 / 0) |
| Frenadas de emergencia | 1 | 0 |
| Longitud media (m) | 1517.14 | 1703.51 |
| Velocidad media (m/s) | 4.15 | 3.32 |
| Duración media (s) | 427.75 | 607.14 |
| WaitingTime (s) | 247.00 | 366.24 |
| TimeLoss (s) | 316.41 | 482.71 |
| DepartDelay (s) | 139.93 | 144.48 |
| Performance Duration (s) | 8.67 | 14.18 |
| **Tiempo completo `real` (s)** | **8.75** | **14.26** |
| **Tiempo limpio `real` (s)** | **7.70** | **14.92** |
| Consultas Dijkstra | — | 34505 |
| Tiempo Dijkstra (s) | — | 0.38 |

### 2.6. Demanda de 8000 vehículos

| Métrica | Estático | Dinámico |
|---|---:|---:|
| Cargados (Loaded) | 8001 | 8001 |
| Insertados | 5869 | 5849 |
| Finalizados | 4020 | 4043 |
| Circulando al finalizar | 1849 | 1806 |
| Pendientes de entrar | 2132 | 2152 |
| Teleports (Jam / Yield) | 122 (37 / 85) | 0 (0 / 0) |
| Frenadas de emergencia | 0 | 0 |
| Longitud media (m) | 1505.90 | 1738.70 |
| Velocidad media (m/s) | 3.92 | 3.10 |
| Duración media (s) | 477.40 | 685.36 |
| WaitingTime (s) | 293.28 | 428.71 |
| TimeLoss (s) | 365.48 | 558.33 |
| DepartDelay (s) | 163.78 | 172.20 |
| Performance Duration (s) | 12.61 | 18.60 |
| **Tiempo completo `real` (s)** | **12.70** | **18.69** |
| **Tiempo limpio `real` (s)** | **12.97** | **18.01** |
| Consultas Dijkstra | — | 40601 |
| Tiempo Dijkstra (s) | — | 0.54 |

### 2.7. Demanda de 9000 vehículos

| Métrica | Estático | Dinámico |
|---|---:|---:|
| Cargados (Loaded) | 9000 | 9000 |
| Insertados | 6252 | 5799 |
| Finalizados | 4327 | 3749 |
| Circulando al finalizar | 1925 | 2050 |
| Pendientes de entrar | 2748 | 3201 |
| Teleports (Jam / Yield) | 136 (34 / 102) | 1 (0 / 1) |
| Frenadas de emergencia | 0 | 2 |
| Longitud media (m) | 1496.63 | 1731.15 |
| Velocidad media (m/s) | 3.85 | 2.94 |
| Duración media (s) | 464.50 | 737.18 |
| WaitingTime (s) | 277.56 | 474.41 |
| TimeLoss (s) | 353.71 | 610.63 |
| DepartDelay (s) | 161.84 | 168.08 |
| Performance Duration (s) | 13.91 | 23.15 |
| **Tiempo completo `real` (s)** | **14.00** | **23.25** |
| **Tiempo limpio `real` (s)** | **13.23** | **21.85** |
| Consultas Dijkstra | — | 46736 |
| Tiempo Dijkstra (s) | — | 0.61 |

### 2.8. Demanda de 11 000 vehículos

| Métrica | Estático | Dinámico |
|---|---:|---:|
| Cargados (Loaded) | 11000 | 11000 |
| Insertados | 6449 | 6051 |
| Finalizados | 4188 | 3913 |
| Circulando al finalizar | 2261 | 2138 |
| Pendientes de entrar | 4549 | 4947 |
| Teleports (Jam / Yield) | 184 (56 / 128) | 1 (1 / 0) |
| Frenadas de emergencia | 0 | 0 |
| Longitud media (m) | 1497.77 | 1753.09 |
| Velocidad media (m/s) | 3.37 | 2.67 |
| Duración media (s) | 570.01 | 816.31 |
| WaitingTime (s) | 369.90 | 534.56 |
| TimeLoss (s) | 458.73 | 688.18 |
| DepartDelay (s) | 211.75 | 207.14 |
| Performance Duration (s) | 21.81 | 28.75 |
| **Tiempo completo `real` (s)** | **21.92** | **28.87** |
| **Tiempo limpio `real` (s)** | **18.90** | **27.91** |
| Consultas Dijkstra | — | 52142 |
| Tiempo Dijkstra (s) | — | 0.70 |

## 3. Comparación general de los tiempos y el tráfico

| Demanda | Finalizados estático | Finalizados dinámico | Teleports estático | Teleports dinámico | Limpio estático (s) | Limpio dinámico (s) |
|---|---:|---:|---:|---:|---:|---:|
| 3000 | 2692 | 2702 | 0 | 0 | 1.24 | 1.54 |
| 4000 | 3498 | 3496 | 0 | 0 | 1.92 | 2.72 |
| 5000 | 4203 | 4229 | 0 | 0 | 3.08 | 4.78 |
| 6000 | 4578 | 4416 | 5 | 0 | 5.31 | 9.10 |
| 7000 | 4635 | 4296 | 31 | 0 | 7.70 | 14.92 |
| 8000 | 4020 | 4043 | 122 | 0 | 12.97 | 18.01 |
| 9000 | 4327 | 3749 | 136 | 1 | 13.23 | 21.85 |
| 11000 | 4188 | 3913 | 184 | 1 | 18.90 | 27.91 |

### Observaciones de las pruebas

1. **Hasta 5000 vehículos** no aparecen teleports en ninguna modalidad. Los resultados de viajes finalizados son próximos, aunque el enrutamiento dinámico consume más tiempo de cálculo.
2. **Desde 6000 vehículos** la red empieza a mostrar bloqueos prolongados en el modo estático, y la demanda pendiente de inserción aumenta claramente. El dinámico reduce casi por completo los teleports, pero eso **no significa que haga llegar antes a los vehículos**.
3. **Con 7000–11 000 vehículos** el dinámico suele recorrer más distancia y registrar mayores `Duration`, `WaitingTime` y `TimeLoss`. En estos ensayos, la posibilidad de cambiar de ruta no compensa la congestión y el mayor recorrido.
4. **Con 11 000 vehículos**, de los 11 000 cargados terminaron **4188 en estático y 3913 en dinámico**. Permanecían pendientes de insertarse **4549 y 4947**, respectivamente: la red está claramente saturada a los 3600 s.
5. Los tiempos `real` corresponden **a la ejecución del programa en el ordenador**, no a los segundos simulados ni al tiempo medio de un trayecto. Son mediciones individuales y pueden variar ligeramente por la carga del equipo.

**Cautela al interpretar las medias:** las estadísticas se refieren a los viajes que terminaron antes de los 3600 s. Cuando la red está muy saturada, quedan fuera muchos vehículos lentos que seguían circulando o que todavía no pudieron entrar, por lo que una menor duración media **no implica necesariamente una mejora general**.

### Referencias breves

- [SUMO — Traffic Lights](https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html): estados `G`, `g`, `y` y `r` y reglas de prioridad.
- [SUMO — Statistics](https://sumo.dlr.de/docs/Simulation/Output/StatisticOutput.html): significado de las estadísticas de vehículos.
- [SUMO — Vehicle Insertion](https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html): cola de inserción y retrasos de salida.
