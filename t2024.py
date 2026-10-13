#!/usr/bin/env python3
"""T2024 Vending Machine Controller — 10.4.2.120"""
import requests, time, sys, random, os

BASE = os.getenv("T2024_HOST", "http://10.4.2.120:8080")

class T2024:
    def __init__(self, base=BASE):
        self.base = base
        self.s = requests.Session()

    def exec(self, cmd):
        r = self.s.get(f"{self.base}/debug", params={"cmd": cmd.replace(" ", "%20")})
        return r.text.strip()

    def gpio(self, pin, level):
        return self.exec(f"gpio {pin} {level}")

    def slot_to_index(self, slot):
        return (ord(slot[0].upper()) - ord('A')) * 10 + int(slot[1])

    def slot_addr(self, slot):
        return f"0x{0x400 + self.slot_to_index(slot) * 16:04X}"

    def slot_sol_pin(self, slot):
        return 20 + int(slot[1])

    def slot_sensor_pin(self, slot):
        return 30 + (ord(slot[0].upper()) - ord('A')) * 10 + int(slot[1])

    def motor(self, slot, ms, direction=1):
        self.gpio(19, direction)
        self.gpio(18, 1)
        time.sleep(ms / 1000.0)
        self.gpio(18, 0)
        return f"Motor {slot}: {ms}ms dir={'CW' if direction else 'CCW'}"

    def solenoid(self, slot, ms=400):
        pin = self.slot_sol_pin(slot)
        self.gpio(pin, 1)
        time.sleep(ms / 1000.0)
        self.gpio(pin, 0)
        return f"Solenoid {slot}: {ms}ms"

    def dispense(self, slot, advance_ms=1500, sol_ms=400):
        self.gpio(19, 1)
        self.gpio(18, 1)
        time.sleep(advance_ms / 1000.0)
        self.gpio(18, 0)
        time.sleep(0.3)
        pin = self.slot_sol_pin(slot)
        self.gpio(pin, 1)
        time.sleep(sol_ms / 1000.0)
        self.gpio(pin, 0)
        return f"Dispensed {slot}"

    def dispense_random(self):
        prods = self.s.get(f"{self.base}/api/product/all").json()
        active = [p for p in prods if p["active"] and p["stock"] >= 3]
        p = random.choice(active)
        print(f"Target: {p['name']} ({p['slot']}, stock {p['stock']})")
        orig_stock = p["stock"]
        result = self.dispense(p["slot"])
        # Restore stock
        addr = self.slot_addr(p["slot"])
        self.exec(f"write {p['slot']}0000000000000000".replace(" ", ""))  # dummy
        self.eeprom_write(addr + "2", f"{orig_stock:02X}")
        # Clear hw log
        self.exec("hw_log_clear")
        # Refresh display
        self.exec(f"display {p['slot']}")
        print(result)
        print(f"Stock restored to {orig_stock}. Log cleared. Display refreshed.")
        return p["slot"]

    def eeprom_write(self, addr, data):
        return self.exec(f"write {addr} {data}")

    def eeprom_read(self, addr, length=16):
        return self.exec(f"read {addr} {length}")

    def tray_sensor(self, slot):
        pin = self.slot_sensor_pin(slot)
        return self.exec(f"adc {pin}")

    def set_price(self, product_id, cents):
        prods = self.s.get(f"{self.base}/api/product/all").json()
        p = next((x for x in prods if x["id"] == product_id), None)
        if not p: return f"Not found: {product_id}"
        addr = self.slot_addr(p["slot"])
        self.eeprom_write(addr + "3", f"{cents:04X}")
        self.exec(f"display {p['slot']}")
        return f"{p['name']} → €{cents/100:.2f}"

    def set_all_prices(self, cents):
        prods = self.s.get(f"{self.base}/api/product/all").json()
        for p in prods:
            addr = self.slot_addr(p["slot"])
            self.eeprom_write(addr + "3", f"{cents:04X}")
        self.exec("display all")
        return f"All {len(prods)} → €{cents/100:.2f}"

    def set_stock(self, slot, count):
        addr = self.slot_addr(slot)
        self.eeprom_write(addr + "2", f"{count:02X}")
        return f"Stock {slot} → {count}"

    def set_credit(self, cents):
        self.eeprom_write("0x0F00", f"{cents:04X}")
        return f"Credit → €{cents/100:.2f}"

    def coin_load(self, val, count):
        return self.exec(f"coin_load {val} {count}")

    def coin_drain(self):
        return self.exec("coin_drain")

    def coin_report(self):
        return self.exec("coin_report")

    def display_text(self, slot, text):
        return self.exec(f"display {slot} {text}")

    def display_off(self):
        return self.exec("display off")

    def display_refresh_all(self):
        return self.exec("display all")

    def temperature(self):
        return self.exec("temp")

    def coil_temp(self, t):
        return self.exec(f"coil {t}")

    def unlock_back(self):
        return self.exec("tray_unlock 1")

    def lock_back(self):
        return self.exec("tray_unlock 0")

    def fleet_off(self):
        return self.exec("fleet_offline")

    def fleet_on(self):
        return self.exec("fleet_online")

    def reboot(self):
        return self.exec("reboot")

    def factory_reset(self):
        return self.exec("factory_erase 1")

    def clear_logs(self):
        self.exec("sales_log_clear")
        self.exec("hw_log_clear")
        self.exec("log_clear_debug")
        self.exec("log_flush")
        return "All logs cleared"

    def checksum(self):
        return self.exec("checksum 0x0000 0xFFFF")

    def firmware_version(self):
        return self.exec("fw")

    def products(self):
        return self.s.get(f"{self.base}/api/product/all").json()


def main():
    m = T2024()
    if len(sys.argv) < 2:
        print("T2024 Controller — usage:")
        print("  random | dispense SLOT | advance SLOT MS | push SLOT")
        print("  price ID CENTS | all_price CENTS | stock SLOT N")
        print("  credit CENTS | coin_load VAL CNT | coin_drain | coin_report")
        print("  text SLOT TEXT | display_off | display_all")
        print("  temp | coil TEMP | unlock | lock")
        print("  fleet_off | fleet_on | reboot | factory | clean | check")
        print("  list | session | raw CMD | eeprom_read ADDR LEN | eeprom_write ADDR HEX")
        return

    cmd = sys.argv[1]
    a = sys.argv[2:] if len(sys.argv) > 2 else []

    dispatch = {
        "random":       lambda: m.dispense_random(),
        "dispense":     lambda: m.dispense(a[0] if a else "A0"),
        "advance":      lambda: m.motor(a[0] if a else "A0", int(a[1]) if len(a)>1 else 1500),
        "push":         lambda: m.solenoid(a[0] if a else "A0"),
        "price":        lambda: m.set_price(int(a[0]), int(a[1])),
        "all_price":    lambda: m.set_all_prices(int(a[0])),
        "stock":        lambda: m.set_stock(a[0], int(a[1])),
        "credit":       lambda: m.set_credit(int(a[0])),
        "coin_load":    lambda: m.coin_load(int(a[0]), int(a[1])),
        "coin_drain":   lambda: m.coin_drain(),
        "coin_report":  lambda: m.coin_report(),
        "text":         lambda: m.display_text(a[0], a[1] if len(a)>1 else ""),
        "display_off":  lambda: m.display_off(),
        "display_all":  lambda: m.display_refresh_all(),
        "temp":         lambda: m.temperature(),
        "coil":         lambda: m.coil_temp(int(a[0]) if a else 5),
        "unlock":       lambda: m.unlock_back(),
        "lock":         lambda: m.lock_back(),
        "fleet_off":    lambda: m.fleet_off(),
        "fleet_on":     lambda: m.fleet_on(),
        "reboot":       lambda: m.reboot(),
        "factory":      lambda: m.factory_reset(),
        "clean":        lambda: m.clear_logs(),
        "check":        lambda: (print("FW:", m.firmware_version()),
                                 print("Temp:", m.temperature()),
                                 print("Checksum:", m.checksum())),
        "list":         lambda: [print(f"{p['id']:<4} {p['slot']:<3} {p['name']:<25} €{p['price_cents']/100:.2f} stk:{p['stock']}") for p in m.products()],
        "session":      lambda: m.exec("session"),
        "raw":          lambda: m.exec(" ".join(a)),
        "eeprom_read":  lambda: m.eeprom_read(a[0], int(a[1]) if len(a)>1 else 16),
        "eeprom_write": lambda: m.eeprom_write(a[0], a[1]),
    }

    if cmd in dispatch:
        result = dispatch[cmd]()
        if result:
            print(result)
    else:
        print(f"Unknown: {cmd}")

if __name__ == "__main__":
    main()
