var picked = "";
var typing = false;

function timeText(t) {
  return new Date(t * 1000).toLocaleTimeString();
}

function send(url, data) {
  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data || {})
  }).then(update);
}

function changeText(list) {
  if (list.length < 2) return "0.0";
  var diff = Math.round((list[list.length - 1] - list[list.length - 2]) * 10) / 10;
  if (diff > 0) return "<span class='up'>+" + diff.toFixed(1) + "</span>";
  if (diff < 0) return "<span class='down'>" + diff.toFixed(1) + "</span>";
  return "0.0";
}

function showReadings(data) {
  var dev = null;
  for (var i = 0; i < data.devices.length; i++) {
    if (data.devices[i].mac == picked) dev = data.devices[i];
  }
  if (!dev) return;
  var html = "";
  var values = dev.history;
  var times = data.times;
  var count = 0;
  for (var i = values.length - 1; i >= 0 && count < 10; i--) {
    var t = times[times.length - values.length + i] || "";
    var prev = i > 0 ? values[i - 1] : values[i];
    var diff = Math.round((values[i] - prev) * 10) / 10;
    var change = diff > 0 ? "<span class='up'>+" + diff.toFixed(1) + "</span>" : diff < 0 ? "<span class='down'>" + diff.toFixed(1) + "</span>" : "0.0";
    var note = values[i] > dev.limit ? "over limit" : "";
    html += "<tr><td>" + t + "</td><td>" + values[i].toFixed(1) + "</td><td>" + change + "</td><td>" + note + "</td></tr>";
    count++;
  }
  document.getElementById("readings").innerHTML = html;
  document.getElementById("current").textContent = dev.usage.toFixed(1);
}

function showDevices(data) {
  var select = document.getElementById("pick");
  if (select.options.length == 0) {
    for (var i = 0; i < data.devices.length; i++) {
      var o = document.createElement("option");
      o.value = data.devices[i].mac;
      o.text = data.devices[i].name;
      select.appendChild(o);
    }
    picked = "B8:27:EB:33:6D:04";
    select.value = picked;
  }
  if (typing) return;

  var html = "";
  for (var i = 0; i < data.devices.length; i++) {
    var d = data.devices[i];
    var cls = "";
    var status = "Normal";
    if (d.throttled) {
      cls = "limited";
      status = "Throttled to " + data.settings.speed + " Mbps (" + d.release_in + "s left)";
    } else if (d.usage > d.limit) {
      cls = "over";
      status = "Over limit " + d.strikes + "/" + data.settings.strikes;
    }
    var button = d.throttled
      ? "<button onclick=\"send('/api/release/" + d.mac + "')\">Release</button>"
      : "<button onclick=\"send('/api/throttle/" + d.mac + "')\">Throttle</button>";
    html += "<tr class='" + cls + "'>" +
      "<td>" + d.name + "</td><td>" + d.type + "</td><td>" + d.ip + "</td><td>" + d.mac + "</td>" +
      "<td>" + d.usage.toFixed(1) + "</td><td>" + changeText(d.history) + "</td>" +
      "<td><input class='limit-box' type='number' value='" + d.limit + "' data-mac='" + d.mac + "'></td>" +
      "<td>" + status + "</td>" +
      "<td><button onclick=\"send('/api/spike/" + d.mac + "')\">Spike</button> " + button + "</td></tr>";
  }
  document.getElementById("devices").innerHTML = html;
}

function showEvents(list) {
  var html = "";
  for (var i = 0; i < list.length; i++) {
    var e = list[i];
    html += "<tr><td>" + timeText(e.time) + "</td><td>" + e.name + "</td><td><b>" + e.action + "</b></td>" +
      "<td>" + e.usage.toFixed(1) + " / " + e.usage_limit + "</td><td>" + e.detail + "</td></tr>";
  }
  if (html == "") html = "<tr><td colspan='5'>No events yet. Press Spike on a device to test.</td></tr>";
  document.getElementById("events").innerHTML = html;
}

function showSide(data) {
  var html = "";
  for (var i = 0; i < data.alerts.length; i++) {
    var a = data.alerts[i];
    html += "<div class='alert'><span>" + timeText(a.time) + " - " + a.channel + "</span><br>" + a.text + "</div>";
  }
  document.getElementById("alerts").innerHTML = html || "No alerts yet";
  document.getElementById("commands").textContent = data.commands.length ? data.commands.join("\n") : "No rules applied yet";
}

function update() {
  Promise.all([
    fetch("/api/status").then(function (r) { return r.json(); }),
    fetch("/api/events").then(function (r) { return r.json(); })
  ]).then(function (res) {
    var data = res[0];
    var throttled = 0;
    for (var i = 0; i < data.devices.length; i++) if (data.devices[i].throttled) throttled++;
    document.getElementById("mode").textContent = data.mode;
    document.getElementById("simtime").textContent = data.sim_time;
    document.getElementById("total").textContent = data.total;
    document.getElementById("count").textContent = data.devices.length;
    document.getElementById("throttled").textContent = throttled;
    document.getElementById("samples").textContent = data.samples;
    var s = data.settings;
    document.getElementById("rules").textContent = "Rules: limit " + s.limit + " Mbps per device, throttle to " + s.speed +
      " Mbps after " + s.strikes + " checks over the limit, auto release after " + s.release + " seconds.";
    showDevices(data);
    showReadings(data);
    showEvents(res[1]);
    showSide(data);
  }).catch(function () {
    document.getElementById("mode").textContent = "server stopped";
  });
}

document.getElementById("pick").onchange = function () {
  picked = this.value;
  update();
};

document.getElementById("clear").onclick = function () {
  send("/api/clear");
};

document.addEventListener("focusin", function (e) {
  if (e.target.className == "limit-box") typing = true;
});

document.addEventListener("focusout", function (e) {
  if (e.target.className == "limit-box") {
    typing = false;
    send("/api/limit/" + e.target.dataset.mac, { limit: e.target.value });
  }
});

document.addEventListener("keydown", function (e) {
  if (e.key == "Enter" && e.target.className == "limit-box") e.target.blur();
});

update();
setInterval(update, 1000);
