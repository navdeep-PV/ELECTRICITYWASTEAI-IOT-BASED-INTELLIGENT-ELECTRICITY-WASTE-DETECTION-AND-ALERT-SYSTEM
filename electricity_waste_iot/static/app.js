// EnergyGuard IoT – dashboard helpers

function initDashboard(readings) {
  const canvas = document.getElementById("powerChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let data = (readings || []).map((r) => r.power_w);

  function draw() {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // grid
    ctx.strokeStyle = "#2a3548";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = (h / 4) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    if (data.length < 2) {
      ctx.fillStyle = "#8b9cb3";
      ctx.font = "14px sans-serif";
      ctx.fillText("Waiting for sensor data…", 20, h / 2);
      return;
    }

    const maxP = Math.max(...data, 50);
    const stepX = w / (data.length - 1);

    // area fill
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "rgba(59,130,246,0.35)");
    grad.addColorStop(1, "rgba(59,130,246,0)");
    ctx.beginPath();
    data.forEach((v, i) => {
      const x = i * stepX;
      const y = h - (v / maxP) * (h - 10);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // line
    ctx.beginPath();
    data.forEach((v, i) => {
      const x = i * stepX;
      const y = h - (v / maxP) * (h - 10);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2.5;
    ctx.lineJoin = "round";
    ctx.stroke();
  }

  draw();

  // Live poll every 5 s
  setInterval(async () => {
    try {
      const res = await fetch("/api/live");
      const json = await res.json();
      const latest = json.latest;
      if (!latest) return;

      // Update KPIs
      const pEl = document.getElementById("kpi-power");
      const cEl = document.getElementById("kpi-current");
      const oEl = document.getElementById("kpi-occ");
      const wEl = document.getElementById("kpi-waste");
      const wCard = document.getElementById("kpi-waste-card");

      if (pEl) pEl.innerHTML = `${Math.round(latest.power_w)} <span class="unit">W</span>`;
      if (cEl) cEl.innerHTML = `${latest.current_a.toFixed(2)} <span class="unit">A</span>`;
      if (oEl) oEl.textContent = latest.occupancy ? "Occupied" : "Empty";
      if (wEl) wEl.textContent = latest.waste_flag ? "Detected" : "Normal";
      if (wCard) wCard.classList.toggle("waste", !!latest.waste_flag);

      // Summary
      const s = json.summary || {};
      const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };
      set("sum-samples", s.samples || 0);
      set("sum-avg", `${(s.avg_power || 0).toFixed(1)} W`);
      set("sum-max", `${(s.max_power || 0).toFixed(1)} W`);
      set("sum-waste", s.waste_samples || 0);
      set("sum-kwh", s.est_kwh || 0);

      // Chart data
      data.push(latest.power_w);
      if (data.length > 60) data.shift();
      draw();

      // Alerts
      const list = document.getElementById("alert-list");
      if (list && json.alerts && json.alerts.length) {
        list.innerHTML = json.alerts
          .slice(0, 5)
          .map(
            (a) => `
          <li class="${a.acknowledged ? "" : "unacked"}">
            <span class="alert-ts">${(a.ts || "").slice(11, 19)}</span>
            <span class="alert-msg">${a.message}</span>
            ${a.power_w ? `<span class="alert-meta">${Math.round(a.power_w)} W</span>` : ""}
          </li>`
          )
          .join("");
        const empty = document.getElementById("alert-empty");
        if (empty) empty.remove();
      }
    } catch (e) {
      console.warn("Live update failed", e);
    }
  }, 5000);
}

// Flash auto-dismiss
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });
});
