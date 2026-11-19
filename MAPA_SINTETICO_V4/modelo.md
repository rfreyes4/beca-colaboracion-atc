# Mapa sintético V4 — MICRO y MESO con semáforos progresivos

Pruebas realizadas con **SUMO 1.28.0** sobre una red sintética de **7×7 intersecciones**, tramos de **200 m** y **un carril por sentido**. En MICRO se comparan el **enrutamiento estático y el dinámico**; en MESO se estudian cuatro configuraciones con **enrutamiento estático**. Todas utilizan semáforos progresivos.

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

| Parámetro | Valor usado | Qué significa |
|---|---|---|
| Red (`-n`) | `red_7x7/red_7x7.net.xml` | Archivo de la red: calles, carriles, cruces y conexiones. |
| Rutas (`-r`) | `red_7x7/N_rutas/rutas_N.rou.xml` | Vehículos y recorridos previstos para la demanda `N`. |
| Semáforos (`-a`) | `red_7x7/semaforos.add.xml,red_7x7/semaforos_progresivos_rectas.add.xml` | Carga tanto las fases semafóricas como sus desfases de coordinación. |
| Intervalo (`--begin`, `--end`) | `0` a `3600` s | Simula una hora. Al llegar a 3600 s se detiene aunque queden vehículos circulando o sin insertar. |
| Semilla (`--seed`) | `42` | Fija la aleatoriedad de SUMO para poder repetir la simulación. Las rutas ya se habían generado aparte con RandomTrips. |
| Teletransporte (`--time-to-teleport`) | `300` s | Permite teletransportar un vehículo que permanece bloqueado demasiado tiempo, para evitar esperas indefinidas. No significa que todos los vehículos se teletransporten al cumplir 300 s de viaje. |
| Enrutamiento estático | `--device.rerouting.probability 0` | Desactiva el dispositivo de reenrutamiento: cada vehículo mantiene la ruta prevista. |
| Enrutamiento dinámico | `--device.rerouting.probability 1` y `--device.rerouting.period 120` | Activa el dispositivo de reenrutamiento para todos los vehículos y permite revisar periódicamente su ruta cada 120 s según las condiciones de tráfico. No implica que todos cambien de ruta. |
| Resultados completos | `--no-step-log true`, `--duration-log.statistics true`, `--verbose true` | Oculta la línea de progreso de cada paso, pero mantiene las estadísticas de viajes y la información de la ejecución. |
| Medición limpia | Misma simulación, suprimiendo la salida para medir `real`, `user` y `sys` | Sirve para medir el tiempo de ejecución sin el coste adicional de imprimir mensajes; no modifica la circulación. |

Los archivos de demanda proceden de **RandomTrips** (semilla 42, salidas aleatorias entre 0 y 3600 s); demandas nominales de 3000, 4000, 5000, 6000, 7000, 8000, 9000 y 11 000. Se reutilizan las mismas rutas de entrada en ambos enrutamientos.

### 2.1. Cómo interpretar las medidas de SUMO (MICRO y MESO)

Los parámetros anteriores **configuran la simulación**. En cambio, los siguientes nombres son **resultados que aparecen en los logs**; no son opciones que se hayan modificado en las pruebas.

| Medida | Qué indica | Qué no debe confundirse |
|---|---|---|
| `Loaded` / **Cargados** | Vehículos leídos o preparados desde el archivo de rutas. | No todos consiguen incorporarse a la carretera antes del final. |
| `Inserted` / **Insertados** | Vehículos que realmente han entrado en la red. | No equivale a la demanda nominal ni a los finalizados. |
| `Running` / **Circulando** | Vehículos que todavía permanecen en la red cuando acaba la simulación. | Pueden estar circulando o detenidos en una cola. |
| `Waiting` / **Pendientes** | **Número de vehículos** que siguen esperando fuera de la red porque no han podido incorporarse. | **No es** `WaitingTime`, que se mide en segundos por vehículo. |
| **Finalizados** | En las tablas de este documento se calcula como **insertados − circulando**. | Cuenta vehículos que ya no están en la red; si hubo retiradas por teletransporte, no equivale necesariamente a llegadas normales a destino. |
| `RouteLength` (m) | Longitud del recorrido realizado por un vehículo. | No es el tamaño de un segmento MESO. Con rutas dinámicas puede aumentar si se toma otro camino. |
| `Speed` (m/s) | Velocidad media del viaje, expresada en metros por segundo. | No es la velocidad instantánea de un coche ni la velocidad máxima de la carretera. |
| `Duration` (s) | Tiempo transcurrido **desde que el vehículo entra en la red hasta que termina su viaje**. Incluye los semáforos, las colas y las reducciones de velocidad. | **No incluye** el tiempo que tuvo que esperar antes de entrar (`DepartDelay`). |
| `WaitingTime` (s) | Tiempo acumulado **dentro de la red** con velocidad muy baja (≤ 0,1 m/s), normalmente por semáforos o atascos. Las paradas planificadas no cuentan. | No es toda la duración del viaje ni la espera para incorporarse a la red. |
| `TimeLoss` (s) | Tiempo adicional perdido por circular más despacio que la velocidad ideal del recorrido: incluye esperas por semáforos y otros retrasos **dentro de la red**. | **Incluye `WaitingTime`**; no hay que sumar ambas medidas porque se contaría parte del retraso dos veces. |
| `DepartDelay` (s) | Retraso entre la hora de salida **programada** y la hora en la que el vehículo **consigue entrar** en la red. | No son segundos parado ante un semáforo: ese tiempo ya ocurre durante el viaje. |
| `Teleports` | Número de veces que SUMO desplaza vehículos bloqueados para resolver situaciones de espera excesiva. | No es el número de vehículos pendientes ni demuestra por sí solo que exista un bloqueo circular. |

**Ejemplo para distinguir los tiempos:** un vehículo tiene programada su salida en el segundo **100**, pero no consigue entrar hasta el **120** y llega a su destino en el **320**. Por tanto, su `DepartDelay` es **20 s** y su `Duration` es **200 s**. Supongamos que durante el trayecto estuvo **40 s detenido** (`WaitingTime`) y perdió **60 s frente a la circulación ideal** (`TimeLoss`): esos 60 s **ya incluyen** los 40 s parado. Desde la salida programada hasta la llegada transcurrieron **220 s = 20 + 200**; no debemos sumar también `WaitingTime` y `TimeLoss`.

**Importante al comparar MICRO y MESO:** las medidas tienen los mismos nombres, pero los vehículos se mueven mediante modelos diferentes (movimiento individual en MICRO y colas/segmentos en MESO). Además, las medias habituales corresponden a los viajes incluidos en las estadísticas de salida, no a todos los vehículos que se pretendían insertar. Con más congestión, los vehículos que siguen en la red a los 3600 s pueden alterar la interpretación de las medias.

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

**Finalizados = insertados − circulando**. «Pendientes» son vehículos que no han entrado en la red cuando termina la simulación. Las diferencias entre vehículos, segundos de espera y llegadas se explican en el apartado 2.1.

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

**Cómo leer esta tabla:** `Duration` mide el tiempo de viaje una vez dentro de la red; `WaitingTime` es la parte del recorrido detenida; `TimeLoss` incluye esa espera y otros retrasos por circular más lento; y `DepartDelay` sucede **antes de entrar**. La diferencia y un ejemplo completo aparecen en el **apartado 2.1**. **Todas las medias corresponden a los viajes contabilizados en las estadísticas**, por lo que deben interpretarse junto con el número de vehículos finalizados y los que todavía están circulando.

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

La ejecución **completa** muestra estadísticas y avisos. La medición **limpia** se ejecuta con la salida suprimida; no cambia las reglas de circulación. `Performance Duration` es el tiempo de procesamiento que indica SUMO; `real` es el tiempo de reloj medido desde la terminal, `user` el tiempo de CPU en modo usuario y `sys` el tiempo de CPU dedicado al sistema operativo. **Ninguno es el tiempo que tarda un vehículo en llegar:** ese dato aparece en `Duration` (apartado 2.1). Los valores `real` pueden variar entre ejecuciones.

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

1. **Hasta 5000 vehículos** no se registran teletransportes y los dos enrutamientos completan un número similar de viajes.
2. **Desde 6000 vehículos**, el enrutamiento estático presenta teletransportes que aumentan con la demanda (hasta **249** con 11 000), mientras que el dinámico registra **0** hasta 9000 y **2** con 11 000.
3. El **dinámico** finaliza más viajes en **6 de las 8 demandas**; sin embargo, suele recorrer más distancia y presenta mayores tiempos medios de viaje.
4. La ejecución **estática es más rápida** computacionalmente en todas las demandas. Con 11 000 vehículos: **18,97 s** frente a **28,23 s** en la medición limpia.

**Conclusión:** con semáforos progresivos, el reenrutamiento dinámico reduce notablemente los teletransportes, pero no reduce los tiempos medios de viaje. Para la posterior comparación MICRO–MESO se tomará como referencia principal **MICRO estático con estos mismos semáforos progresivos**.

## 5. Simulación MESO con semáforos progresivos

Se realizaron **cuatro pruebas mesoscópicas** en SUMO 1.28.0, utilizando la misma red 7×7, los mismos archivos de rutas y los **49 semáforos progresivos** descritos anteriormente. Todas las simulaciones MESO usan **enrutamiento estático**, para compararlas con el MICRO estático del apartado 3.

### 5.1. Configuración de las cuatro pruebas

El objetivo es comparar el modelo MESO convencional con distintos tamaños de segmento y el modelo alternativo **LTM**, que representa la propagación de huecos hacia atrás cuando se libera espacio en una cola. Aquí `--meso-edgelength` **no cambia la longitud real de las carreteras**: solo modifica cómo las divide internamente el simulador.

| Prueba | Modelo | `--meso-ltm` | `--meso-edgelength` | Segmentos por tramo de 200 m |
|---|---|---|---:|---:|
| **1** | MESO convencional | `false` | `200` | 1 |
| **2** | MESO convencional | `false` | `100` | 2 |
| **3** | MESO convencional | `false` | `50` | 4 |
| **4** | MESO alternativo LTM | `true` | `100` | 2 |

El modelo **convencional** distingue entre segmentos libres y congestionados según su ocupación, y calcula los tiempos mínimos de paso teniendo en cuenta esos estados. El modelo **LTM** utiliza la propagación de huecos: cuando un vehículo sale de un segmento, el espacio que deja se transmite progresivamente hacia atrás y permite que otros avancen. **Activar `--meso-ltm true` basta para utilizar LTM**; no se añadió ningún parámetro extra para activar los huecos. En ambos casos se conservan los mismos semáforos y rutas.

Los parámetros comunes a las cuatro pruebas fueron:

| Parámetro | Valor utilizado | Función |
|---|---|---|
| `-n` | `red_7x7/red_7x7.net.xml` | Utiliza exactamente la misma red que MICRO. |
| `-r` | `red_7x7/N_rutas/rutas_N.rou.xml` | Utiliza las mismas rutas de entrada para cada demanda `N`. |
| `-a` | `red_7x7/semaforos.add.xml,red_7x7/semaforos_progresivos_rectas.add.xml` | Mantiene las fases de los 49 semáforos y sus desfases progresivos. |
| `--begin`, `--end` | `0`, `3600` | Simula 3600 s y se detiene aunque queden vehículos en la red. |
| `--seed` | `42` | Mantiene una semilla fija para repetir la ejecución. |
| `--time-to-teleport` | `300` | Evita esperas indefinidas mediante el teletransporte de vehículos bloqueados durante demasiado tiempo. |
| `--device.rerouting.probability` | `0` | Mantiene las rutas estáticas: los coches no buscan caminos alternativos durante la simulación. |
| `--mesosim` | `true` | Cambia del modelo de movimiento individual (MICRO) al modelo de colas por segmentos (MESO). |
| `--meso-junction-control` | `true` | Hace que MESO tenga en cuenta las reglas de paso en cruces y semáforos. |
| `--meso-junction-control.limited` | `false` | Mantiene el control de cruces también cuando el segmento siguiente está libre; con `true`, este control se aplicaría solo al entrar en un segmento congestionado. |
| `--meso-jam-threshold` | `-1` | En MESO convencional calcula automáticamente el umbral a partir del cual un segmento se considera congestionado. LTM no utiliza esta clasificación de estados. |
| `--meso-overtaking` | `false` | Impide que vehículos intercambien posiciones por el mecanismo de adelantamiento mesoscópico. |

No se modificaron explícitamente los parámetros `meso-tauff`, `meso-taufj`, `meso-taujf` ni `meso-taujj`: se mantuvieron los **valores por defecto** de SUMO 1.28.0. Son parámetros de tiempo que condicionan la separación entre vehículos o la propagación de huecos, y **no deben confundirse con las métricas de salida** `TimeLoss`, `WaitingTime` o `DepartDelay`.

| Parámetro (valor por defecto) | Uso en MESO convencional | Uso en MESO LTM |
|---|---|---|
| `meso-tauff` (**1,13 s**) | Separación temporal mínima al pasar entre dos segmentos libres. | Separación mínima al avanzar; también interviene en la propagación hacia atrás de huecos generados en flujo libre. |
| `meso-taufj` (**1,13 s**) | Separación temporal al pasar de un segmento libre a uno congestionado. | No interviene directamente en el modelo LTM. |
| `meso-taujf` (**1,73 s**) | Separación temporal al salir de un segmento congestionado hacia uno libre. | Separación al volver a avanzar después de haber estado bloqueado. |
| `meso-taujj` (**1,40 s**) | Controla cómo se transmiten hacia atrás los espacios disponibles dentro de una cola congestionada. | Tiempo de propagación hacia atrás de un hueco por cada 7,5 m cuando el vehículo no avanzaba en flujo libre. |

**Entre las cuatro pruebas solo cambian `--meso-ltm` y/o `--meso-edgelength`; los demás valores se mantienen.**

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

Se mantiene el mismo criterio del apartado MICRO: **Finalizados = insertados − circulando**; «Pendientes» son vehículos que no pudieron entrar antes de los 3600 s. En condiciones de congestión, el total que deja de circular también puede incluir vehículos retirados por teletransporte, por lo que no equivale siempre a llegadas normales a destino. Estas diferencias se explican en el **apartado 2.1**.

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

Las medias proceden de los logs originales de cada prueba. **`Duration`, `WaitingTime` y `TimeLoss` son tiempos de viaje en segundos simulados** (véanse las diferencias y el ejemplo del apartado 2.1). En cambio, **`real` limpio mide segundos reales de ejecución en el ordenador**, sin imprimir los mensajes habituales. No se modificó el tráfico para esta medición. Como en MICRO, las medias deben leerse junto al número de vehículos finalizados y no representan necesariamente a toda la demanda nominal.

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

1. **3000–5000 vehículos:** las cuatro configuraciones MESO dan resultados parecidos, con **0 teletransportes** y tiempos medios de viaje inferiores a MICRO.
2. **6000 vehículos:** la prueba 3 (50 m) y LTM mejoran claramente el número de finalizados; LTM alcanza 5403 finalizados y 0 teletransportes, aunque supera a MICRO.
3. **7000 vehículos:** la prueba 4 (LTM) alcanza 5047 finalizados y 54 teletransportes, frente a los 4419 y 46 de MICRO. Entre los tres modelos convencionales, la prueba 2 (100 m) completa más viajes.
4. **8000–11000 vehículos:** todas las pruebas MESO muestran congestión importante. LTM suele completar más viajes que el convencional, pero sigue lejos de MICRO a las demandas altas. Con 11 000 vehículos, LTM finaliza 2134 frente a 3722 de MICRO, y registra 962 teletransportes frente a 249.
5. **Rendimiento:** MESO ejecuta las simulaciones mucho más rápido que MICRO. Con 11 000 vehículos, los tiempos limpios de las cuatro pruebas van de 3,04 a 7,37 s, frente a 18,97 s en MICRO estático.

**Conclusión:** la prueba 2 (**MESO convencional, 100 m**) ofrece el comportamiento más equilibrado entre las configuraciones convencionales, mientras que la prueba 4 (**LTM, 100 m**) mejora el número de finalizados en las demandas medias y altas. Sin embargo, ninguna de las cuatro reproduce completamente el comportamiento del MICRO estático con semáforos progresivos, especialmente a partir de 8000 vehículos.

**Referencia técnica:** [SUMO — Simulación mesoscópica](https://sumo.dlr.de/docs/Simulation/Meso.html).

## Referencias

- [SUMO — Traffic Lights](https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html)
- [SUMO — Statistics](https://sumo.dlr.de/docs/Simulation/Output/StatisticOutput.html)
- [SUMO — Vehicle Insertion](https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html)
