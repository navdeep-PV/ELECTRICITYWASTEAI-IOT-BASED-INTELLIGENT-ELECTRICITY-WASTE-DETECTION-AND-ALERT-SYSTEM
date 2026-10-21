"""
IoT-Based Intelligent Electricity Waste Detection and Alert System
Web dashboard (Flask)
"""

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)
from datetime import date

from database import (
    init_db,
    get_latest_reading,
    get_recent_readings,
    get_alerts,
    acknowledge_alert,
    get_daily_summary,
    get_hourly_power,
    get_setting,
    set_setting,
    add_reading,
    add_alert,
)

app = Flask(__name__)
app.secret_key = "electricity-waste-iot-secret-change-me"

init_db()


@app.route("/")
def index():
    latest = get_latest_reading()
    readings = get_recent_readings(60)
    alerts = get_alerts(limit=10)
    summary = get_daily_summary()
    room = get_setting("room_name", "Lab / Classroom")
    return render_template(
        "index.html",
        latest=latest,
        readings=readings,
        alerts=alerts,
        summary=summary,
        room=room,
    )


@app.route("/api/live")
def api_live():
    """JSON endpoint for live dashboard updates."""
    latest = get_latest_reading()
    alerts = get_alerts(limit=5, unacked_only=True)
    summary = get_daily_summary()
    return jsonify(
        {
            "latest": latest,
            "alerts": alerts,
            "summary": summary,
        }
    )


@app.route("/api/readings")
def api_readings():
    limit = request.args.get("limit", 100, type=int)
    return jsonify(get_recent_readings(limit))


@app.route("/api/hourly")
def api_hourly():
    day = request.args.get("day", date.today().isoformat())
    return jsonify(get_hourly_power(day))


@app.route("/alerts")
def alerts_page():
    alerts = get_alerts(limit=100)
    return render_template("alerts.html", alerts=alerts)


@app.route("/alerts/<int:alert_id>/ack", methods=["POST"])
def ack_alert(alert_id):
    acknowledge_alert(alert_id)
    flash("Alert acknowledged.", "success")
    return redirect(url_for("alerts_page"))


@app.route("/reports")
def reports():
    day = request.args.get("day", date.today().isoformat())
    summary = get_daily_summary(day)
    hourly = get_hourly_power(day)
    return render_template(
        "reports.html",
        summary=summary,
        hourly=hourly,
        day=day,
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        set_setting("room_name", request.form.get("room_name", "").strip())
        set_setting("voltage", request.form.get("voltage", "230").strip())
        set_setting(
            "waste_threshold_w",
            request.form.get("waste_threshold_w", "40").strip(),
        )
        set_setting(
            "empty_minutes",
            request.form.get("empty_minutes", "3").strip(),
        )
        flash("Settings saved.", "success")
        return redirect(url_for("settings"))

    cfg = {
        "room_name": get_setting("room_name", "Lab / Classroom 101"),
        "voltage": get_setting("voltage", "230"),
        "waste_threshold_w": get_setting("waste_threshold_w", "40"),
        "empty_minutes": get_setting("empty_minutes", "3"),
    }
    return render_template("settings.html", cfg=cfg)


@app.route("/api/ingest", methods=["POST"])
def api_ingest():
    """
    Endpoint for ESP32 (or simulator) to push sensor data.
    JSON body: { "current_a": 0.5, "power_w": 115, "occupancy": 0, "voltage_v": 230 }
    """
    data = request.get_json(force=True, silent=True) or {}
    current = float(data.get("current_a", 0))
    power = float(data.get("power_w", 0))
    occupancy = int(data.get("occupancy", 0))
    voltage = float(data.get("voltage_v", 230))

    threshold = float(get_setting("waste_threshold_w", "40"))
    waste = 1 if (occupancy == 0 and power >= threshold) else 0

    ts = add_reading(current, power, occupancy, voltage, waste)

    if waste:
        msg = (
            f"Possible electricity waste! Unoccupied room drawing {power:.0f} W."
        )
        add_alert(msg, power_w=power, occupancy=0)

    return jsonify({"ok": True, "ts": ts, "waste": waste})


if __name__ == "__main__":
    print("Electricity Waste Detection dashboard")
    print("Open http://127.0.0.1:5000")
    print("In another terminal run:  python simulate_sensors.py")
    app.run(debug=True, host="0.0.0.0", port=5000)
