# IoT-Based Intelligent Electricity Waste Detection and Alert System

Monitors electricity usage in a classroom, laboratory or small room and detects possible energy wastage when equipment is left running while the room is unoccupied.

## Features

- Real-time power & current monitoring
- Occupancy-based waste detection
- Alert notifications with acknowledge workflow
- Energy usage dashboard with live chart
- Daily consumption reports (hourly breakdown)
- Configurable thresholds
- ESP32 firmware (Arduino) + optional relay control
- Full software simulation (no hardware required for demo)

## Project Structure

```
electricity_waste_iot/
├── app.py                          # Flask web dashboard
├── database.py                     # SQLite helpers
├── simulate_sensors.py             # Software sensor simulator
├── requirements.txt
├── README.md
├── data/                           # SQLite DB
├── models/                         # Reserved
├── outputs/                        # Reserved
├── firmware/
│   └── electricity_monitor/
│       └── electricity_monitor.ino # ESP32 Arduino sketch
├── static/
│   ├── style.css
│   └── app.js
└── templates/
    ├── base.html
    ├── index.html
    ├── alerts.html
    ├── reports.html
    └── settings.html
```

## How to Run (Demo – no hardware)

```bash
pip install -r requirements.txt
python app.py
```

In a **second terminal**:

```bash
python simulate_sensors.py
```

Open **http://127.0.0.1:5000**

The simulator generates realistic occupancy + power readings every ~10 seconds and will trigger waste alerts when the room is empty but loads remain on.

## Hardware Setup (optional)

| Component              | Role                          | ESP32 Pin |
|------------------------|-------------------------------|-----------|
| ACS712 / SCT-013       | Current sensing               | GPIO 34   |
| HC-SR501 PIR           | Occupancy / motion            | GPIO 27   |
| Relay module (optional)| Cut selected loads            | GPIO 26   |

1. Open `firmware/electricity_monitor/electricity_monitor.ino` in Arduino IDE.
2. Install ESP32 board support + libraries: `ArduinoJson`, `WiFi`, `HTTPClient`.
3. Set your Wi-Fi SSID/password and the PC’s IP in `SERVER_URL`.
4. Flash to ESP32. The device POSTs JSON to `/api/ingest`.

**Safety note:** Use properly rated, isolated monitoring hardware and qualified supervision when working with mains electricity. A low-voltage / CT-based prototype is recommended for student demonstrations.

## How Waste Detection Works

1. Sensors (or simulator) report `power_w` and `occupancy`.
2. If `occupancy == 0` and `power_w >= threshold` (default 40 W) → waste flag is set.
3. An alert is stored and shown on the dashboard.
4. Optional relay can switch off selected loads (commented out in firmware for safety).

## Technologies

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Hardware     | ESP32, current sensor, PIR          |
| Firmware     | Arduino C/C++                       |
| Backend      | Python + Flask                      |
| Database     | SQLite                              |
| Frontend     | HTML, CSS, JavaScript (live chart)  |
| Communication| Wi-Fi (HTTP JSON)                   |

## Objectives Met

- Reduce unnecessary electricity consumption
- Monitor usage in real time
- Detect possible energy wastage
- Encourage energy-efficient practices

## License

Educational / campus project use.
