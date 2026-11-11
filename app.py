#!/usr/bin/env python3
"""
Backend Service - Inventaris Barang Laboratorium (Lab Inventory Catalog)
Cloud Computing Chunin Exam - Telkom University

Spesifikasi:
- REST API berbasis JSON (GET, POST, DELETE /inventory dan alias /messages)
- Python standard library (tanpa framework berat)
- Data disimpan ke file JSON di dalam Docker Named Volume (lab-inventory-data)
- Robust error handling: 200, 201, 400, 404, 500
"""

import os
import json
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import threading

# Konfigurasi Storage Path dari Environment Variable (Docker Named Volume)
# Default ke Named Volume path: /var/lib/lab-inventory-data/inventory.json
DATA_PATH = os.environ.get("DATA_PATH", "/var/lib/lab-inventory-data/inventory.json")
PORT = int(os.environ.get("PORT", 5000))

# Thread lock untuk memastikan konkurensi aman saat baca/tulis file JSON
file_lock = threading.Lock()

# Data awal (seed data) jika berkas inventory.json belum ada
INITIAL_INVENTORY = [
    {
        "id": 1,
        "nama_alat": "Mikrotik RouterBoard RB750Gr3",
        "kategori": "Jaringan & Routing",
        "jumlah": 8,
        "kondisi": "Tersedia",
        "peminjam": "-",
        "lokasi_rak": "Rak Jaringan A1",
        "tanggal_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 2,
        "nama_alat": "Modem Telkomsel Orbit Star 2",
        "kategori": "Modem & Wireless",
        "jumlah": 3,
        "kondisi": "Tersedia",
        "peminjam": "-",
        "lokasi_rak": "Rak Wireless B2",
        "tanggal_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 3,
        "nama_alat": "Switch Cisco Catalyst 2960 24-Port",
        "kategori": "Jaringan & Switch",
        "jumlah": 2,
        "kondisi": "Dipinjam",
        "peminjam": "Praktikum Jarkom Shift 2",
        "lokasi_rak": "Meja Praktikum 3",
        "tanggal_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 4,
        "nama_alat": "Kabel UTP Cat6 Belden (Roll 50m)",
        "kategori": "Kabel & Aksesoris",
        "jumlah": 4,
        "kondisi": "Tersedia",
        "peminjam": "-",
        "lokasi_rak": "Gudang Alat C1",
        "tanggal_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 5,
        "nama_alat": "Crimping Tool RJ45 Heavy Duty",
        "kategori": "Peralatan & Perkakas",
        "jumlah": 6,
        "kondisi": "Tersedia",
        "peminjam": "-",
        "lokasi_rak": "Kotak Perkakas P1",
        "tanggal_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]


def ensure_storage_ready():
    """Memastikan direktori dan berkas inventory.json siap digunakan."""
    with file_lock:
        dir_path = os.path.dirname(DATA_PATH)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"[STORAGE] Direktori storage dibuat: {dir_path}")

        if not os.path.exists(DATA_PATH):
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(INITIAL_INVENTORY, f, indent=2, ensure_ascii=False)
            print(f"[STORAGE] Berkas {DATA_PATH} diinisialisasi dengan data awal ({len(INITIAL_INVENTORY)} item).")


def load_inventory():
    """Membaca daftar inventaris dari berkas JSON."""
    ensure_storage_ready()
    with file_lock:
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ERROR] Gagal membaca storage: {e}")
            return []


def save_inventory(items):
    """Menyimpan daftar inventaris ke berkas JSON secara aman."""
    ensure_storage_ready()
    with file_lock:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)


class InventoryRequestHandler(BaseHTTPRequestHandler):
    """Handler HTTP REST API untuk Inventaris Laboratorium."""

    def _set_headers(self, status_code=200, content_type="application/json"):
        """Mengirim status code dan CORS headers."""
        self.send_response(status_code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        # CORS Headers agar frontend dapat berkomunikasi tanpa kendala origin
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        """Menangani CORS pre-flight request."""
        self._set_headers(204)

    def _send_json(self, status_code, payload):
        """Helper untuk serialisasi dan mengirim respons JSON."""
        self._set_headers(status_code, "application/json")
        response_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.wfile.write(response_bytes)

    def do_GET(self):
        """
        Menangani HTTP GET:
        - /health: Health check service
        - /inventory & /messages: Ambil daftar seluruh katalog inventaris alat
        """
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        if not path:
            path = "/"

        # 1. Health check endpoint untuk Docker & Jenkins Health Check stage
        if path == "/health":
            items = load_inventory()
            self._send_json(200, {
                "status": "UP",
                "service": "lab-inventory-backend",
                "storage_path": DATA_PATH,
                "total_items": len(items),
                "timestamp": datetime.now().isoformat()
            })
            return

        # 2. Endpoint Katalog Inventaris: /inventory atau /messages (sesuai panduan tugas)
        if path in ("/inventory", "/messages", "/"):
            items = load_inventory()
            self._send_json(200, {
                "success": True,
                "total": len(items),
                "data": items
            })
            return

        # 404 jika route tidak ditemukan
        self._send_json(404, {
            "success": False,
            "error": f"Endpoint '{path}' tidak ditemukan. Gunakan GET /inventory atau GET /health."
        })

    def do_POST(self):
        """
        Menangani HTTP POST:
        - /inventory & /messages: Tambah alat/barang baru ke katalog laboratorium
        """
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.rstrip("/")

        if path not in ("/inventory", "/messages"):
            self._send_json(404, {
                "success": False,
                "error": f"Endpoint POST '{path}' tidak ditemukan. Gunakan POST /inventory."
            })
            return

        # Baca body request
        content_length = self.headers.get("Content-Length")
        if not content_length:
            self._send_json(400, {
                "success": False,
                "error": "Header Content-Length tidak ditemukan atau body kosong."
            })
            return

        try:
            length = int(content_length)
            raw_body = self.rfile.read(length).decode("utf-8")
            body_data = json.loads(raw_body)
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json(400, {
                "success": False,
                "error": f"Format JSON tidak valid: {str(e)}"
            })
            return

        # Validasi input: nama alat wajib diisi
        nama_alat = body_data.get("nama_alat") or body_data.get("item_name") or body_data.get("name")
        if not nama_alat or not str(nama_alat).strip():
            self._send_json(400, {
                "success": False,
                "error": "Field 'nama_alat' (atau 'item_name') wajib diisi dan tidak boleh kosong."
            })
            return

        # Validasi jumlah
        raw_jumlah = body_data.get("jumlah", body_data.get("quantity", 1))
        try:
            jumlah = int(raw_jumlah)
            if jumlah < 0:
                raise ValueError()
        except (ValueError, TypeError):
            self._send_json(400, {
                "success": False,
                "error": "Field 'jumlah' harus berupa angka integer non-negatif."
            })
            return

        items = load_inventory()

        # Generate ID baru berdasarkan ID tertinggi + 1
        new_id = (max([item.get("id", 0) for item in items]) + 1) if items else 1

        new_item = {
            "id": new_id,
            "nama_alat": str(nama_alat).strip(),
            "kategori": str(body_data.get("kategori", body_data.get("category", "Peralatan Umum"))).strip(),
            "jumlah": jumlah,
            "kondisi": str(body_data.get("kondisi", body_data.get("status", "Tersedia"))).strip(),
            "peminjam": str(body_data.get("peminjam", body_data.get("borrower", "-"))).strip(),
            "lokasi_rak": str(body_data.get("lokasi_rak", body_data.get("location", "Lab Utama"))).strip(),
            "tanggal_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        items.append(new_item)
        save_inventory(items)

        print(f"[POST] Berhasil menambahkan alat: {new_item['nama_alat']} (Index: {len(items)-1})")
        self._send_json(201, {
            "success": True,
            "message": "Alat laboratorium berhasil ditambahkan.",
            "index": len(items) - 1,
            "item": new_item
        })

    def do_DELETE(self):
        """
        Menangani HTTP DELETE:
        - /inventory?index=X atau /messages?index=X
        Menghapus alat laboratorium berdasarkan index urutan.
        """
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.rstrip("/")

        if path not in ("/inventory", "/messages"):
            self._send_json(404, {
                "success": False,
                "error": f"Endpoint DELETE '{path}' tidak ditemukan. Gunakan DELETE /inventory?index=X."
            })
            return

        # Parse query parameter index
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if "index" not in query_params:
            self._send_json(400, {
                "success": False,
                "error": "Parameter query 'index' wajib disertakan. Contoh: DELETE /inventory?index=0"
            })
            return

        index_str = query_params["index"][0]
        try:
            target_index = int(index_str)
        except ValueError:
            self._send_json(400, {
                "success": False,
                "error": f"Nilai index '{index_str}' tidak valid. Index harus berupa angka bulat (integer)."
            })
            return

        items = load_inventory()

        # Validasi rentang index (404 jika di luar bounds)
        if target_index < 0 or target_index >= len(items):
            self._send_json(404, {
                "success": False,
                "error": f"Item pada index {target_index} tidak ditemukan. Rentang index valid saat ini: 0 hingga {len(items)-1}."
            })
            return

        # Hapus item pada index tersebut
        removed_item = items.pop(target_index)
        save_inventory(items)

        print(f"[DELETE] Berhasil menghapus item pada index {target_index}: {removed_item.get('nama_alat')}")
        self._send_json(200, {
            "success": True,
            "message": f"Item '{removed_item.get('nama_alat')}' pada index {target_index} berhasil dihapus.",
            "deleted_index": target_index,
            "deleted_item": removed_item,
            "remaining_items": len(items)
        })

    def log_message(self, format, *args):
        """Format logging standar ke stdout."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.address_string()} - {format % args}")


def run(server_class=ThreadingHTTPServer, handler_class=InventoryRequestHandler, port=PORT):
    """Menjalankan HTTP server."""
    ensure_storage_ready()
    server_address = ("0.0.0.0", port)
    httpd = server_class(server_address, handler_class)
    print("=" * 65)
    print("  LAB INVENTORY CATALOG BACKEND SERVICE (PYTHON)")
    print(f"  Listening on: http://0.0.0.0:{port}")
    print(f"  Storage Path: {DATA_PATH}")
    print(f"  Endpoints   : GET /inventory, POST /inventory, DELETE /inventory?index=X")
    print(f"                GET /health")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Menghentikan server...")
        httpd.server_close()


if __name__ == "__main__":
    run()
