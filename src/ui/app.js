let currentDriverId = null;
let db = null;
let startDate = "";
let endDate = "";

console.log("App.js loaded");

new QWebChannel(qt.webChannelTransport, function (channel) {
  db = channel.objects.db;
  console.log("QWebChannel ready");
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
  document.getElementById("modal-driver-name").textContent =
    element.textContent;
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
                <td><input type="checkbox" data-id="${shift.id}"></td>
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
  document.getElementById("modal-driver-name").textContent =
    document.querySelector(".driver-list .active").textContent;
  document.getElementById("add-shift-modal").style.display = "block";
});

document.getElementById("add-shift-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const date = document.getElementById("shift-date").value;
  const start = document.getElementById("shift-start").value;
  const end = document.getElementById("shift-end").value;
  const mileage = parseFloat(document.getElementById("shift-mileage").value);
  const cash = parseFloat(document.getElementById("shift-cash").value);
  const credit = parseFloat(document.getElementById("shift-credit").value);
  const owed = parseFloat(document.getElementById("shift-owed").value);
  const hourly = parseFloat(document.getElementById("shift-hourly").value);
  db.add_shift(
    currentDriverId,
    date,
    start,
    end,
    mileage,
    cash,
    credit,
    owed,
    hourly,
  );
  document.getElementById("add-shift-modal").style.display = "none";
  document.getElementById("add-shift-form").reset();
  loadShifts();
  loadSummary();
});

document.getElementById("cancel-add").addEventListener("click", () => {
  document.getElementById("add-shift-modal").style.display = "none";
  document.getElementById("add-shift-form").reset();
});

document.getElementById("delete-shift-btn").addEventListener("click", () => {
  const checkboxes = document.querySelectorAll(
    '#shift-table input[type="checkbox"]:checked',
  );
  if (checkboxes.length === 0) {
    alert("Please select at least one shift to delete.");
    return;
  }
  if (
    confirm(`Are you sure you want to delete ${checkboxes.length} shift(s)?`)
  ) {
    checkboxes.forEach((cb) => {
      db.delete_shift(cb.dataset.id);
    });
    loadShifts();
    loadSummary();
  }
});

document.getElementById("edit-shift-btn").addEventListener("click", () => {
  console.log("Edit shift clicked");
});
