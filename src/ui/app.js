let currentDriverId = null;
let db = null;
let startDate = "";
let endDate = "";
let modalMode = "add";
let currentShiftId = null;
let deliveryModalMode = "add";
let currentDeliveryId = null;
let currentTab = "shifts";

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
  document.getElementById("delivery-modal-driver-name").textContent =
    element.textContent;
  if (currentTab === "shifts") {
    loadShifts();
    loadSummary();
  } else {
    loadDeliveries();
    loadDeliveriesSummary();
  }
}

// Tab Switching
document.getElementById("shifts-tab-btn").addEventListener("click", () => {
  switchTab("shifts");
});

document.getElementById("deliveries-tab-btn").addEventListener("click", () => {
  switchTab("deliveries");
});

function switchTab(tab) {
  currentTab = tab;
  document
    .querySelectorAll(".tab-button")
    .forEach((btn) => btn.classList.remove("active"));
  document
    .querySelectorAll(".tab-content")
    .forEach((content) => content.classList.remove("active"));

  if (tab === "shifts") {
    document.getElementById("shifts-tab-btn").classList.add("active");
    document.getElementById("shifts-section").classList.add("active");
    loadShifts();
    loadSummary();
  } else {
    document.getElementById("deliveries-tab-btn").classList.add("active");
    document.getElementById("deliveries-section").classList.add("active");
    loadDeliveries();
    loadDeliveriesSummary();
  }
}

// Shifts Functions
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

// Deliveries Functions
function loadDeliveries() {
  if (!currentDriverId) return;
  db.get_deliveries(currentDriverId, startDate, endDate).then(
    (deliveriesJson) => {
      const deliveries = JSON.parse(deliveriesJson);
      const table = document.getElementById("delivery-table");
      table.innerHTML = "";
      deliveries.forEach((delivery) => {
        const subtotal = parseFloat(delivery.order_subtotal.replace("$", ""));
        const tip = parseFloat(delivery.tip.replace("$", ""));
        const collected = parseFloat(
          delivery.amount_collected.replace("$", ""),
        );
        const additionalCashTip = delivery.additional_cash_tip || 0;
        const totalTip = tip + additionalCashTip;
        const total = (subtotal + totalTip).toFixed(2);
        // Calculate tip percentage based on amount collected
        let tipPercent = 0;
        if (collected > 0) {
          tipPercent = (totalTip / collected) * 100;
        }
        const row = document.createElement("tr");
        row.innerHTML = `
                <td><input type="checkbox" data-id="${delivery.id}"></td>
                <td>${delivery.date}</td>
                <td>${delivery.order_num || "-"}</td>
                <td>${delivery.payment_type}</td>
                <td>${delivery.order_subtotal}</td>
                <td>${delivery.amount_collected}</td>
                <td class="green">${delivery.tip}</td>
                <td>${tipPercent.toFixed(1)}%</td>
                <td><strong>$${total}</strong></td>
            `;
        table.appendChild(row);
      });
    },
  );
}

function loadDeliveriesSummary() {
  if (!currentDriverId) return;
  db.get_deliveries_summary(currentDriverId, startDate, endDate).then(
    (summaryJson) => {
      const summary = JSON.parse(summaryJson);
      const cards = document.getElementById("delivery-summary-cards");
      const totalTipsWithAdditional =
        summary.total_tips + summary.total_additional_tips;
      const avgTip =
        summary.delivery_count > 0
          ? totalTipsWithAdditional / summary.delivery_count
          : 0;
      cards.innerHTML = `
            <div class="card green">Deliveries<br><strong>${summary.delivery_count}</strong></div>
            <div class="card green">Total Subtotal<br><strong>$${summary.total_subtotal.toFixed(2)}</strong></div>
            <div class="card green">Total Collected<br><strong>$${summary.total_collected.toFixed(2)}</strong></div>
            <div class="card green">Total Tips<br><strong>$${totalTipsWithAdditional.toFixed(2)}</strong></div>
            <div class="card green">Avg Tip<br><strong>$${avgTip.toFixed(2)}</strong></div>
        `;
    },
  );
}

// Search Button
document.getElementById("search-btn").addEventListener("click", () => {
  startDate = document.getElementById("start-date").value;
  endDate = document.getElementById("end-date").value;
  if (currentTab === "shifts") {
    loadShifts();
    loadSummary();
  } else {
    loadDeliveries();
    loadDeliveriesSummary();
  }
});

// Shift Modal Handlers
document.getElementById("add-shift-btn").addEventListener("click", () => {
  modalMode = "add";
  currentShiftId = null;
  document.getElementById("modal-title").textContent = "Add New Shift";
  document.querySelector('#add-shift-form button[type="submit"]').textContent =
    "Add Shift";
  document.getElementById("modal-driver-name").textContent =
    document.querySelector(".driver-list .active").textContent;
  document.getElementById("shift-id").value = "";
  document.getElementById("add-shift-form").reset();
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
  if (modalMode === "edit") {
    db.update_shift(
      currentShiftId,
      date,
      start,
      end,
      mileage,
      cash,
      credit,
      owed,
      hourly,
    );
  } else {
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
  }
  modalMode = "add";
  currentShiftId = null;
  document.getElementById("modal-title").textContent = "Add New Shift";
  document.querySelector('#add-shift-form button[type="submit"]').textContent =
    "Add Shift";
  document.getElementById("shift-id").value = "";
  document.getElementById("add-shift-modal").style.display = "none";
  document.getElementById("add-shift-form").reset();
  loadShifts();
  loadSummary();
});

document.getElementById("cancel-add").addEventListener("click", () => {
  modalMode = "add";
  currentShiftId = null;
  document.getElementById("modal-title").textContent = "Add New Shift";
  document.querySelector('#add-shift-form button[type="submit"]').textContent =
    "Add Shift";
  document.getElementById("shift-id").value = "";
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
  const checked = document.querySelectorAll(
    '#shift-table input[type="checkbox"]:checked',
  );
  if (checked.length !== 1) {
    alert("Please select exactly one shift to edit.");
    return;
  }
  const shiftId = checked[0].dataset.id;
  db.get_shift(shiftId).then((shiftJson) => {
    const shift = JSON.parse(shiftJson);
    if (!shift.id) {
      alert("Shift not found.");
      return;
    }
    modalMode = "edit";
    currentShiftId = shiftId;
    document.getElementById("modal-title").textContent = "Edit Shift";
    document.querySelector(
      '#add-shift-form button[type="submit"]',
    ).textContent = "Edit Shift";
    document.getElementById("modal-driver-name").textContent =
      document.querySelector(".driver-list .active").textContent;
    document.getElementById("shift-id").value = shift.id;
    document.getElementById("shift-date").value = shift.date;
    document.getElementById("shift-start").value = shift.start_time;
    document.getElementById("shift-end").value = shift.end_time;
    document.getElementById("shift-mileage").value = shift.mileage;
    document.getElementById("shift-cash").value = shift.cash_tips;
    document.getElementById("shift-credit").value = shift.credit_tips;
    document.getElementById("shift-owed").value = shift.owed;
    document.getElementById("shift-hourly").value = shift.hourly_rate;
    document.getElementById("add-shift-modal").style.display = "block";
  });
});

// Delivery Modal Handlers
function validateCurrencyInput(input) {
  const value = parseFloat(input.value);

  // Check for negative values
  if (value < 0) {
    input.value = "";
    alert("Value cannot be negative.");
    return false;
  }

  // Check for more than 2 decimal places
  const decimalMatch = input.value.match(/^\d+(\.\d{0,2})?$/);
  if (!decimalMatch && input.value !== "") {
    input.value = parseFloat(input.value).toFixed(2);
  }

  return true;
}

function validateCollectedVsSubtotal() {
  const subtotal =
    parseFloat(document.getElementById("delivery-subtotal").value) || 0;
  const collected =
    parseFloat(document.getElementById("delivery-collected").value) || 0;

  if (collected < subtotal) {
    alert("Amount collected cannot be less than order subtotal.");
    return false;
  }
  return true;
}

function calculateTip() {
  const subtotal =
    parseFloat(document.getElementById("delivery-subtotal").value) || 0;
  const collected =
    parseFloat(document.getElementById("delivery-collected").value) || 0;
  const baseTip = collected - subtotal;

  // Get additional cash tip if enabled
  const additionalTipInput = document.getElementById(
    "delivery-additional-cash-tip",
  );
  let additionalTip = 0;
  if (!additionalTipInput.disabled) {
    additionalTip = parseFloat(additionalTipInput.value) || 0;
  }

  const totalTip = baseTip + additionalTip;
  document.getElementById("delivery-tip").value = totalTip.toFixed(2);

  // Calculate tip percentage based on amount collected
  let tipPercent = 0;
  if (collected > 0) {
    tipPercent = (totalTip / collected) * 100;
  }
  document.getElementById("delivery-tip-percent").value =
    tipPercent.toFixed(1) + "%";
}

function toggleAdditionalCashTipField() {
  const paymentType = document.getElementById("delivery-payment-type").value;
  const additionalTipInput = document.getElementById(
    "delivery-additional-cash-tip",
  );

  // Enable additional cash tip only for Credit or Debit
  if (paymentType === "Credit" || paymentType === "Debit") {
    additionalTipInput.disabled = false;
    additionalTipInput.style.background = "#ffffff";
  } else {
    additionalTipInput.disabled = true;
    additionalTipInput.value = "";
    additionalTipInput.style.background = "#e0e0e0";
  }
  calculateTip();
}

document.getElementById("add-delivery-btn").addEventListener("click", () => {
  deliveryModalMode = "add";
  currentDeliveryId = null;
  document.getElementById("delivery-modal-title").textContent =
    "Add New Delivery";
  document.querySelector(
    '#add-delivery-form button[type="submit"]',
  ).textContent = "Add Delivery";
  document.getElementById("delivery-modal-driver-name").textContent =
    document.querySelector(".driver-list .active").textContent;
  document.getElementById("delivery-id").value = "";
  document.getElementById("add-delivery-form").reset();

  // Reset additional cash tip field state
  toggleAdditionalCashTipField();

  document.getElementById("add-delivery-modal").style.display = "block";
});

document
  .getElementById("delivery-subtotal")
  .addEventListener("input", calculateTip);
document
  .getElementById("delivery-collected")
  .addEventListener("input", calculateTip);
document
  .getElementById("delivery-additional-cash-tip")
  .addEventListener("input", calculateTip);

// Add validation listeners for currency fields
document
  .getElementById("delivery-subtotal")
  .addEventListener("blur", function () {
    validateCurrencyInput(this);
    validateCollectedVsSubtotal();
    calculateTip();
  });
document
  .getElementById("delivery-collected")
  .addEventListener("blur", function () {
    validateCurrencyInput(this);
    validateCollectedVsSubtotal();
    calculateTip();
  });
document
  .getElementById("delivery-additional-cash-tip")
  .addEventListener("blur", function () {
    validateCurrencyInput(this);
    calculateTip();
  });

// Add payment type change listener
document
  .getElementById("delivery-payment-type")
  .addEventListener("change", toggleAdditionalCashTipField);

document.getElementById("add-delivery-form").addEventListener("submit", (e) => {
  e.preventDefault();

  // Validate subtotal and collected before submission
  const subtotalInput = document.getElementById("delivery-subtotal");
  const collectedInput = document.getElementById("delivery-collected");

  if (
    !validateCurrencyInput(subtotalInput) ||
    !validateCurrencyInput(collectedInput)
  ) {
    return;
  }

  // Validate that collected is not less than subtotal
  if (!validateCollectedVsSubtotal()) {
    return;
  }

  const date = document.getElementById("delivery-date").value;
  const orderNum = document.getElementById("delivery-order-num").value;
  const paymentType = document.getElementById("delivery-payment-type").value;
  const subtotal = parseFloat(subtotalInput.value);
  const collected = parseFloat(collectedInput.value);
  const tip = parseFloat(document.getElementById("delivery-tip").value);

  // Get additional cash tip (0 if disabled)
  const additionalTipInput = document.getElementById(
    "delivery-additional-cash-tip",
  );
  const additionalCashTip = additionalTipInput.disabled
    ? 0
    : parseFloat(additionalTipInput.value) || 0;

  // Additional validation: ensure values are non-negative
  if (subtotal < 0 || collected < 0) {
    alert("Subtotal and Amount Collected must be non-negative values.");
    return;
  }

  if (deliveryModalMode === "edit") {
    db.update_delivery(
      currentDeliveryId,
      date,
      orderNum,
      paymentType,
      subtotal,
      collected,
      tip,
      additionalCashTip,
    );
  } else {
    db.add_delivery(
      currentDriverId,
      date,
      orderNum,
      paymentType,
      subtotal,
      collected,
      tip,
      additionalCashTip,
    );
  }
  deliveryModalMode = "add";
  currentDeliveryId = null;
  document.getElementById("delivery-modal-title").textContent =
    "Add New Delivery";
  document.querySelector(
    '#add-delivery-form button[type="submit"]',
  ).textContent = "Add Delivery";
  document.getElementById("delivery-id").value = "";
  document.getElementById("add-delivery-modal").style.display = "none";
  document.getElementById("add-delivery-form").reset();
  loadDeliveries();
  loadDeliveriesSummary();
});

document.getElementById("cancel-delivery-add").addEventListener("click", () => {
  deliveryModalMode = "add";
  currentDeliveryId = null;
  document.getElementById("delivery-modal-title").textContent =
    "Add New Delivery";
  document.querySelector(
    '#add-delivery-form button[type="submit"]',
  ).textContent = "Add Delivery";
  document.getElementById("delivery-id").value = "";
  document.getElementById("add-delivery-modal").style.display = "none";
  document.getElementById("add-delivery-form").reset();
});

document.getElementById("delete-delivery-btn").addEventListener("click", () => {
  const checkboxes = document.querySelectorAll(
    '#delivery-table input[type="checkbox"]:checked',
  );
  if (checkboxes.length === 0) {
    alert("Please select at least one delivery to delete.");
    return;
  }
  if (
    confirm(`Are you sure you want to delete ${checkboxes.length} delivery(s)?`)
  ) {
    checkboxes.forEach((cb) => {
      db.delete_delivery(cb.dataset.id);
    });
    loadDeliveries();
    loadDeliveriesSummary();
  }
});

document.getElementById("edit-delivery-btn").addEventListener("click", () => {
  const checked = document.querySelectorAll(
    '#delivery-table input[type="checkbox"]:checked',
  );
  if (checked.length !== 1) {
    alert("Please select exactly one delivery to edit.");
    return;
  }
  const deliveryId = checked[0].dataset.id;
  db.get_delivery(deliveryId).then((deliveryJson) => {
    const delivery = JSON.parse(deliveryJson);
    if (!delivery.id) {
      alert("Delivery not found.");
      return;
    }
    deliveryModalMode = "edit";
    currentDeliveryId = deliveryId;
    document.getElementById("delivery-modal-title").textContent =
      "Edit Delivery";
    document.querySelector(
      '#add-delivery-form button[type="submit"]',
    ).textContent = "Edit Delivery";
    document.getElementById("delivery-modal-driver-name").textContent =
      document.querySelector(".driver-list .active").textContent;
    document.getElementById("delivery-id").value = delivery.id;
    document.getElementById("delivery-date").value = delivery.date;
    document.getElementById("delivery-order-num").value =
      delivery.order_num || "";
    document.getElementById("delivery-payment-type").value =
      delivery.payment_type;
    document.getElementById("delivery-subtotal").value =
      delivery.order_subtotal;
    document.getElementById("delivery-collected").value =
      delivery.amount_collected;

    // Set additional cash tip and toggle field
    const additionalTipInput = document.getElementById(
      "delivery-additional-cash-tip",
    );
    additionalTipInput.value = delivery.additional_cash_tip || "";
    toggleAdditionalCashTipField();

    calculateTip();
    document.getElementById("add-delivery-modal").style.display = "block";
  });
});
