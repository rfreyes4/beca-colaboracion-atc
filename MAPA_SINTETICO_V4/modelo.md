# Mapa sintético V4 — MICRO con semáforos progresivos

Pruebas realizadas con **SUMO 1.28.0** sobre una red sintética de **7×7 intersecciones**, tramos de **200 m** y **un carril por sentido**. Se comparan el **enrutamiento estático y el dinámico** con semaforización coordinada.

## 1. Semaforización

La red cuenta con **49 semáforos**. Se mantiene el ciclo de **96 segundos** y las reglas de paso; la coordinación progresiva introduce **desfases (`offset`) entre intersecciones**, calculados con `tlsCoordinator.py` a partir de 28 recorridos rectos de referencia y un factor de velocidad `0.9`. Esos recorridos solo se usan para calcular la coordinación, **no sustituyen las rutas de las simulaciones**.

| Fase principal | Duración | Funcionamiento |
|---|---:|---|
| Norte-Sur | 30 s | Recto y derecha con prioridad (`G`); izquierda permitida cediendo el paso (`g`). |
| Izquierda Norte-Sur | 8 s | Izquierda protegida (`G`). |
| Este-Oeste | 30 s | Recto y derecha con prioridad (`G`); izquierda permitida cediendo el paso (`g`). |
| Izquierda Este-Oeste | 8 s | Izquierda protegida (`G`). |

Entre fases: **3 s de amarillo (`y`) y 2 s de rojo general (`r`)**; cuatro transiciones por ciclo. Total: **96 s**.

**Archivos utilizados conjuntamente:** `red_7x7/semaforos.add.xml` (fases y prioridades) y `red_7x7/semaforos_progresivos_rectas.add.xml` (coordinación temporal). Previamente se realizaron pruebas sin coordinación progresiva; sus resultados se conservan aparte y **no se mezclan** con los que aparecen aquí.

## 2. Configuración de las simulaciones MICRO

| Parámetro | Valor usado |
|---|---|
| Red (`-n`) | `red_7x7/red_7x7.net.xml` |
| Rutas (`-r`) | `red_7x7/N_rutas/rutas_N.rou.xml` |
| Semáforos (`-a`) | `red_7x7/semaforos.add.xml,red_7x7/semaforos_progresivos_rectas.add.xml` |
| Intervalo (`--begin`, `--end`) | `0` a `3600` s |
| Semilla (`--seed`) | `42` |
| Teletransporte (`--time-to-teleport`) | `300` s |
| Enrutamiento estático | `--device.rerouting.probability 0` |
| Enrutamiento dinámico | `--device.rerouting.probability 1` y `--device.rerouting.period 120` |
| Resultados completos | `--no-step-log true`, `--duration-log.statistics true`, `--verbose true` |
| Medición limpia | Misma simulación, suprimiendo la salida para medir `real`, `user` y `sys` |

Los archivos de demanda proceden de **RandomTrips** (semilla 42, salidas aleatorias entre 0 y 3600 s); demandas nominales de 3000, 4000, 5000, 6000, 7000, 8000, 9000 y 11 000. Se reutilizan las mismas rutas de entrada en ambos enrutamientos.

## 3. Resultados MICRO con semáforos progresivos

### 3.1. Vehículos y bloqueos

| Tipo | Demanda | Cargados | Insertados | Finalizados | Circulando | Pendientes | Teleports (Jam / Yield) | Frenadas emergencia |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Estático | 3000 | 3001 | 2946 | **2649** | 297 | 55 | 0 (0 / 0) | 1 |
| Estático | 4000 | 4000 | 3853 | **3464** | 389 | 147 | 0 (0 / 0) | 0 |
| Estático | 5000 | 5001 | 4614 | **4070** | 544 | 387 | 0 (0 / 0) | 0 |
| Estático | 6000 | 6001 | 5186 | **4403** | 783 | 815 | 6 (2 / 4) | 0 |
| Estático | 7000 | 7000 | 5596 | **4419** | 1177 | 1404 | 46 (14 / 32) | 0 |
| Estático | 8000 | 8001 | 5731 | **3804** | 1927 | 2270 | 128 (44 / 84) | 0 |
| Estático | 9000 | 9000 | 6063 | **4068** | 1995 | 2937 | 129 (41 / 88) | 0 |
| Estático | 11000 | 11000 | 6132 | **3722** | 2410 | 4866 | 249 (74 / 175) | 0 |
| Dinámico | 3000 | 3001 | 2956 | **2664** | 292 | 45 | 0 (0 / 0) | 0 |
| Dinámico | 4000 | 4000 | 3907 | **3473** | 434 | 93 | 0 (0 / 0) | 1 |
| Dinámico | 5000 | 5001 | 4753 | **4132** | 621 | 248 | 0 (0 / 0) | 0 |
| Dinámico | 6000 | 6001 | 5437 | **4483** | 954 | 564 | 0 (0 / 0) | 0 |
| Dinámico | 7000 | 7000 | 5683 | **4402** | 1281 | 1317 | 0 (0 / 0) | 4 |
| Dinámico | 8000 | 8001 | 5869 | **4267** | 1602 | 2132 | 0 (0 / 0) | 0 |
| Dinámico | 9000 | 9000 | 6010 | **4293** | 1717 | 2990 | 0 (0 / 0) | 0 |
| Dinámico | 11000 | 11000 | 5815 | **3691** | 2124 | 5183 | 2 (0 / 2) | 0 |

**Finalizados = insertados − circulando**. «Pendientes» son vehículos que no han entrado en la red cuando termina la simulación; no debe confundirse con el tiempo de espera durante un viaje.

### 3.2. Medias de los viajes finalizados

| Tipo | Demanda | RouteLength (m) | Speed (m/s) | Duration (s) | WaitingTime (s) | TimeLoss (s) | DepartDelay (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Estático | 3000 | 1524,68 | 5,32 | 311,72 | 155,76 | 200,28 | 57,58 |
| Estático | 4000 | 1525,62 | 5,09 | 324,83 | 163,50 | 213,46 | 81,10 |
| Estático | 5000 | 1526,05 | 4,67 | 361,38 | 190,95 | 249,89 | 103,88 |
| Estático | 6000 | 1524,68 | 4,32 | 405,38 | 225,16 | 293,97 | 130,82 |
| Estático | 7000 | 1510,54 | 4,00 | 455,93 | 269,46 | 345,15 | 147,72 |
| Estático | 8000 | 1504,84 | 3,97 | 481,11 | 295,87 | 369,55 | 174,25 |
| Estático | 9000 | 1500,31 | 3,78 | 488,60 | 295,73 | 377,21 | 183,81 |
| Estático | 11000 | 1490,23 | 3,42 | 565,29 | 362,24 | 453,11 | 178,29 |
| Dinámico | 3000 | 1547,00 | 5,19 | 319,56 | 156,44 | 206,48 | 48,30 |
| Dinámico | 4000 | 1566,97 | 4,75 | 354,75 | 179,38 | 240,30 | 69,73 |
| Dinámico | 5000 | 1582,85 | 4,35 | 399,70 | 211,09 | 283,96 | 106,74 |
| Dinámico | 6000 | 1639,69 | 3,79 | 486,78 | 272,92 | 366,99 | 141,84 |
| Dinámico | 7000 | 1703,31 | 3,39 | 583,86 | 344,52 | 459,44 | 175,85 |
| Dinámico | 8000 | 1723,14 | 3,23 | 642,09 | 390,64 | 516,27 | 190,94 |
| Dinámico | 9000 | 1718,92 | 3,05 | 680,88 | 423,16 | 555,21 | 202,62 |
| Dinámico | 11000 | 1761,63 | 2,73 | 818,36 | 537,06 | 689,54 | 196,08 |

`Duration` es el tiempo de viaje; `WaitingTime`, el tiempo parado o casi parado; `TimeLoss`, el tiempo perdido frente a condiciones de referencia; y `DepartDelay`, el retraso de inserción. **Todas las medias corresponden a vehículos que finalizaron**, por lo que deben interpretarse junto con el número de finalizados.

### 3.3. Rendimiento computacional

| Tipo | Demanda | Performance Duration (s) | `real` completo (s) | `real` limpio (s) | `user` limpio (s) | `sys` limpio (s) | Dijkstra: consultas / tiempo (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Estático | 3000 | 1,45 | 1,52 | **1,49** | 1,46 | 0,02 | — |
| Estático | 4000 | 2,32 | 2,39 | **2,10** | 2,07 | 0,02 | — |
| Estático | 5000 | 3,69 | 3,76 | **3,55** | 3,52 | 0,02 | — |
| Estático | 6000 | 6,48 | 6,56 | **6,08** | 6,04 | 0,03 | — |
| Estático | 7000 | 9,63 | 9,71 | **8,86** | 8,81 | 0,03 | — |
| Estático | 8000 | 13,15 | 13,24 | **11,88** | 11,82 | 0,05 | — |
| Estático | 9000 | 14,44 | 14,53 | **13,33** | 13,28 | 0,03 | — |
| Estático | 11000 | 20,19 | 20,29 | **18,97** | 18,91 | 0,04 | — |
| Dinámico | 3000 | 2,18 | 2,25 | **2,58** | 2,56 | 0,02 | 9207 / 0,11 |
| Dinámico | 4000 | 4,77 | 4,87 | **4,15** | 4,11 | 0,03 | 13547 / 0,21 |
| Dinámico | 5000 | 5,54 | 5,62 | **5,10** | 5,08 | 0,02 | 18430 / 0,24 |
| Dinámico | 6000 | 9,11 | 9,19 | **8,98** | 8,93 | 0,03 | 25198 / 0,30 |
| Dinámico | 7000 | 13,50 | 13,59 | **12,97** | 12,93 | 0,03 | 31930 / 0,38 |
| Dinámico | 8000 | 17,85 | 17,95 | **17,17** | 17,12 | 0,04 | 37666 / 0,47 |
| Dinámico | 9000 | 20,96 | 21,06 | **20,24** | 20,19 | 0,04 | 41875 / 0,56 |
| Dinámico | 11000 | 28,84 | 28,96 | **28,23** | 28,13 | 0,06 | 51149 / 0,71 |

La ejecución **completa** muestra estadísticas y avisos. La medición **limpia** se ejecuta con la salida suprimida; no cambia las reglas de circulación. Los valores `real` son tiempos de reloj y pueden variar entre ejecuciones.

## 4. Comparación general

| Demanda | Finalizados estático | Finalizados dinámico | Teleports estático | Teleports dinámico | Limpio estático (s) | Limpio dinámico (s) |
|---|---:|---:|---:|---:|---:|---:|
| 3000 | 2649 | 2664 | 0 | 0 | 1,49 | 2,58 |
| 4000 | 3464 | 3473 | 0 | 0 | 2,10 | 4,15 |
| 5000 | 4070 | 4132 | 0 | 0 | 3,55 | 5,10 |
| 6000 | 4403 | 4483 | 6 | 0 | 6,08 | 8,98 |
| 7000 | 4419 | 4402 | 46 | 0 | 8,86 | 12,97 |
| 8000 | 3804 | 4267 | 128 | 0 | 11,88 | 17,17 |
| 9000 | 4068 | 4293 | 129 | 0 | 13,33 | 20,24 |
| 11000 | 3722 | 3691 | 249 | 2 | 18,97 | 28,23 |

### Observaciones

1. **Hasta 5000 vehículos** no se registran teletransportes y los dos enrutamientos completan un número similar de viajes.
2. **Desde 6000 vehículos**, el enrutamiento estático presenta teletransportes que aumentan con la demanda (hasta **249** con 11 000), mientras que el dinámico registra **0** hasta 9000 y **2** con 11 000.
3. El **dinámico** finaliza más viajes en **6 de las 8 demandas**; sin embargo, suele recorrer más distancia y presenta mayores tiempos medios de viaje.
4. La ejecución **estática es más rápida** computacionalmente en todas las demandas. Con 11 000 vehículos: **18,97 s** frente a **28,23 s** en la medición limpia.

**Conclusión:** con semáforos progresivos, el reenrutamiento dinámico reduce notablemente los teletransportes, pero no reduce los tiempos medios de viaje. Para la posterior comparación MICRO–MESO se tomará como referencia principal **MICRO estático con estos mismos semáforos progresivos**.

## Referencias

- [SUMO — Traffic Lights](https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html)
- [SUMO — Statistics](https://sumo.dlr.de/docs/Simulation/Output/StatisticOutput.html)
- [SUMO — Vehicle Insertion](https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html)
