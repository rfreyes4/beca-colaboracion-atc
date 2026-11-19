# Mapa sintético V4 — MICRO y MESO con semáforos progresivos

Se ha utilizado **SUMO 1.28.0** con una red de **7×7 intersecciones**, calles de **200 m** y **un carril por sentido**. En MICRO se han probado rutas estáticas y dinámicas. En MESO se han realizado cuatro pruebas, todas con rutas estáticas. En ambos casos se usan los mismos semáforos progresivos.

## 1. Semaforización

La red tiene **49 semáforos**, con ciclos de **96 segundos**. Los semáforos progresivos mantienen las mismas fases, pero cada cruce tiene un desfase (`offset`) para coordinar los verdes. Los desfases se calcularon con `tlsCoordinator.py`, usando 28 recorridos rectos de referencia y un factor de velocidad de `0.9`. Esos recorridos solo sirven para calcular la coordinación; las rutas de los vehículos no cambian.

| Fase principal | Duración | Funcionamiento |
|---|---:|---|
| Norte-Sur | 30 s | Recto y derecha con prioridad (`G`); izquierda permitida cediendo el paso (`g`). |
| Izquierda Norte-Sur | 8 s | Izquierda protegida (`G`). |
| Este-Oeste | 30 s | Recto y derecha con prioridad (`G`); izquierda permitida cediendo el paso (`g`). |
| Izquierda Este-Oeste | 8 s | Izquierda protegida (`G`). |

Cada cambio de fase incluye **3 s de amarillo (`y`) y 2 s de rojo general (`r`)**. Hay cuatro cambios por ciclo, por lo que el total es **96 s**.

Se cargan dos archivos: `red_7x7/semaforos.add.xml` (fases y prioridades) y `red_7x7/semaforos_progresivos_rectas.add.xml` (desfases). Las pruebas anteriores, sin coordinación progresiva, están guardadas aparte.

## 2. Configuración de las simulaciones MICRO

| Parámetro | Valor usado | Qué significa |
|---|---|---|
| Red (`-n`) | `red_7x7/red_7x7.net.xml` | Define las calles, carriles e intersecciones. |
| Rutas (`-r`) | `red_7x7/N_rutas/rutas_N.rou.xml` | Indica qué vehículos salen y qué recorrido siguen. `N` es la demanda. |
| Semáforos (`-a`) | `red_7x7/semaforos.add.xml,red_7x7/semaforos_progresivos_rectas.add.xml` | Aplica las fases y los desfases progresivos. |
| Intervalo (`--begin`, `--end`) | `0` a `3600` s | Simula una hora y se detiene en el segundo 3600, aunque queden coches en la red. |
| Semilla (`--seed`) | `42` | Permite repetir la simulación con la misma aleatoriedad. |
| Teletransporte (`--time-to-teleport`) | `300` s | SUMO puede desplazar un vehículo si permanece bloqueado demasiado tiempo. |
| Enrutamiento estático | `--device.rerouting.probability 0` | Los vehículos siguen la ruta asignada al principio. |
| Enrutamiento dinámico | `--device.rerouting.probability 1` y `--device.rerouting.period 120` | Todos tienen la opción de recalcular su ruta cada 120 s según el tráfico. |
| Resultados completos | `--no-step-log true`, `--duration-log.statistics true`, `--verbose true` | Oculta el progreso paso a paso y muestra estadísticas e información de la ejecución. |
| Medición limpia | Misma configuración, con la salida oculta | Mide los tiempos `real`, `user` y `sys` sin imprimir los mensajes de SUMO. |

Las rutas se generaron con **RandomTrips** (semilla 42 y salidas entre 0 y 3600 s). Se probaron demandas de **3000, 4000, 5000, 6000, 7000, 8000, 9000 y 11 000 vehículos**. MICRO estático y dinámico utilizan los mismos archivos de rutas.

### 2.1. Significado de los resultados (MICRO y MESO)

Estas medidas aparecen en los resultados de ambos modelos. Las cantidades indican vehículos y los tiempos se expresan en segundos.

| Medida | Significado |
|---|---|
| **Cargados (`Loaded`)** | Vehículos que SUMO ha leído del archivo de rutas para la simulación. |
| **Insertados (`Inserted`)** | Vehículos que han conseguido entrar en la red de carreteras. |
| **Circulando (`Running`)** | Vehículos que permanecen dentro de la red cuando termina la simulación, aunque estén parados en una cola. |
| **Pendientes (`Waiting`)** | Vehículos que aún esperan para incorporarse a la red. Es una **cantidad de vehículos**, no un tiempo. |
| **Finalizados** | Vehículos que ya no están circulando al terminar: **insertados − circulando**. Puede incluir vehículos retirados de la simulación. |
| **Distancia (`RouteLength`)** | Metros recorridos por un vehículo durante su viaje. |
| **Velocidad (`Speed`)** | Velocidad media del viaje, en metros por segundo (m/s). |
| **Duración (`Duration`)** | Tiempo desde que el vehículo **entra en la red hasta que llega a su destino**. Incluye los semáforos, las colas y el tiempo en movimiento. |
| **Espera (`WaitingTime`)** | Segundos que el vehículo pasa **parado o casi parado dentro de la red** (velocidad de hasta 0,1 m/s), por ejemplo ante un semáforo. No cuenta las paradas programadas. |
| **Tiempo perdido (`TimeLoss`)** | Segundos adicionales que tarda el viaje respecto a circular a la velocidad ideal. Incluye las paradas y los retrasos por ir más despacio. **Ya incluye `WaitingTime`.** |
| **Retraso de salida (`DepartDelay`)** | Segundos entre la hora en que el vehículo **debía salir** y el momento en que **consigue entrar en la red**. |
| **Teletransportes (`Teleports`)** | Veces que SUMO desplaza un vehículo para resolver una situación de bloqueo prolongado. En los resultados se distinguen causas como `Jam` (atasco) y `Yield` (problemas para ceder el paso). |
| **Frenadas de emergencia** | Número de frenadas muy bruscas detectadas durante la simulación MICRO. |

**Ejemplo:** un coche debe salir en el segundo 100, entra en el 120 y llega en el 320. Su `DepartDelay` es **20 s** y su `Duration` es **200 s**. Si pasó 40 s parado y perdió 60 s frente al viaje ideal, su `WaitingTime` es **40 s** y su `TimeLoss` es **60 s**. Los 40 s de espera ya están dentro de los 60 s perdidos; no se suman.

Las medias corresponden a los viajes finalizados. Cuando hay congestión, también hay que mirar cuántos coches quedan circulando o pendientes al terminar la hora de simulación.

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

**Finalizados = insertados − circulando.** Los pendientes todavía no han entrado en la red. Las medidas se explican en el apartado 2.1.

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

Las medias se refieren a los viajes finalizados. Su significado se explica en el apartado 2.1.

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

La ejecución **completa** muestra las estadísticas de SUMO. En la **limpia** se ocultan los mensajes para medir el rendimiento, sin cambiar la simulación. `Performance Duration` es el tiempo de ejecución que informa SUMO; `real` es el tiempo de reloj, `user` es el tiempo de CPU del programa y `sys` el tiempo de CPU del sistema operativo. `Dijkstra` muestra cuántas búsquedas de ruta se hicieron y cuánto tiempo emplearon. Son tiempos del ordenador, no de los coches, y pueden variar ligeramente entre ejecuciones.

## 4. Comparación general

| Demanda | Finalizados estático | Finalizados dinámico | Teleports estático | Teleports dinámico | Limpio estático (s) | Limpio dinámico (s) |
|---|---:|---:|---:|---:|---:|
| 3000 | 2649 | 2664 | 0 | 0 | 1,49 | 2,58 |
| 4000 | 3464 | 3473 | 0 | 0 | 2,10 | 4,15 |
| 5000 | 4070 | 4132 | 0 | 0 | 3,55 | 5,10 |
| 6000 | 4403 | 4483 | 6 | 0 | 6,08 | 8,98 |
| 7000 | 4419 | 4402 | 46 | 0 | 8,86 | 12,97 |
| 8000 | 3804 | 4267 | 128 | 0 | 11,88 | 17,17 |
| 9000 | 4068 | 4293 | 129 | 0 | 13,33 | 20,24 |
| 11000 | 3722 | 3691 | 249 | 2 | 18,97 | 28,23 |

### Observaciones

1. Hasta **5000 vehículos**, los resultados son parecidos y no hay teletransportes.
2. A partir de **6000**, el estático empieza a registrar teletransportes y llega a **249** con 11 000 vehículos. El dinámico solo registra **2** en esa demanda.
3. El dinámico completa más viajes en **6 de las 8 demandas**, pero sus recorridos y tiempos medios suelen ser mayores.
4. El estático tarda menos en ejecutarse. Con 11 000 vehículos, el tiempo limpio es de **18,97 s**, frente a **28,23 s** del dinámico.

**Conclusión:** el enrutamiento dinámico reduce los teletransportes, pero los viajes no son más rápidos. Para comparar con MESO se utiliza como referencia **MICRO estático con semáforos progresivos**.

## 5. Simulación MESO con semáforos progresivos

Se hicieron **cuatro pruebas MESO** con la misma red, rutas y semáforos progresivos que en MICRO. Todas utilizan **enrutamiento estático**, para poder compararlas con MICRO estático.

### 5.1. Configuración de las cuatro pruebas

Se compara el MESO convencional con distintos tamaños de segmento y el modelo alternativo **LTM**. El parámetro `--meso-edgelength` solo divide las carreteras en segmentos internos: **las calles siguen midiendo 200 m**.

| Prueba | Modelo | `--meso-ltm` | `--meso-edgelength` | Segmentos por tramo de 200 m |
|---|---|---|---:|---:|
| **1** | MESO convencional | `false` | `200` | 1 |
| **2** | MESO convencional | `false` | `100` | 2 |
| **3** | MESO convencional | `false` | `50` | 4 |
| **4** | MESO alternativo LTM | `true` | `100` | 2 |

En el modelo **convencional**, SUMO comprueba si cada segmento está libre o congestionado y calcula cuánto deben esperar los vehículos para avanzar. En **LTM**, cuando sale un vehículo, el hueco que deja se propaga hacia atrás hasta permitir que avance el siguiente. Este comportamiento se activa con `--meso-ltm true`; no se han añadido otras opciones. Las rutas y los semáforos son iguales en las cuatro pruebas.

Los parámetros comunes a las cuatro pruebas fueron:

| Parámetro | Valor utilizado | Función |
|---|---|---|
| `-n` | `red_7x7/red_7x7.net.xml` | Red de carreteras usada también en MICRO. |
| `-r` | `red_7x7/N_rutas/rutas_N.rou.xml` | Rutas de cada demanda. |
| `-a` | `red_7x7/semaforos.add.xml,red_7x7/semaforos_progresivos_rectas.add.xml` | Fases y desfases de los semáforos. |
| `--begin`, `--end` | `0`, `3600` | Simula una hora. |
| `--seed` | `42` | Fija la semilla aleatoria. |
| `--time-to-teleport` | `300` | Permite desplazar vehículos bloqueados durante demasiado tiempo. |
| `--device.rerouting.probability` | `0` | Los vehículos mantienen su ruta inicial. |
| `--mesosim` | `true` | Activa la simulación MESO, basada en colas y segmentos. |
| `--meso-junction-control` | `true` | Aplica el control de paso en los cruces. |
| `--meso-junction-control.limited` | `false` | Aplica ese control también cuando el siguiente segmento está libre. |
| `--meso-jam-threshold` | `-1` | Calcula automáticamente cuándo un segmento se considera congestionado en MESO convencional. |
| `--meso-overtaking` | `false` | Desactiva los adelantamientos internos del modelo MESO. |

Los cuatro parámetros `meso-tau` se dejaron con los **valores por defecto** de SUMO 1.28.0. Indican separaciones mínimas entre vehículos o tiempos de propagación de huecos, según el modelo:

| Parámetro (valor por defecto) | Uso en MESO convencional | Uso en MESO LTM |
|---|---|---|
| `meso-tauff` (**1,13 s**) | Tiempo mínimo entre vehículos que pasan de un segmento libre a otro libre. | Tiempo mínimo entre vehículos que avanzan y tiempo para propagar un hueco 7,5 m hacia atrás en flujo libre. |
| `meso-taufj` (**1,13 s**) | Tiempo mínimo al pasar de un segmento libre a otro congestionado. | No se utiliza directamente. |
| `meso-taujf` (**1,73 s**) | Tiempo mínimo al pasar de un segmento congestionado a otro libre. | Tiempo mínimo entre vehículos que vuelven a avanzar tras estar bloqueados. |
| `meso-taujj` (**1,40 s**) | Controla la velocidad con la que se libera una cola congestionada. | Tiempo que tarda un hueco en propagarse 7,5 m hacia atrás cuando el vehículo no circulaba en flujo libre. |

**Solo se cambian `--meso-ltm` y `--meso-edgelength` entre las cuatro pruebas.**

Los resultados se guardaron por separado en:

- **Prueba 1:** `meso/prueba_1_progresivos/`
- **Prueba 2:** `meso/prueba_2_progresivos/`
- **Prueba 3:** `meso/prueba_3_progresivos/`
- **Prueba 4:** `meso/prueba_4_ltm_progresivos/`

### 5.2. Vehículos y teletransportes

| Prueba | Demanda | Insertados | Finalizados | Circulando | Pendientes | Teleports |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 3000 | 3001 | 2769 | 232 | 0 | 0 |
| 1 | 4000 | 4000 | 3694 | 306 | 0 | 0 |
| 1 | 5000 | 5001 | 4628 | 373 | 0 | 0 |
| 1 | 6000 | 5907 | 4152 | 1755 | 94 | 47 |
| 1 | 7000 | 6403 | 2990 | 3413 | 597 | 313 |
| 1 | 8000 | 6625 | 2351 | 4274 | 1376 | 624 |
| 1 | 9000 | 6781 | 2080 | 4701 | 2219 | 797 |
| 1 | 11000 | 6665 | 1565 | 5100 | 4333 | 1064 |
| 2 | 3000 | 3001 | 2772 | 229 | 0 | 0 |
| 2 | 4000 | 4000 | 3692 | 308 | 0 | 0 |
| 2 | 5000 | 5001 | 4620 | 381 | 0 | 0 |
| 2 | 6000 | 5931 | 4574 | 1357 | 70 | 34 |
| 2 | 7000 | 6464 | 3388 | 3076 | 536 | 317 |
| 2 | 8000 | 6861 | 2771 | 4090 | 1140 | 571 |
| 2 | 9000 | 7008 | 2365 | 4643 | 1992 | 756 |
| 2 | 11000 | 7167 | 2106 | 5061 | 3831 | 952 |
| 3 | 3000 | 3001 | 2770 | 231 | 0 | 0 |
| 3 | 4000 | 4000 | 3692 | 308 | 0 | 0 |
| 3 | 5000 | 5001 | 4626 | 375 | 0 | 0 |
| 3 | 6000 | 5990 | 5221 | 769 | 11 | 2 |
| 3 | 7000 | 6343 | 3041 | 3302 | 657 | 407 |
| 3 | 8000 | 6668 | 2712 | 3956 | 1333 | 661 |
| 3 | 9000 | 6756 | 2304 | 4452 | 2244 | 922 |
| 3 | 11000 | 6777 | 2062 | 4715 | 4221 | 1131 |
| 4 (LTM) | 3000 | 3001 | 2767 | 234 | 0 | 0 |
| 4 (LTM) | 4000 | 4000 | 3686 | 314 | 0 | 0 |
| 4 (LTM) | 5000 | 5001 | 4639 | 362 | 0 | 0 |
| 4 (LTM) | 6000 | 6001 | 5403 | 598 | 0 | 0 |
| 4 (LTM) | 7000 | 6881 | 5047 | 1834 | 119 | 54 |
| 4 (LTM) | 8000 | 7053 | 3168 | 3885 | 948 | 457 |
| 4 (LTM) | 9000 | 7386 | 3062 | 4324 | 1614 | 605 |
| 4 (LTM) | 11000 | 7223 | 2134 | 5089 | 3775 | 962 |

Como en MICRO, **finalizados = insertados − circulando**. Los pendientes no llegaron a entrar antes del segundo 3600. Si se han retirado vehículos durante la simulación, también pueden aparecer dentro del cálculo de finalizados.

### 5.3. Medias de viaje y rendimiento computacional

| Prueba | Demanda | Speed (m/s) | Duration (s) | WaitingTime (s) | TimeLoss (s) | `real` limpio (s) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 3000 | 6,49 | 252,55 | 64,76 | 140,52 | 0,34 |
| 1 | 4000 | 6,29 | 262,38 | 57,12 | 150,42 | 0,41 |
| 1 | 5000 | 5,97 | 276,68 | 51,16 | 164,57 | 0,44 |
| 1 | 6000 | 4,94 | 384,85 | 51,86 | 274,28 | 0,50 |
| 1 | 7000 | 4,28 | 499,24 | 60,89 | 390,11 | 0,95 |
| 1 | 8000 | 4,13 | 589,74 | 83,49 | 482,92 | 2,25 |
| 1 | 9000 | 3,87 | 656,81 | 92,40 | 551,86 | 2,96 |
| 1 | 11000 | 3,29 | 947,10 | 141,71 | 845,75 | 5,37 |
| 2 | 3000 | 6,49 | 252,87 | 64,61 | 140,80 | 0,34 |
| 2 | 4000 | 6,27 | 262,97 | 56,95 | 151,00 | 0,43 |
| 2 | 5000 | 5,90 | 279,82 | 51,26 | 167,77 | 0,44 |
| 2 | 6000 | 5,11 | 356,43 | 51,94 | 245,24 | 0,51 |
| 2 | 7000 | 4,56 | 430,63 | 60,14 | 321,45 | 1,41 |
| 2 | 8000 | 4,18 | 530,25 | 73,79 | 422,15 | 1,32 |
| 2 | 9000 | 3,78 | 623,68 | 88,26 | 517,48 | 2,71 |
| 2 | 11000 | 3,33 | 799,79 | 121,34 | 696,59 | 3,04 |
| 3 | 3000 | 6,47 | 253,73 | 65,87 | 141,70 | 0,36 |
| 3 | 4000 | 6,25 | 263,85 | 59,58 | 151,88 | 0,43 |
| 3 | 5000 | 5,90 | 279,36 | 55,50 | 167,31 | 0,46 |
| 3 | 6000 | 5,26 | 330,48 | 58,02 | 218,93 | 0,52 |
| 3 | 7000 | 4,39 | 474,18 | 87,61 | 365,16 | 1,67 |
| 3 | 8000 | 4,30 | 513,79 | 101,49 | 406,15 | 2,12 |
| 3 | 9000 | 3,82 | 648,36 | 132,82 | 542,87 | 4,02 |
| 3 | 11000 | 3,24 | 862,90 | 190,05 | 760,11 | 7,37 |
| 4 (LTM) | 3000 | 6,45 | 254,38 | 64,86 | 142,32 | 0,36 |
| 4 (LTM) | 4000 | 6,25 | 264,04 | 57,09 | 152,10 | 0,41 |
| 4 (LTM) | 5000 | 5,97 | 276,15 | 51,33 | 164,10 | 0,45 |
| 4 (LTM) | 6000 | 5,49 | 307,06 | 49,23 | 195,24 | 0,51 |
| 4 (LTM) | 7000 | 4,76 | 384,59 | 53,17 | 273,78 | 0,69 |
| 4 (LTM) | 8000 | 4,29 | 498,98 | 70,28 | 390,20 | 2,53 |
| 4 (LTM) | 9000 | 3,97 | 540,08 | 77,50 | 433,06 | 3,37 |
| 4 (LTM) | 11000 | 3,61 | 740,62 | 119,93 | 636,87 | 6,58 |

Las medias son de los viajes finalizados. `Duration`, `WaitingTime` y `TimeLoss` están en **segundos de simulación**; `real` limpio es lo que tarda el ordenador en ejecutar SUMO, con los mensajes ocultos. La configuración del tráfico es la misma.

### 5.4. Comparación con MICRO estático

| Demanda | MICRO finalizados | Prueba 1 | Prueba 2 | Prueba 3 | Prueba 4 (LTM) |
|---:|---:|---:|---:|---:|---:|
| 3000 | 2649 | 2769 | 2772 | 2770 | 2767 |
| 4000 | 3464 | 3694 | 3692 | 3692 | 3686 |
| 5000 | 4070 | 4628 | 4620 | 4626 | 4639 |
| 6000 | 4403 | 4152 | 4574 | 5221 | 5403 |
| 7000 | 4419 | 2990 | 3388 | 3041 | 5047 |
| 8000 | 3804 | 2351 | 2771 | 2712 | 3168 |
| 9000 | 4068 | 2080 | 2365 | 2304 | 3062 |
| 11000 | 3722 | 1565 | 2106 | 2062 | 2134 |

**Observaciones:**

1. Entre **3000 y 5000 vehículos**, las cuatro pruebas MESO son parecidas y no tienen teletransportes.
2. Con **6000 y 7000**, LTM completa más viajes. Por ejemplo, a 7000 llega a **5047 finalizados**, frente a **4419** de MICRO.
3. Desde **8000 vehículos** aparece mucha congestión en MESO. Con 11 000, LTM finaliza **2134** frente a **3722** de MICRO y tiene **962 teletransportes** frente a **249**.
4. MESO se ejecuta más rápido: con 11 000 vehículos tarda entre **3,04 y 7,37 s**, frente a **18,97 s** de MICRO estático.

**Conclusión:** entre las pruebas convencionales, la **prueba 2 (100 m)** da resultados más equilibrados. La **prueba 4 (LTM, 100 m)** completa más viajes en varias demandas medias y altas. Aun así, ninguna reproduce bien el comportamiento de MICRO cuando la demanda supera los 8000 vehículos.

**Referencia técnica:** [SUMO — Simulación mesoscópica](https://sumo.dlr.de/docs/Simulation/Meso.html).

## Referencias

- [SUMO — Traffic Lights](https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html)
- [SUMO — Statistics](https://sumo.dlr.de/docs/Simulation/Output/StatisticOutput.html)
- [SUMO — Vehicle Insertion](https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html)
