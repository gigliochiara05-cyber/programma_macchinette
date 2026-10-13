#!/usr/bin/env python3
"""
T2024 Mock Vending Machine Server
Simula il firmware della macchinetta T2024 per testare t2024.py in locale senza hardware fisico.
Non richiede dipendenze esterne (usa la libreria standard di Python).
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import sys

PRODUCTS = [
    {"id": 1, "slot": "A0", "name": "Espresso Classico", "price_cents": 50, "stock": 5, "active": True},
    {"id": 2, "slot": "A1", "name": "Caffe Macchiato", "price_cents": 60, "stock": 4, "active": True},
    {"id": 3, "slot": "B0", "name": "Acqua Naturale 500ml", "price_cents": 100, "stock": 10, "active": True},
    {"id": 4, "slot": "B1", "name": "Acqua Frizzante 500ml", "price_cents": 100, "stock": 8, "active": True},
    {"id": 5, "slot": "C0", "name": "Patatine Classiche", "price_cents": 120, "stock": 6, "active": True},
    {"id": 6, "slot": "C1", "name": "Taralli Pugliesi", "price_cents": 110, "stock": 5, "active": True},
    {"id": 7, "slot": "C2", "name": "Barretta Cioccolato", "price_cents": 150, "stock": 7, "active": True},
    {"id": 8, "slot": "D0", "name": "Coca Cola 330ml", "price_cents": 180, "stock": 4, "active": True},
    {"id": 9, "slot": "D1", "name": "Te al Limone 330ml", "price_cents": 160, "stock": 5, "active": True},
    {"id": 10, "slot": "D2", "name": "Succo Arancia 200ml", "price_cents": 140, "stock": 3, "active": True},
]

STATE = {
    "temperature": 4.2,
    "credit_cents": 0,
    "tray_locked": True,
    "fleet_online": True,
    "logs": ["SYSTEM BOOT OK", "FIRMWARE v3.2.14 READY"],
}

class MockVendingHandler(BaseHTTPRequestHandler):
    def _send_text(self, text, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/":
            self._send_text("T2024 Vending Machine Controller Online - Firmware v3.2.14\n")
            return

        if path == "/api/product/all":
            self._send_json(PRODUCTS)
            return

        if path.startswith("/api/product/"):
            try:
                pid = int(path.split("/")[-1])
                prod = next((p for p in PRODUCTS if p["id"] == pid), None)
                if prod:
                    self._send_json(prod)
                else:
                    self._send_json({"error": "Not found"}, 404)
            except Exception:
                self._send_json({"error": "Invalid ID"}, 400)
            return

        if path == "/debug":
            cmd_list = query.get("cmd", [""])
            cmd_str = cmd_list[0]
            parts = cmd_str.split()
            cmd = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []

            print(f"[*] /debug CMD: '{cmd_str}'")

            if cmd == "fw":
                self._send_text("T2024 v3.2.14")
            elif cmd == "session":
                self._send_text("Session ID: f8a2c91e (Authorized)")
            elif cmd == "temp":
                self._send_text(f"Temp: {STATE['temperature']} C (Normal)")
            elif cmd == "coil":
                target = args[0] if args else "5"
                STATE["temperature"] = float(target)
                self._send_text(f"Coil target set to {target} C")
            elif cmd == "gpio":
                pin = args[0] if len(args) > 0 else "?"
                lvl = args[1] if len(args) > 1 else "?"
                self._send_text(f"GPIO {pin} set to {lvl}")
            elif cmd == "adc":
                pin = args[0] if args else "0"
                self._send_text("0")  # 0 = item detected in tray
            elif cmd == "write":
                self._send_text(f"EEPROM write OK at {args[0] if args else '0x0000'}")
            elif cmd == "read":
                self._send_text(f"00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F")
            elif cmd == "checksum":
                self._send_text("CRC32: 0x9B41C204 OK")
            elif cmd == "display":
                slot = args[0] if args else "all"
                text = " ".join(args[1:]) if len(args) > 1 else ""
                self._send_text(f"Display {slot} refreshed ({text})")
            elif cmd == "hw_log_clear":
                STATE["logs"].clear()
                self._send_text("HW logs cleared")
            elif cmd in ("sales_log_clear", "log_clear_debug", "log_flush"):
                self._send_text(f"{cmd} OK")
            elif cmd == "coin_load":
                self._send_text(f"Coin loaded: {args}")
            elif cmd == "coin_drain":
                self._send_text("Coins drained to cashbox")
            elif cmd == "coin_report":
                self._send_text("Coin inventory: 10c: 20 | 20c: 15 | 50c: 10 | 1e: 12 | 2e: 5")
            elif cmd == "tray_unlock":
                STATE["tray_locked"] = (args[0] == "0") if args else False
                self._send_text(f"Tray unlocked: {not STATE['tray_locked']}")
            elif cmd == "fleet_offline":
                STATE["fleet_online"] = False
                self._send_text("Fleet telemetry offline")
            elif cmd == "fleet_online":
                STATE["fleet_online"] = True
                self._send_text("Fleet telemetry online")
            elif cmd == "reboot":
                self._send_text("System rebooting in 3s...")
            elif cmd == "factory_erase":
                self._send_text("Factory erase initiated")
            else:
                self._send_text(f"ACK: {cmd_str}")
            return

        self._send_text("Not Found", 404)

    def log_message(self, format, *args):
        # silenzia log di default per pulizia o stampa sintetica
        sys.stderr.write(f"[MOCK HTTP] {self.address_string()} - {format % args}\n")

def run(port=8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, MockVendingHandler)
    print("=" * 60)
    print(f"  T2024 Mock Vending Machine Server avviato!")
    print(f"  In ascolto su: http://localhost:{port}")
    print(f"  Premi Ctrl+C per fermare il server.")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer arrestato.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run(port)
