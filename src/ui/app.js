let currentDriverId = null;
let db = null;
let startDate = "";
let endDate = "";

new QWebChannel(qt.webChannelTransport, function (channel) {
  db = channel.objects.db;
  loadDrivers();
});

function loadDrivers() {
  db.get_drivers().then((driversJson) => {
    const drivers = JSON.parse(driversJson);
    const driverList = document.getElementById("driver-list");
    driverList.innerHTML = "";
    drivers.forEach((driver) => {
      const li = document.createElement("li");
      li.textContent = driver.name;
      li.dataset.id = driver.id;
      li.addEventListener("click", () => selectDriver(driver.id, li));
      driverList.appendChild(li);
    });
    if (drivers.length > 0) {
      selectDriver(drivers[0].id, driverList.firstChild);
    }
  });
}

function selectDriver(driverId, element) {
  currentDriverId = driverId;
  document
    .querySelectorAll(".driver-list li")
    .forEach((li) => li.classList.remove("active"));
  element.classList.add("active");
  loadShifts();
  loadSummary();
}

function loadShifts() {
  if (!currentDriverId) return;
  db.get_shifts(currentDriverId, startDate, endDate).then((shiftsJson) => {
    const shifts = JSON.parse(shiftsJson);
    const table = document.getElementById("shift-table");
    table.innerHTML = "";
    shifts.forEach((shift) => {
      const row = document.createElement("tr");
      row.innerHTML = `
                <td>${shift.date}</td>
                <td>${shift.start}</td>
                <td>${shift.end}</td>
                <td>${shift.mileage}</td>
                <td class="green">${shift.cash}</td>
                <td class="green">${shift.credit}</td>
                <td class="${shift.owed.startsWith("-") ? "red" : "green"}">${shift.owed}</td>
                <td>${shift.hourly}</td>
            `;
      table.appendChild(row);
    });
  });
}

function loadSummary() {
  if (!currentDriverId) return;
  db.get_summary(currentDriverId, startDate, endDate).then((summaryJson) => {
    const summary = JSON.parse(summaryJson);
    const cards = document.getElementById("summary-cards");
    cards.innerHTML = `
            <div class="card green">Total Mileage<br><strong>${summary.total_mileage.toFixed(1)}</strong></div>
            <div class="card green">Cash Tips<br><strong>$${summary.total_cash.toFixed(2)}</strong></div>
            <div class="card green">Credit Tips<br><strong>$${summary.total_credit.toFixed(2)}</strong></div>
            <div class="card ${summary.total_owed < 0 ? "red" : "green"}">Owed<br><strong>$${summary.total_owed.toFixed(2)}</strong></div>
            <div class="card green">Avg Hourly<br><strong>$${summary.avg_hourly.toFixed(2)}</strong></div>
        `;
  });
}

document.getElementById("search-btn").addEventListener("click", () => {
  startDate = document.getElementById("start-date").value;
  endDate = document.getElementById("end-date").value;
  loadShifts();
  loadSummary();
});

document.getElementById("add-shift-btn").addEventListener("click", () => {
  console.log("Add shift clicked");
});

// TODO: edit and delete
