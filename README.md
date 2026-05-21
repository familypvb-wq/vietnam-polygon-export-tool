# Vietnam Polygon Export Tool

A lightweight internal GIS tool for selecting Vietnam administrative polygons from GeoJSON and exporting them as KML files.

Built with Streamlit + GeoPandas.

---

## Features

- Select multiple Provinces / Districts / Wards
- Interactive map preview
- Search wards with Vietnamese accent-insensitive matching
- Export polygons to `.kml`
- Polygon fill color support
- In-memory KML export (no temp file leak)
- CRS normalization (`EPSG:4326`)
- Geometry validation
- Docker-ready
- Coolify-ready
- Resource limits & healthcheck support

---

## Tech Stack

- Python
- Streamlit
- GeoPandas
- Folium
- SimpleKML
- Docker

---

## Screenshots

### Map Preview

![preview](screenshots/preview.png)

### Exported KML

![export](screenshots/export.png)

---

## Requirements

- Python 3.11+
- GDAL dependencies
- Docker (optional)

---

## GeoJSON Schema

The GeoJSON file must contain:

| Column | Description |
|---|---|
| provinceName | Province / City |
| districtName | District |
| wardName | Ward |
| geometry | Polygon geometry |

Example:

```json
{
  "provinceName": "Hồ Chí Minh",
  "districtName": "Quận 1",
  "wardName": "Bến Nghé"
}
```

---

## Installation

### Local

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

### Docker

```bash
docker compose up -d
```

---

## Access

```text
http://localhost:8501
```

---

## Production Deployment

Recommended:
- Docker
- Coolify
- Nginx reverse proxy

---

## Healthcheck

Streamlit health endpoint:

```text
/_stcore/health
```

Example:

```bash
curl http://localhost:8501/_stcore/health
```

---

## Resource Limits

Example Docker Compose config:

```yaml
mem_limit: 1g
mem_reservation: 512m
cpus: "1.0"
```

---

## Security Recommendations

- Use read-only filesystem
- Enable reverse proxy
- Add authentication if public
- Limit export size

---

## Export Protection

The app limits maximum polygon export count:

```python
MAX_FEATURES = 5000
```

This helps prevent:
- OOM
- Huge KML exports
- Server overload


---

## License

MIT