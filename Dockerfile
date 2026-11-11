# Base image Python yang ringan dan stabil
FROM python:3.11-alpine

# Set environment variable agar log langsung tercetak tanpa buffer
ENV PYTHONUNBUFFERED=1

# Tentukan direktori kerja di dalam kontainer
WORKDIR /app

# Salin script aplikasi backend
COPY app.py .

# Buat direktori default untuk Named Volume jika belum ada
RUN mkdir -p /var/lib/lab-inventory-data

# Port default yang digunakan oleh backend
EXPOSE 5000

# Jalankan service backend Python
CMD ["python", "app.py"]
