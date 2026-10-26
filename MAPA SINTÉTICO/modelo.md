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

## Resultado

Red sintética de **25 intersecciones y 16 manzanas**, visualizada en SUMO-GUI.

![Red sintética 5x5](imagenes/resultado.png)
