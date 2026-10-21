"""
Simulate ESP32 sensor readings for demonstration without hardware.

Generates realistic current / power / occupancy patterns and
injects them into the database so the dashboard stays live.

Run in a separate terminal:
    python simulate_sensors.py
"""

import time
import random
import math
from datetime import datetime

from database import init_db, add_reading, add_alert, get_setting

# Room load profiles (watts when "on")
LOADS = {
    "lights": 120,
    "fans": 80,
    "projector": 250,
    "computers": 400,
}


def simulate_once():
    """Generate one realistic reading and decide waste flag."""
    hour = datetime.now().hour
    # Occupancy probability higher during class hours
    if 9 <= hour <= 17:
        occupied = 1 if random.random() < 0.65 else 0
    else:
        occupied = 1 if random.random() < 0.15 else 0

    # Base load
    power = 15  # standby / phantom
    active = []

    if occupied:
        # People present – some equipment on
        if random.random() < 0.9:
            power += LOADS["lights"]
            active.append("lights")
        if random.random() < 0.7:
            power += LOADS["fans"]
            active.append("fans")
        if random.random() < 0.3:
            power += LOADS["projector"]
            active.append("projector")
        if random.random() < 0.4:
            power += LOADS["computers"]
            active.append("computers")
    else:
        # Unoccupied – sometimes people forget to switch off
        if random.random() < 0.25:
            power += LOADS["lights"]
            active.append("lights (left on)")
        if random.random() < 0.15:
            power += LOADS["fans"]
            active.append("fans (left on)")
        if random.random() < 0.08:
            power += LOADS["projector"]
            active.append("projector (left on)")
        if random.random() < 0.10:
            power += LOADS["computers"]
            active.append("computers (left on)")

    # Small noise
    power += random.uniform(-8, 8)
    power = max(5, power)

    voltage = float(get_setting("voltage", "230"))
    current = power / voltage

    threshold = float(get_setting("waste_threshold_w", "40"))
    waste = 1 if (occupied == 0 and power >= threshold) else 0

    ts = add_reading(current, power, occupied, voltage, waste)

    if waste:
        msg = (
            f"Possible electricity waste detected! "
            f"Room unoccupied but drawing ~{power:.0f} W "
            f"({', '.join(active) if active else 'unknown loads'})."
        )
        add_alert(msg, power_w=power, occupancy=0)
        print(f"[{ts}] ALERT  power={power:.1f}W  occ={occupied}  {active}")
    else:
        print(f"[{ts}] OK     power={power:.1f}W  occ={occupied}  {active}")

    return power, occupied, waste


def main():
    init_db()
    print("Sensor simulator started. Sending readings every 8–12 seconds.")
    print("Press Ctrl+C to stop.\n")
    try:
        while True:
            simulate_once()
            time.sleep(random.uniform(8, 12))
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    main()
