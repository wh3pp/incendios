# Casos reales

Insumos para los dos casos de estudio del documento.

## Acos (Cusco, Perú)

- Evento: incendio forestal en el sector Mayuhuilca, distrito de Acos,
  provincia de Acomayo, Cusco.
- Fecha: 11/09/2025, 12:24 h; extinción 15/09/2025.
- Área oficial: 300 ha (INDECI, Reporte Complementario N.º 9686).
- Coordenadas de referencia: -13.95128, -71.73823.
- `acos_dem.npy`: DEM de 128×128 celdas, descargado de Terrarium/Mapzen,
  recortado a la ventana del evento.
- No existe perímetro oficial; el documento usa una elipse de área equivalente
  solo como referencia de escala.

## Little Giant (Washington, EE. UU.)

- Evento: Little Giant Fire, condado de Chelan, Washington.
- Inicio: 15/07/2026, causa natural (rayo).
- Área oficial: 172 912 acres (~69 975 ha), WFIGS/NIFC.
- `little_giant.geojson`: perímetro oficial descargado del servicio WFIGS
  (ArcGIS REST, NIFC).
- `little_giant_dem.npy`: DEM de 128×128 celdas, Terrarium/Mapzen.
- La simulación usa una subventana de 4.4 km alrededor de la ignición; el
  evento completo excede la escala del modelo.

## Reproducción

```bash
uv run python scripts/fetch_real_cases.py
uv run python scripts/run_all.py --only casos
```

Los archivos se cachean para evitar descargas repetidas. Los servicios son
públicos; respetar sus términos de uso y citar las fuentes en publicaciones.
