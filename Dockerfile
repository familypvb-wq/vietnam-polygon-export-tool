# --- Stage 1: Dùng container này để pull data thật từ LFS ---
FROM alpine/git:v2.43.0 AS lfs-fetcher
WORKDIR /src
RUN apk add --no-cache git-lfs
COPY . .
# Ép Git LFS pull dữ liệu thật 165MB về thay thế file con trỏ
RUN git lfs pull

# --- Stage 2: Container chạy app Streamlit thực tế ---
FROM python:3.10-slim
WORKDIR /app

# Cài đặt các thư viện hệ thống cần cho Geopandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code từ máy local
COPY app.py .
# NHƯNG thư mục data thì lấy từ Stage 1 (nơi đã có file thật 165MB)
COPY --from=lfs-fetcher /src/data ./data

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]