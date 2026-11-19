# Informe de diagnostico: cuatro MESO progresivos vs MICRO

Fecha: 2026-11-19T10:35:18  |  SUMO: Eclipse SUMO sumo 1.28.0

## Metodo y limites

- Misma red, rutas y semaforos progresivos; seed 42; 0-3600 s; sin enrutamiento dinamico.
- MESO 1 = convencional 200 m; MESO 2 = convencional 100 m; MESO 3 = convencional 50 m; MESO 4 = LTM 100 m.
- MICRO se ejecuta de nuevo como referencia, con los mismos archivos y opciones comunes.
- Unicamente se anaden salidas de observacion. Los resultados originales no se modifican.
- **Importante**: medias de duracion/espera se calculan SOLO para viajes terminados. Los no terminados tambien aparecen en sus propios recuentos y XML.
- **Sospecha de bloqueo** = velocidad de arista < 2 m/s y densidad >= 15 veh/km en >= 3 intervalos consecutivos de 60 s, con al menos 30 vehiculo-segundos/intervalo. No demuestra un deadlock: los semaforos rojos tambien producen colas.
- Los tiempos de MICRO y MESO son modelos diferentes: la salida no permite atribuir por si sola una causa mecanica exacta a un semaforo o cruce.

## Reproduccion de los datos anteriores

- Logs MESO anteriores encontrados: 32 de 32.
- Diferencias con logs MESO anteriores: 19.
- Diferencias con tabla MICRO historica: 0.

Las ejecuciones nuevas no reproducen estas cifras antiguas:
- prueba_1_progresivos / 6000: llegados 4152 -> 4147; teleports 47 -> 47.
- prueba_2_progresivos / 6000: llegados 4574 -> 4569; teleports 34 -> 34.
- prueba_3_progresivos / 6000: llegados 5221 -> 5220; teleports 2 -> 2.
- prueba_1_progresivos / 7000: llegados 2990 -> 2921; teleports 313 -> 313.
- prueba_2_progresivos / 7000: llegados 3388 -> 3332; teleports 317 -> 317.
- prueba_3_progresivos / 7000: llegados 3041 -> 2967; teleports 407 -> 407.
- prueba_4_ltm_progresivos / 7000: llegados 5047 -> 5037; teleports 54 -> 54.
- prueba_1_progresivos / 8000: llegados 2351 -> 2155; teleports 624 -> 624.
- prueba_2_progresivos / 8000: llegados 2771 -> 2640; teleports 571 -> 571.
- prueba_3_progresivos / 8000: llegados 2712 -> 2532; teleports 661 -> 661.
- prueba_4_ltm_progresivos / 8000: llegados 3168 -> 3078; teleports 457 -> 457.
- prueba_1_progresivos / 9000: llegados 2080 -> 1839; teleports 797 -> 797.
- prueba_2_progresivos / 9000: llegados 2365 -> 2147; teleports 756 -> 756.
- prueba_3_progresivos / 9000: llegados 2304 -> 1982; teleports 922 -> 922.
- prueba_4_ltm_progresivos / 9000: llegados 3062 -> 2896; teleports 605 -> 605.
- prueba_1_progresivos / 11000: llegados 1565 -> 1138; teleports 1064 -> 1064.
- prueba_2_progresivos / 11000: llegados 2106 -> 1681; teleports 952 -> 952.
- prueba_3_progresivos / 11000: llegados 2062 -> 1513; teleports 1131 -> 1131.
- prueba_4_ltm_progresivos / 11000: llegados 2134 -> 1740; teleports 962 -> 962.

## Llegados al final de la simulacion

| Demanda | MICRO | MESO 1 (200) | MESO 2 (100) | MESO 3 (50) | MESO 4 (LTM) |
|---:|---:|---:|---:|---:|---:|
| 3000 | 2649 | 2769 | 2772 | 2770 | 2767 |
| 4000 | 3464 | 3694 | 3692 | 3692 | 3686 |
| 5000 | 4070 | 4628 | 4620 | 4626 | 4639 |
| 6000 | 4403 | 4147 | 4569 | 5220 | 5403 |
| 7000 | 4419 | 2921 | 3332 | 2967 | 5037 |
| 8000 | 3804 | 2155 | 2640 | 2532 | 3078 |
| 9000 | 4068 | 1839 | 2147 | 1982 | 2896 |
| 11000 | 3722 | 1138 | 1681 | 1513 | 1740 |

## Teletransportes

| Demanda | MICRO | MESO 1 | MESO 2 | MESO 3 | MESO 4 LTM |
|---:|---:|---:|---:|---:|---:|
| 3000 | 0 | 0 | 0 | 0 | 0 |
| 4000 | 0 | 0 | 0 | 0 | 0 |
| 5000 | 0 | 0 | 0 | 0 | 0 |
| 6000 | 6 | 47 | 34 | 2 | 0 |
| 7000 | 46 | 313 | 317 | 407 | 54 |
| 8000 | 128 | 624 | 571 | 661 | 457 |
| 9000 | 129 | 797 | 756 | 922 | 605 |
| 11000 | 249 | 1064 | 952 | 1131 | 962 |

## Indicios que permiten investigar el desacuerdo

### Demanda 3000
MICRO: 2649 terminados; 55 pendientes de insercion; 297 circulando al llegar a 3600 s; 0 teleports.
- MESO 1: 200 m: 2769 terminados (diferencia de +120 con MICRO); 232 en red, 0 esperando entrar, 0 teleports, 0 focos candidatos.
- MESO 2: 100 m: 2772 terminados (diferencia de +123 con MICRO); 229 en red, 0 esperando entrar, 0 teleports, 0 focos candidatos.
- MESO 3: 50 m: 2770 terminados (diferencia de +121 con MICRO); 231 en red, 0 esperando entrar, 0 teleports, 0 focos candidatos.
- MESO 4: LTM 100 m: 2767 terminados (diferencia de +118 con MICRO); 234 en red, 0 esperando entrar, 0 teleports, 0 focos candidatos.

### Demanda 4000
MICRO: 3464 terminados; 147 pendientes de insercion; 389 circulando al llegar a 3600 s; 0 teleports.
- MESO 1: 200 m: 3694 terminados (diferencia de +230 con MICRO); 306 en red, 0 esperando entrar, 0 teleports, 0 focos candidatos.
- MESO 2: 100 m: 3692 terminados (diferencia de +228 con MICRO); 308 en red, 0 esperando entrar, 0 teleports, 0 focos candidatos.
- MESO 3: 50 m: 3692 terminados (diferencia de +228 con MICRO); 308 en red, 0 esperando entrar, 0 teleports, 0 focos candidatos.
- MESO 4: LTM 100 m: 3686 terminados (diferencia de +222 con MICRO); 314 en red, 0 esperando entrar, 0 teleports, 0 focos candidatos.
- Alertas de congestion prolongada: `e-j-1-3-a-j-1-4` [micro, 2580-2820 s], `e-j-0-3-a-j-0-2` [micro, 2700-2880 s].

### Demanda 5000
MICRO: 4070 terminados; 387 pendientes de insercion; 544 circulando al llegar a 3600 s; 0 teleports.
- MESO 1: 200 m: 4628 terminados (diferencia de +558 con MICRO); 373 en red, 0 esperando entrar, 0 teleports, 3 focos candidatos.
- MESO 2: 100 m: 4620 terminados (diferencia de +550 con MICRO); 381 en red, 0 esperando entrar, 0 teleports, 6 focos candidatos.
- MESO 3: 50 m: 4626 terminados (diferencia de +556 con MICRO); 375 en red, 0 esperando entrar, 0 teleports, 2 focos candidatos.
- MESO 4: LTM 100 m: 4639 terminados (diferencia de +569 con MICRO); 362 en red, 0 esperando entrar, 0 teleports, 2 focos candidatos.
- Alertas de congestion prolongada: `e-j-1-4-a-j-1-3` [micro, 2880-3600 s], `e-j-1-4-a-j-1-3` [micro, 2100-2640 s], `e-j-0-3-a-j-0-2` [micro, 2340-2820 s], `e-j-1-5-a-j-1-4` [micro, 2400-2820 s], `e-j-1-5-a-j-1-4` [micro, 2880-3300 s].

### Demanda 6000
MICRO: 4403 terminados; 815 pendientes de insercion; 783 circulando al llegar a 3600 s; 6 teleports.
- MESO 1: 200 m: 4147 terminados (diferencia de -256 con MICRO); 1755 en red, 94 esperando entrar, 47 teleports, 115 focos candidatos.
- MESO 2: 100 m: 4569 terminados (diferencia de +166 con MICRO); 1357 en red, 70 esperando entrar, 34 teleports, 73 focos candidatos.
- MESO 3: 50 m: 5220 terminados (diferencia de +817 con MICRO); 769 en red, 11 esperando entrar, 2 teleports, 39 focos candidatos.
- MESO 4: LTM 100 m: 5403 terminados (diferencia de +1000 con MICRO); 598 en red, 0 esperando entrar, 0 teleports, 20 focos candidatos.
- Aristas con mas teleports MESO combinados: `e-j-4-6-a-j-4-5` (6), `e-j-5-4-a-j-5-5` (6), `e-j-6-4-a-j-6-5` (5), `e-j-6-6-a-j-6-5` (4), `e-j-2-5-a-j-2-6` (4).
- Alertas de congestion prolongada: `e-j-1-6-a-j-1-5` [prueba_1_progresivos, 1080-3600 s], `e-j-2-6-a-j-1-6` [prueba_1_progresivos, 1320-3600 s], `e-j-1-6-a-j-1-5` [prueba_2_progresivos, 1440-3600 s], `e-j-2-5-a-j-1-5` [prueba_2_progresivos, 1440-3600 s], `e-j-3-2-a-j-2-2` [prueba_1_progresivos, 1620-3600 s].

### Demanda 7000
MICRO: 4419 terminados; 1404 pendientes de insercion; 1177 circulando al llegar a 3600 s; 46 teleports.
- MESO 1: 200 m: 2921 terminados (diferencia de -1498 con MICRO); 3413 en red, 597 esperando entrar, 313 teleports, 205 focos candidatos.
- MESO 2: 100 m: 3332 terminados (diferencia de -1087 con MICRO); 3076 en red, 536 esperando entrar, 317 teleports, 192 focos candidatos.
- MESO 3: 50 m: 2967 terminados (diferencia de -1452 con MICRO); 3302 en red, 657 esperando entrar, 407 teleports, 228 focos candidatos.
- MESO 4: LTM 100 m: 5037 terminados (diferencia de +618 con MICRO); 1834 en red, 119 esperando entrar, 54 teleports, 138 focos candidatos.
- Aristas con mas teleports MESO combinados: `e-j-2-6-a-j-1-6` (21), `e-j-0-6-a-j-1-6` (19), `e-j-3-6-a-j-2-6` (18), `e-j-6-5-a-j-5-5` (17), `e-j-4-6-a-j-4-5` (15).
- Alertas de congestion prolongada: `e-j-1-4-a-j-1-3` [prueba_2_progresivos, 480-3600 s], `e-j-1-5-a-j-1-4` [prueba_2_progresivos, 480-3600 s], `e-j-1-6-a-j-1-5` [prueba_1_progresivos, 600-3600 s], `e-j-1-5-a-j-1-4` [prueba_3_progresivos, 660-3600 s], `e-j-2-1-a-j-1-1` [prueba_1_progresivos, 780-3600 s].

### Demanda 8000
MICRO: 3804 terminados; 2270 pendientes de insercion; 1927 circulando al llegar a 3600 s; 128 teleports.
- MESO 1: 200 m: 2155 terminados (diferencia de -1649 con MICRO); 4274 en red, 1376 esperando entrar, 624 teleports, 221 focos candidatos.
- MESO 2: 100 m: 2640 terminados (diferencia de -1164 con MICRO); 4090 en red, 1140 esperando entrar, 571 teleports, 243 focos candidatos.
- MESO 3: 50 m: 2532 terminados (diferencia de -1272 con MICRO); 3956 en red, 1333 esperando entrar, 661 teleports, 235 focos candidatos.
- MESO 4: LTM 100 m: 3078 terminados (diferencia de -726 con MICRO); 3885 en red, 948 esperando entrar, 457 teleports, 246 focos candidatos.
- Aristas con mas teleports MESO combinados: `e-ext-n-6-a-j-0-6` (27), `e-j-1-6-a-j-0-6` (26), `e-j-2-5-a-j-2-6` (25), `e-j-3-6-a-j-3-5` (23), `e-j-6-5-a-j-5-5` (23).
- Alertas de congestion prolongada: `e-j-0-1-a-j-0-2` [prueba_1_progresivos, 360-3600 s], `e-j-1-5-a-j-1-4` [prueba_1_progresivos, 360-3600 s], `e-j-0-0-a-j-0-1` [prueba_1_progresivos, 420-3600 s], `e-j-1-6-a-j-1-5` [prueba_1_progresivos, 480-3600 s], `e-j-2-5-a-j-1-5` [prueba_2_progresivos, 480-3600 s].

### Demanda 9000
MICRO: 4068 terminados; 2937 pendientes de insercion; 1995 circulando al llegar a 3600 s; 129 teleports.
- MESO 1: 200 m: 1839 terminados (diferencia de -2229 con MICRO); 4701 en red, 2219 esperando entrar, 797 teleports, 216 focos candidatos.
- MESO 2: 100 m: 2147 terminados (diferencia de -1921 con MICRO); 4643 en red, 1992 esperando entrar, 756 teleports, 245 focos candidatos.
- MESO 3: 50 m: 1982 terminados (diferencia de -2086 con MICRO); 4452 en red, 2244 esperando entrar, 922 teleports, 243 focos candidatos.
- MESO 4: LTM 100 m: 2896 terminados (diferencia de -1172 con MICRO); 4324 en red, 1614 esperando entrar, 605 teleports, 239 focos candidatos.
- Aristas con mas teleports MESO combinados: `e-j-3-6-a-j-2-6` (26), `e-j-4-5-a-j-4-6` (26), `e-j-1-6-a-j-0-6` (26), `e-j-2-6-a-j-1-6` (25), `e-ext-e-5-a-j-5-6` (25).
- Alertas de congestion prolongada: `e-j-1-5-a-j-1-4` [prueba_1_progresivos, 300-3600 s], `e-j-2-4-a-j-2-3` [prueba_2_progresivos, 300-3600 s], `e-j-2-5-a-j-2-4` [prueba_1_progresivos, 360-3600 s], `e-j-2-4-a-j-2-3` [prueba_3_progresivos, 360-3600 s], `e-j-2-5-a-j-1-5` [prueba_1_progresivos, 420-3600 s].

### Demanda 11000
MICRO: 3722 terminados; 4866 pendientes de insercion; 2410 circulando al llegar a 3600 s; 249 teleports.
- MESO 1: 200 m: 1138 terminados (diferencia de -2584 con MICRO); 5100 en red, 4333 esperando entrar, 1064 teleports, 214 focos candidatos.
- MESO 2: 100 m: 1681 terminados (diferencia de -2041 con MICRO); 5061 en red, 3831 esperando entrar, 952 teleports, 244 focos candidatos.
- MESO 3: 50 m: 1513 terminados (diferencia de -2209 con MICRO); 4715 en red, 4221 esperando entrar, 1131 teleports, 230 focos candidatos.
- MESO 4: LTM 100 m: 1740 terminados (diferencia de -1982 con MICRO); 5089 en red, 3775 esperando entrar, 962 teleports, 230 focos candidatos.
- Aristas con mas teleports MESO combinados: `e-j-1-6-a-j-0-6` (32), `e-j-3-5-a-j-2-5` (31), `e-j-2-5-a-j-1-5` (31), `e-ext-n-6-a-j-0-6` (31), `e-j-1-0-a-j-0-0` (31).
- Alertas de congestion prolongada: `e-j-1-4-a-j-1-3` [prueba_2_progresivos, 240-3600 s], `e-j-1-4-a-j-1-3` [prueba_3_progresivos, 240-3600 s], `e-j-1-5-a-j-1-4` [prueba_1_progresivos, 300-3600 s], `e-j-2-2-a-j-3-2` [prueba_1_progresivos, 300-3600 s], `e-j-2-5-a-j-2-4` [prueba_1_progresivos, 300-3600 s].

## Como interpretar las causas

1. **Diferente insercion:** comparar `insertados`, `pendientes_entrada` y la evolucion en `02_evolucion_60s.csv`. Si MICRO no puede insertar vehiculos que MESO si, las medias de viajes completados tienen poblaciones distintas.
2. **Cuellos de botella concretos:** agrupar `03_teleports_detallados.csv` por arista y tiempo. Coincidencias con `04_sospechas_bloqueo_persistente.csv` son fuertes indicios de congestion recurrente, no necesariamente error de configuracion.
3. **Diferencias de flujo locales:** buscar las aristas mas discordantes en `05_diferencias_aristas_vs_micro.csv`. Revisar velocidades, densidades y salidas por arista; estas ultimas pueden estar afectadas por teleports.
4. **Dinamica del modelo:** el MESO convencional representa colas por segmentos; LTM propaga los huecos hacia atras. Incluso con igual semaforizacion pueden formarse y disiparse colas de otra manera.
5. **Sesgo de viajes terminados:** a 3600 s no todos llegan. Una media menor puede deberse a que los mas lentos no terminaron. Hay viajes sin terminar en cada `viajes.xml` y contadores en `01_resumen_global.csv`.

## Estructura de archivos

- `01_resumen_global.csv`: estadisticas de las 40 combinaciones analizadas.
- `02_evolucion_60s.csv`: evolucion de inserciones, circulantes y pendientes.
- `03_teleports_detallados.csv`: carretera y segundo de cada teleport.
- `04_sospechas_bloqueo_persistente.csv`: alertas de congestion prolongada.
- `05_diferencias_aristas_vs_micro.csv`: diferencia en velocidad, densidad, flujo y espera por carretera.
- `06_verificacion_con_logs_originales.csv`: comprobacion de reproducibilidad.
- `07_diferencias_globales_vs_micro.csv`: diferencias globales por demanda.
- `CASO/DEMANDA/`: comando, log de ejecucion, viajes, resumen temporal, aristas, estadisticas.

Fuentes: https://sumo.dlr.de/docs/Simulation/Meso.html ; https://sumo.dlr.de/docs/Simulation/Output/StatisticOutput.html ; https://sumo.dlr.de/docs/Simulation/Output/Lane-_or_Edge-based_Traffic_Measures.html
