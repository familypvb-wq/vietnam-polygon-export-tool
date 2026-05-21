# app.py

import os
import tempfile
import unicodedata

import geopandas as gpd
import pandas as pd
import streamlit as st
import folium

from streamlit_folium import st_folium
import simplekml
from shapely.geometry import Polygon, MultiPolygon

# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="Vietnam Polygon Export Tool",
    layout="wide"
)

# DATA_PATH = "data/ward_polygons.geojson"
DATA_PATH = "zip://data/ward_polygons.zip"
MAX_FEATURES = 5000

# =========================
# HELPERS
# =========================

def normalize_text(text):
    if pd.isna(text):
        return ""

    text = str(text).lower().strip()

    text = unicodedata.normalize("NFD", text)
    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )

    return text


@st.cache_data
def load_data():

    gdf = gpd.read_file(DATA_PATH)

    # normalize CRS
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)

    gdf = gdf.to_crs(epsg=4326)

    # remove invalid geometry
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.is_valid]

    # normalize column names
    gdf.columns = [c.lower() for c in gdf.columns]

    required_cols = ["provincename", "districtname", "wardname"]

    for col in required_cols:
        if col not in gdf.columns:
            raise Exception(
                f"Missing required column: {col}"
            )

    # create normalized columns
    gdf["province_norm"] = gdf["provincename"].apply(normalize_text)
    gdf["district_norm"] = gdf["districtname"].apply(normalize_text)
    gdf["ward_norm"] = gdf["wardname"].apply(normalize_text)

    return gdf


# def export_kml(gdf_export):

#     tmp_dir = tempfile.mkdtemp()

#     output_path = os.path.join(
#         tmp_dir,
#         "selected_wards.kml"
#     )

#     gdf_export.to_file(
#         output_path,
#         driver="KML"
#     )

#     return output_path

def export_kml(gdf_export):

    # ensure CRS for KML
    gdf_export = gdf_export.to_crs(epsg=4326)

    # fix invalid geometry
    gdf_export["geometry"] = gdf_export.buffer(0)

    kml = simplekml.Kml()

    for _, row in gdf_export.iterrows():

        geom = row.geometry

        name = row["wardname"]

        if geom is None:
            continue

        # =========================
        # POLYGON
        # =========================

        if isinstance(geom, Polygon):

            pol = kml.newpolygon(
                name=name,
                outerboundaryis=list(geom.exterior.coords)
            )

            # border
            pol.style.linestyle.color = simplekml.Color.blue
            pol.style.linestyle.width = 3

            # fill
            pol.style.polystyle.color = (
                simplekml.Color.changealphaint(
                    80,
                    simplekml.Color.blue
                )
            )

            pol.style.polystyle.fill = 1
            pol.style.polystyle.outline = 1

        # =========================
        # MULTIPOLYGON
        # =========================

        elif isinstance(geom, MultiPolygon):

            for polygon in geom.geoms:

                pol = kml.newpolygon(
                    name=name,
                    outerboundaryis=list(
                        polygon.exterior.coords
                    )
                )

                pol.style.linestyle.color = simplekml.Color.blue
                pol.style.linestyle.width = 3

                pol.style.polystyle.color = (
                    simplekml.Color.changealphaint(
                        80,
                        simplekml.Color.blue
                    )
                )

                pol.style.polystyle.fill = 1
                pol.style.polystyle.outline = 1

    # =========================
    # RETURN IN-MEMORY BYTES
    # =========================

    kml_string = kml.kml()

    return kml_string.encode("utf-8")


def build_map(gdf_map):

    center = [16.0, 106.0]

    if len(gdf_map) > 0:
        centroid = gdf_map.unary_union.centroid
        center = [centroid.y, centroid.x]

    m = folium.Map(
        location=center,
        zoom_start=11
    )

    folium.GeoJson(
        gdf_map.to_json(),
        tooltip=folium.GeoJsonTooltip(
            fields=["provincename", "districtname", "wardname"],
            aliases=["Province", "District", "Ward"]
        )
    ).add_to(m)

    return m


# =========================
# LOAD DATA
# =========================

try:
    gdf = load_data()

except Exception as e:
    st.error(f"Failed to load GeoJSON: {e}")
    st.stop()

# =========================
# HEADER
# =========================

st.title("🗺️ Vietnam Polygon Export Tool")
st.caption(
    "Select Province / District / Ward and export polygons to KML"
)

# =========================
# SIDEBAR
# =========================

st.sidebar.header("Filters")

# Province
province_options = sorted(
    gdf["provincename"].dropna().unique()
)

selected_provinces = st.sidebar.multiselect(
    "Province / City",
    province_options,
    default=province_options[:1]
)

# District
district_df = gdf[
    gdf["provincename"].isin(selected_provinces)
]

district_options = sorted(
    district_df["districtname"].dropna().unique()
)

selected_districts = st.sidebar.multiselect(
    "District",
    district_options,
    default=district_options[:1]
)

# Wards
ward_df = gdf[
    (gdf["provincename"].isin(selected_provinces))
    & (gdf["districtname"].isin(selected_districts))
]

ward_options = sorted(
    ward_df["wardname"].dropna().unique()
)

search_keyword = st.sidebar.text_input(
    "Search Ward"
)

if search_keyword:

    keyword_norm = normalize_text(search_keyword)

    ward_options = [
        w for w in ward_options
        if keyword_norm in normalize_text(w)
    ]

selected_wards = st.sidebar.multiselect(
    "Select Wards",
    ward_options,
    default=ward_options[:1]
)

# =========================
# FILTER DATA
# =========================

filtered = gdf[
    (gdf["provincename"].isin(selected_provinces))
    & (gdf["districtname"].isin(selected_districts))
    & (gdf["wardname"].isin(selected_wards))
]

# =========================
# STATS
# =========================

col1, col2, col3 = st.columns(3)

col1.metric(
    "Selected Provinces",
    len(selected_provinces)
)

col2.metric(
    "Selected Districts",
    len(selected_districts)
)

col3.metric(
    "Selected Wards",
    len(selected_wards)
)

# =========================
# MAP
# =========================

st.subheader("Map Preview")

if len(filtered) > 0:

    map_obj = build_map(filtered)

    st_folium(
        map_obj,
        width=1200,
        height=600
    )

else:
    st.warning("No ward selected")

# =========================
# DATA PREVIEW
# =========================

st.subheader("Selected Data")

if len(filtered) > 0:

    preview_cols = [
        "provincename",
        "districtname",
        "wardname"
    ]

    st.dataframe(
        filtered[preview_cols],
        use_container_width=True
    )

# =========================
# EXPORT
# =========================

st.subheader("Export")

if len(filtered) > 0:

    if st.button("Export KML"):

        try:

            export_gdf = filtered.copy()

            # remove helper columns
            drop_cols = [
                "province_norm",
                "district_norm",
                "ward_norm"
            ]

            export_gdf = export_gdf.drop(
                columns=[
                    c for c in drop_cols
                    if c in export_gdf.columns
                ]
            )
            if len(export_gdf) > MAX_FEATURES:
                st.error(
                    f"Too many polygons selected "
                    f"({len(export_gdf)} > {MAX_FEATURES})"
                )

                st.stop()
            kml_bytes = export_kml(export_gdf)

            st.download_button(
                label="⬇ Download KML",
                data=kml_bytes,
                file_name="selected_wards.kml",
                mime="application/vnd.google-earth.kml+xml"
            )

            st.success("KML exported successfully")

        except Exception as e:
            st.error(f"Export failed: {e}")

else:
    st.info("Select at least one ward")
    