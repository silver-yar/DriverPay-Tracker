let currentDriverId = null;
let db = null;
let startDate = "";
let endDate = "";
let modalMode = "add";
let currentShiftId = null;
let deliveryModalMode = "add";
let currentDeliveryId = null;
let currentTab = "shifts";
let selectedShiftIdForDeliveries = null;
let currentDeliveryShiftId = null;
let currentDeliveryDate = "";

console.log("App.js loaded");

new QWebChannel(qt.webChannelTransport, function (channel) {
  db = channel.objects.db;
  console.log("QWebChannel ready");
  initPaymentTypeDropdown();
  setSelectedPaymentType("Credit");
  loadDrivers();
});

function loadDrivers(preferredDriverId = null) {
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
      const preferred = preferredDriverId
        ? driverList.querySelector(`li[data-id="${preferredDriverId}"]`)
        : null;
      const selectedElement = preferred || driverList.firstChild;
      selectDriver(selectedElement.dataset.id, selectedElement);
    } else {
      currentDriverId = null;
      clearDriverData();
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
  } else {
    loadDeliveries();
    loadDeliveriesSummary();
  }
}

function clearDriverData() {
  document.getElementById("modal-driver-name").textContent = "";
  document.getElementById("delivery-modal-driver-name").textContent = "";
  document.getElementById("shift-table").innerHTML = "";
  document.getElementById("summary-cards").innerHTML = "";
  document.getElementById("delivery-table").innerHTML = "";
  document.getElementById("delivery-summary-cards").innerHTML = "";
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
  } else {
    const checkedShifts = document.querySelectorAll(
      '#shift-table input[type="checkbox"]:checked',
    );
    if (checkedShifts.length !== 1) {
      selectedShiftIdForDeliveries = null;
      if (checkedShifts.length === 0) {
        alert(
          "Select exactly one shift in the Shifts tab before opening Deliveries.",
        );
      } else {
        alert("Select only one shift to view deliveries for that shift.");
      }
    } else {
      selectedShiftIdForDeliveries = checkedShifts[0].dataset.id;
    }

    document.getElementById("deliveries-tab-btn").classList.add("active");
    document.getElementById("deliveries-section").classList.add("active");
    loadDeliveries();
    loadDeliveriesSummary();
  }
}

function renderDeliverySummaryCards(summary) {
  const cards = document.getElementById("delivery-summary-cards");
  const owedColorClass = summary.total_owed < 0 ? "red" : "green";
  const owedDisplay = Math.abs(summary.total_owed);

  cards.innerHTML = `
            <div class="card green">Total Mileage<br><strong>${summary.total_mileage.toFixed(2)}</strong></div>
            <div class="card green">Cash Tips<br><strong>$${summary.total_cash.toFixed(2)}</strong></div>
            <div class="card green">Credit Tips<br><strong>$${summary.total_credit.toFixed(2)}</strong></div>
            <div class="card green">Total Cash Collected<br><strong>$${summary.total_cash_collected.toFixed(2)}</strong></div>
            <div class="card ${owedColorClass}">Owed<br><strong>$${owedDisplay.toFixed(2)}</strong></div>
        `;
}

// Shifts Functions
function loadShifts() {
  if (!currentDriverId) return;
  db.get_shifts(currentDriverId, startDate, endDate).then((shiftsJson) => {
    const shifts = JSON.parse(shiftsJson);
    const table = document.getElementById("shift-table");
    table.innerHTML = "";
    shifts.forEach((shift) => {
      const owedValue = parseFloat(String(shift.owed).replace("$", "")) || 0;
      const row = document.createElement("tr");
      row.innerHTML = `
                <td><input type="checkbox" data-id="${shift.id}"></td>
                <td>${shift.date}</td>
                <td>${shift.start}</td>
                <td>${shift.end}</td>
                <td>${shift.in_store_hours || 0}</td>
                <td>${shift.on_road_hours || 0}</td>
                <td>${parseFloat(shift.mileage).toFixed(2)}</td>
                <td class="green">${shift.cash}</td>
                <td class="green">${shift.credit}</td>
                <td class="${owedValue < 0 ? "red" : "green"}" data-owed-value="${owedValue}">$${Math.abs(owedValue).toFixed(2)}</td>
                <td>${shift.mileage_rate}</td>
            `;
      table.appendChild(row);
    });
    updateShiftSummaryFromSelection();
  });
}

function renderShiftSummaryCards(summary) {
  const cards = document.getElementById("summary-cards");
  const owedColorClass = summary.total_owed < 0 ? "red" : "green";
  const owedDisplay = Math.abs(summary.total_owed);
  cards.innerHTML = `
            <div class="card green">Total Mileage<br><strong>${summary.total_mileage.toFixed(2)}</strong></div>
            <div class="card green">Cash Tips<br><strong>$${summary.total_cash.toFixed(2)}</strong></div>
            <div class="card green">Credit Tips<br><strong>$${summary.total_credit.toFixed(2)}</strong></div>
            <div class="card ${owedColorClass}">Owed<br><strong>$${owedDisplay.toFixed(2)}</strong></div>
        `;
}

function updateShiftSummaryFromSelection() {
  const checked = document.querySelectorAll(
    '#shift-table input[type="checkbox"]:checked',
  );

  if (checked.length !== 1) {
    renderShiftSummaryCards({
      total_mileage: 0,
      total_cash: 0,
      total_credit: 0,
      total_owed: 0,
    });
    return;
  }

  const row = checked[0].closest("tr");
  const mileage = parseFloat(row.cells[4].textContent) || 0;
  const cash = parseFloat(row.cells[5].textContent.replace("$", "")) || 0;
  const credit = parseFloat(row.cells[6].textContent.replace("$", "")) || 0;
  const owed =
    parseFloat(row.cells[7].dataset.owedValue || row.cells[7].textContent) || 0;

  renderShiftSummaryCards({
    total_mileage: mileage,
    total_cash: cash,
    total_credit: credit,
    total_owed: owed,
  });
}

// Deliveries Functions
function loadDeliveries() {
  if (!currentDriverId) return;
  db.get_deliveries(currentDriverId, startDate, endDate).then(
    (deliveriesJson) => {
      const deliveries = JSON.parse(deliveriesJson);
      const filteredDeliveries = selectedShiftIdForDeliveries
        ? deliveries.filter(
            (delivery) =>
              String(delivery.shift_id || "") ===
              String(selectedShiftIdForDeliveries),
          )
        : [];
      const table = document.getElementById("delivery-table");
      table.innerHTML = "";
      filteredDeliveries.forEach((delivery) => {
        const subtotal = parseFloat(delivery.order_subtotal.replace("$", ""));
        const card_tip = parseFloat(delivery.card_tip.replace("$", ""));
        const collected = parseFloat(
          delivery.amount_collected.replace("$", ""),
        );
        const cashTip = delivery.cash_tip || 0;
        const totalTip = card_tip + cashTip;
        // For Cash payments, amount collected already includes cash tip
        // For Credit/Debit, we add cash tip to get total
        const total =
          delivery.payment_type === "Cash" ? collected : collected + cashTip;
        // Calculate tip percentage based on amount collected
        let tipPercent = 0;
        if (collected > 0) {
          tipPercent = (totalTip / subtotal) * 100;
        }
        // const cashTipDisplay = delivery.cash_tip
        //   ? `$${parseFloat(delivery.cash_tip).toFixed(2)}`
        //   : "-";
        const row = document.createElement("tr");
        row.innerHTML = `
                <td><input type="checkbox" data-id="${delivery.id}"></td>
                <td>${delivery.date}</td>
                <td>${delivery.order_num > 0 ? delivery.order_num : "-"}</td>
                <td>${delivery.payment_type}</td>
                <td>${delivery.order_subtotal}</td>
                <td>${delivery.amount_collected}</td>
                <td>${parseFloat(delivery.mileage || 0).toFixed(2)}</td>
                <td class="green">${delivery.card_tip}</td>
                <td class="green">$${parseFloat(delivery.cash_tip || 0).toFixed(2)}</td>
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
  if (!selectedShiftIdForDeliveries) {
    renderDeliverySummaryCards({
      total_mileage: 0,
      total_cash: 0,
      total_credit: 0,
      total_owed: 0,
      total_cash_collected: 0,
    });
    return;
  }

  db.get_deliveries(currentDriverId, startDate, endDate).then(
    (deliveriesJson) => {
      const deliveries = JSON.parse(deliveriesJson).filter(
        (delivery) =>
          String(delivery.shift_id || "") ===
          String(selectedShiftIdForDeliveries),
      );

      const summary = deliveries.reduce(
        (acc, delivery) => {
          const subtotal = parseFloat(
            String(delivery.order_subtotal || "$0").replace("$", ""),
          );
          const collected = parseFloat(
            String(delivery.amount_collected || "$0").replace("$", ""),
          );
          const mileage = parseFloat(delivery.mileage || 0);
          const cashTip = parseFloat(delivery.cash_tip || 0);
          const creditTip = parseFloat(
            String(delivery.card_tip || "$0").replace("$", ""),
          );

          acc.total_mileage += mileage;
          acc.total_credit += creditTip;
          acc.total_cash += cashTip;
          acc.total_tips += creditTip + cashTip;
          if (
            delivery.payment_type &&
            delivery.payment_type.toLowerCase() === "cash"
          ) {
            acc.total_cash_collected += collected;
          }
          return acc;
        },
        {
          total_mileage: 0,
          total_cash: 0,
          total_credit: 0,
          total_owed: 0,
          total_tips: 0,
          total_cash_collected: 0,
        },
      );
      // Keep owed in sync with shift logic.
      summary.total_owed = summary.total_tips - summary.total_cash_collected;

      renderDeliverySummaryCards(summary);
    },
  );
}

// Search Button
document.getElementById("search-btn").addEventListener("click", () => {
  startDate = document.getElementById("start-date").value;
  endDate = document.getElementById("end-date").value;
  if (currentTab === "shifts") {
    loadShifts();
  } else {
    loadDeliveries();
    loadDeliveriesSummary();
  }
});

document.getElementById("shift-table").addEventListener("change", (e) => {
  if (e.target && e.target.matches('input[type="checkbox"]')) {
    updateShiftSummaryFromSelection();
  }
});

// Driver Modal Handlers
function closeDriverModal() {
  document.getElementById("driver-modal-title").textContent = "Add Driver";
  document.getElementById("driver-name-label").textContent = "Driver Name:";
  document.getElementById("driver-submit-btn").textContent = "Add Driver";
  document.getElementById("driver-name-input").value = "";
  document.getElementById("driver-modal").style.display = "none";
}

document.getElementById("add-driver-btn").addEventListener("click", () => {
  document.getElementById("driver-modal-title").textContent = "Add Driver";
  document.getElementById("driver-name-label").textContent = "Driver Name:";
  document.getElementById("driver-submit-btn").textContent = "Add Driver";
  document.getElementById("driver-name-input").value = "";
  document.getElementById("driver-modal").style.display = "block";
});

document.getElementById("delete-driver-btn").addEventListener("click", () => {
  if (!currentDriverId) {
    alert("Please select a driver to delete.");
    return;
  }
  const activeDriver = document.querySelector(".driver-list .active");
  if (!activeDriver) {
    alert("Please select a driver to delete.");
    return;
  }

  const selectedDriverName = activeDriver.textContent.trim();
  if (!confirm(`Delete selected driver "${selectedDriverName}"?`)) {
    return;
  }

  db.delete_driver(selectedDriverName).then((resultJson) => {
    const result = JSON.parse(resultJson);
    if (!result.success) {
      alert(result.error || "Unable to delete driver.");
      return;
    }
    loadDrivers();
  });
});

document
  .getElementById("cancel-driver-modal")
  .addEventListener("click", closeDriverModal);

document.getElementById("driver-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("driver-name-input").value.trim();
  if (!name) {
    alert("Driver name cannot be empty.");
    return;
  }
  if (!/^[A-Za-z ]+$/.test(name)) {
    alert("Driver name can only contain alphabetic characters and spaces.");
    return;
  }

  db.add_driver(name).then((resultJson) => {
    const result = JSON.parse(resultJson);
    if (!result.success) {
      alert(result.error || "Unable to add driver.");
      return;
    }
    closeDriverModal();
    loadDrivers(result.driver_id);
  });
});

// Settings Modal Handlers
document.getElementById("settings-btn").addEventListener("click", () => {
  db.get_settings().then((settingsJson) => {
    const settings = JSON.parse(settingsJson);
    document.getElementById("settings-mileage-rate").value =
      settings.default_mileage_rate;
    document.getElementById("settings-in-store-hourly-rate").value = parseFloat(
      settings.default_in_store_hourly_rate,
    ).toFixed(2);
    document.getElementById("settings-on-road-hourly-rate").value = parseFloat(
      settings.default_on_road_hourly_rate,
    ).toFixed(2);
    document.getElementById("settings-modal").style.display = "block";
  });
});

document.getElementById("cancel-settings").addEventListener("click", () => {
  document.getElementById("settings-modal").style.display = "none";
});

document.getElementById("settings-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const mileageRate = parseFloat(
    document.getElementById("settings-mileage-rate").value,
  );
  const inStoreHourlyRate = parseFloat(
    document.getElementById("settings-in-store-hourly-rate").value,
  );
  const onRoadHourlyRate = parseFloat(
    document.getElementById("settings-on-road-hourly-rate").value,
  );

  // Validate positive values
  if (mileageRate <= 0 || inStoreHourlyRate <= 0 || onRoadHourlyRate <= 0) {
    alert("All rates must be positive values.");
    return;
  }

  db.update_settings(mileageRate, inStoreHourlyRate, onRoadHourlyRate);
  document.getElementById("settings-modal").style.display = "none";
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

  // Load default rates from settings
  db.get_settings().then((settingsJson) => {
    const settings = JSON.parse(settingsJson);
    document.getElementById("shift-mileage-rate").value =
      settings.default_mileage_rate;
    document.getElementById("shift-in-store-hours").value =
      settings.default_in_store_hourly_rate || 0;
    document.getElementById("shift-on-road-hours").value =
      settings.default_on_road_hourly_rate || 0;
  });

  document.getElementById("add-shift-modal").style.display = "block";
});

document.getElementById("add-shift-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const date = document.getElementById("shift-date").value;
  const start = document.getElementById("shift-start").value;
  const end = document.getElementById("shift-end").value;
  const inStoreHours =
    parseFloat(document.getElementById("shift-in-store-hours").value) || 0;
  const onRoadHours =
    parseFloat(document.getElementById("shift-on-road-hours").value) || 0;
  const startingMileage = parseFloat(
    document.getElementById("shift-starting-mileage").value,
  );
  const endingMileage = parseFloat(
    document.getElementById("shift-ending-mileage").value,
  );
  const mileageRate = parseFloat(
    document.getElementById("shift-mileage-rate").value,
  );

  // Calculate total shift hours from start and end time
  const startParts = start.split(":");
  const endParts = end.split(":");
  const startMinutes = parseInt(startParts[0]) * 60 + parseInt(startParts[1]);
  const endMinutes = parseInt(endParts[0]) * 60 + parseInt(endParts[1]);
  const totalShiftHours = (endMinutes - startMinutes) / 60;

  // Input Validation
  if (inStoreHours < 0) {
    alert("In-store hours cannot be negative.");
    return;
  }
  if (onRoadHours < 0) {
    alert("On-road hours cannot be negative.");
    return;
  }
  if (inStoreHours + onRoadHours > totalShiftHours) {
    alert(
      `In-store hours (${inStoreHours}) + On-road hours (${onRoadHours}) = ${inStoreHours + onRoadHours} cannot exceed total shift hours (${totalShiftHours.toFixed(2)}).`,
    );
    return;
  }
  if (startingMileage < 0) {
    alert("Starting mileage cannot be negative.");
    return;
  }
  if (endingMileage < 0) {
    alert("Ending mileage cannot be negative.");
    return;
  }
  if (mileageRate < 0) {
    alert("Mileage rate cannot be negative.");
    return;
  }
  if (endingMileage < startingMileage) {
    alert("Ending mileage cannot be less than starting mileage.");
    return;
  }

  const cash = parseFloat(document.getElementById("shift-cash").value);
  const credit = parseFloat(document.getElementById("shift-credit").value);
  // Owed is auto-calculated from deliveries, pass 0 here
  const owed = 0;
  if (modalMode === "edit") {
    db.update_shift(
      currentShiftId,
      date,
      start,
      end,
      inStoreHours,
      onRoadHours,
      startingMileage,
      endingMileage,
      cash,
      credit,
      owed,
      mileageRate,
    );
  } else {
    db.add_shift(
      currentDriverId,
      date,
      start,
      end,
      inStoreHours,
      onRoadHours,
      startingMileage,
      endingMileage,
      cash,
      credit,
      owed,
      mileageRate,
    );
  }
  closeShiftModal();
  loadShifts();
});

document.getElementById("cancel-add").addEventListener("click", () => {
  closeShiftModal();
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
    document.getElementById("shift-in-store-hours").value =
      shift.in_store_hours || 0;
    document.getElementById("shift-on-road-hours").value =
      shift.on_road_hours || 0;
    document.getElementById("shift-starting-mileage").value =
      shift.starting_mileage;
    document.getElementById("shift-ending-mileage").value =
      shift.ending_mileage;
    document.getElementById("shift-mileage").value = shift.mileage;
    document.getElementById("shift-cash").value = shift.cash_tips;
    document.getElementById("shift-credit").value = shift.credit_tips;
    document.getElementById("shift-owed").value = shift.owed;
    document.getElementById("shift-mileage-rate").value =
      shift.mileage_rate_rate;
    document.getElementById("add-shift-modal").style.display = "block";
  });
});

// Delivery Modal Handlers
const PAYMENT_TYPE_LABELS = {
  Credit: "Credit (auto-calculated)",
  Debit: "Debit (auto-calculated)",
  Cash: "Cash (auto-calculated)",
};

function getSelectedPaymentType() {
  return document.getElementById("delivery-payment-type").value;
}

function setSelectedPaymentType(paymentType) {
  const safeValue = PAYMENT_TYPE_LABELS[paymentType] ? paymentType : "Credit";
  document.getElementById("delivery-payment-type").value = safeValue;
  document.getElementById("delivery-payment-toggle").textContent =
    PAYMENT_TYPE_LABELS[safeValue];
}

function setPaymentDropdownOpen(isOpen) {
  const dropdown = document.getElementById("delivery-payment-dropdown");
  const toggle = document.getElementById("delivery-payment-toggle");
  dropdown.classList.toggle("open", isOpen);
  toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
}

function initPaymentTypeDropdown() {
  const dropdown = document.getElementById("delivery-payment-dropdown");
  const toggle = document.getElementById("delivery-payment-toggle");
  const options = dropdown.querySelectorAll(".custom-dropdown-option");

  toggle.addEventListener("click", () => {
    const isOpen = dropdown.classList.contains("open");
    setPaymentDropdownOpen(!isOpen);
  });

  options.forEach((option) => {
    option.addEventListener("click", () => {
      setSelectedPaymentType(option.dataset.value);
      setPaymentDropdownOpen(false);
      toggleCardTipField();
    });
  });

  document.addEventListener("click", (event) => {
    if (!dropdown.contains(event.target)) {
      setPaymentDropdownOpen(false);
    }
  });
}

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
  const subtotalInput = document.getElementById("delivery-subtotal").value;
  const collectedInput = document.getElementById("delivery-collected").value;

  // Don't validate if either field is empty
  if (!subtotalInput || !collectedInput) {
    return true;
  }

  const subtotal = parseFloat(subtotalInput);
  const collected = parseFloat(collectedInput);

  // Don't validate if values are not valid numbers
  if (isNaN(subtotal) || isNaN(collected)) {
    return true;
  }

  if (collected < subtotal) {
    alert("Amount collected cannot be less than order subtotal.");
    return false;
  }
  return true;
}

function calculateTip(isInitialLoad = false) {
  const subtotal =
    parseFloat(document.getElementById("delivery-subtotal").value) || 0;
  const collected =
    parseFloat(document.getElementById("delivery-collected").value) || 0;
  const paymentType = getSelectedPaymentType();

  let cardTip, cashTip;

  if (paymentType === "Cash") {
    // For Cash: card tip is 0, cash tip is auto-calculated (only if not loading existing data)
    cardTip = 0;
    if (isInitialLoad) {
      // When loading existing delivery, preserve the saved cash tip value
      cashTip =
        parseFloat(document.getElementById("delivery-cash-tip").value) || 0;
    } else {
      cashTip = collected - subtotal;
    }
  } else {
    // For Credit/Debit: card tip is auto-calculated, cash tip is manual
    cardTip = collected - subtotal;
    cashTip =
      parseFloat(document.getElementById("delivery-cash-tip").value) || 0;
  }

  const totalTip = cardTip + cashTip;

  document.getElementById("delivery-card-tip").value = cardTip.toFixed(2);
  if (!isInitialLoad || paymentType === "Cash") {
    document.getElementById("delivery-cash-tip").value = cashTip.toFixed(2);
  }

  // Calculate tip percentage based on subtotal
  let tipPercent = 0;
  if (subtotal > 0) {
    tipPercent = (totalTip / subtotal) * 100;
  }
  document.getElementById("delivery-tip-percent").value =
    tipPercent.toFixed(1) + "%";
}

function toggleCardTipField() {
  const paymentType = getSelectedPaymentType();
  const cardTipInput = document.getElementById("delivery-card-tip");
  const cashTipInput = document.getElementById("delivery-cash-tip");

  if (paymentType === "Cash") {
    // For Cash: card tip is 0 and read-only, cash tip is auto-calculated and read-only
    cardTipInput.disabled = true;
    cardTipInput.value = "0.00";
    cardTipInput.style.background = "#f0f0f0";

    cashTipInput.disabled = true;
    cashTipInput.style.background = "#f0f0f0";
  } else {
    // For Credit/Debit: card tip is auto-calculated and read-only, cash tip is editable
    cardTipInput.disabled = false;
    cardTipInput.style.background = "#f0f0f0";

    cashTipInput.disabled = false;
    cashTipInput.style.background = "#ffffff";
  }
  calculateTip(false);
}

// Calculate total mileage from starting and ending mileage
function calculateMileage() {
  const startingMileage =
    parseFloat(document.getElementById("shift-starting-mileage").value) || 0;
  const endingMileage =
    parseFloat(document.getElementById("shift-ending-mileage").value) || 0;
  const totalMileage = endingMileage - startingMileage;
  document.getElementById("shift-mileage").value =
    totalMileage >= 0 ? totalMileage.toFixed(2) : "";
}

// Helper function to close shift modal
function closeShiftModal() {
  modalMode = "add";
  currentShiftId = null;
  document.getElementById("modal-title").textContent = "Add New Shift";
  document.querySelector('#add-shift-form button[type="submit"]').textContent =
    "Add Shift";
  document.getElementById("shift-id").value = "";
  document.getElementById("add-shift-modal").style.display = "none";
  document.getElementById("add-shift-form").reset();
}

// Helper function to close delivery modal
function closeDeliveryModal() {
  deliveryModalMode = "add";
  currentDeliveryId = null;
  currentDeliveryShiftId = null;
  currentDeliveryDate = "";
  document.getElementById("delivery-modal-title").textContent =
    "Add New Delivery";
  document.querySelector(
    '#add-delivery-form button[type="submit"]',
  ).textContent = "Add Delivery";
  document.getElementById("delivery-id").value = "";
  document.getElementById("add-delivery-modal").style.display = "none";
  document.getElementById("add-delivery-form").reset();
  setSelectedPaymentType("Credit");
  setPaymentDropdownOpen(false);
}

// Add event listeners for mileage calculation
document
  .getElementById("shift-starting-mileage")
  .addEventListener("input", calculateMileage);
document
  .getElementById("shift-ending-mileage")
  .addEventListener("input", calculateMileage);

document.getElementById("add-delivery-btn").addEventListener("click", () => {
  if (!selectedShiftIdForDeliveries) {
    alert("Select one shift in the Shifts tab before adding a delivery.");
    return;
  }

  deliveryModalMode = "add";
  currentDeliveryId = null;
  currentDeliveryShiftId = selectedShiftIdForDeliveries;
  document.getElementById("delivery-modal-title").textContent =
    "Add New Delivery";
  document.querySelector(
    '#add-delivery-form button[type="submit"]',
  ).textContent = "Add Delivery";
  document.getElementById("delivery-modal-driver-name").textContent =
    document.querySelector(".driver-list .active").textContent;
  document.getElementById("delivery-id").value = "";
  document.getElementById("add-delivery-form").reset();
  setSelectedPaymentType("Credit");
  document.getElementById("delivery-date").value = "";
  currentDeliveryDate = "";

  db.get_shift(currentDeliveryShiftId).then((shiftJson) => {
    const shift = JSON.parse(shiftJson);
    if (!shift.id) {
      alert("Selected shift not found.");
      return;
    }
    currentDeliveryDate = shift.date;
    document.getElementById("delivery-date").value = shift.date;

    // Reset card tip field state
    toggleCardTipField();

    document.getElementById("add-delivery-modal").style.display = "block";
  });
});

document
  .getElementById("delivery-subtotal")
  .addEventListener("input", calculateTip);
document
  .getElementById("delivery-collected")
  .addEventListener("input", calculateTip);
document
  .getElementById("delivery-cash-tip")
  .addEventListener("input", calculateTip);

// Add validation listeners for currency fields
document
  .getElementById("delivery-subtotal")
  .addEventListener("blur", function () {
    validateCurrencyInput(this);
    calculateTip();
  });
document
  .getElementById("delivery-collected")
  .addEventListener("blur", function () {
    validateCurrencyInput(this);
    calculateTip();
  });
document
  .getElementById("delivery-cash-tip")
  .addEventListener("blur", function () {
    validateCurrencyInput(this);
    calculateTip();
  });
document
  .getElementById("delivery-mileage")
  .addEventListener("blur", function () {
    validateCurrencyInput(this);
  });

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

  const date =
    currentDeliveryDate || document.getElementById("delivery-date").value;
  const orderNum = parseInt(
    document.getElementById("delivery-order-num").value,
    10,
  );
  const shiftId =
    deliveryModalMode === "edit"
      ? currentDeliveryShiftId
      : selectedShiftIdForDeliveries;
  const paymentType = getSelectedPaymentType();
  const subtotal = parseFloat(subtotalInput.value);
  const collected = parseFloat(collectedInput.value);
  const mileageInput = document.getElementById("delivery-mileage");
  if (!validateCurrencyInput(mileageInput)) {
    return;
  }
  const mileage = parseFloat(mileageInput.value);
  const cashTip = parseFloat(
    document.getElementById("delivery-cash-tip").value,
  );

  // Get credit/debit tip (0 if disabled)
  const cardTipInput = document.getElementById("delivery-card-tip");
  const cardTip = cardTipInput.disabled
    ? 0
    : parseFloat(cardTipInput.value) || 0;

  // Additional validation: ensure values are non-negative
  if (subtotal < 0 || collected < 0 || mileage < 0) {
    alert(
      "Subtotal, Amount Collected, and Mileage must be non-negative values.",
    );
    return;
  }
  if (Number.isNaN(mileage)) {
    alert("Mileage is required.");
    return;
  }
  if (!date) {
    alert("Unable to determine delivery date from the selected shift.");
    return;
  }
  if (!shiftId) {
    alert("Select one shift before saving deliveries.");
    return;
  }

  if (deliveryModalMode === "edit") {
    db.update_delivery(
      currentDeliveryId,
      shiftId,
      date,
      orderNum,
      paymentType,
      subtotal,
      collected,
      cardTip,
      cashTip,
      mileage,
    );
  } else {
    db.add_delivery(
      currentDriverId,
      shiftId,
      date,
      orderNum,
      paymentType,
      subtotal,
      collected,
      cardTip,
      cashTip,
      mileage,
    );
  }
  closeDeliveryModal();
  loadDeliveries();
  loadDeliveriesSummary();
  loadShifts();
});

document.getElementById("cancel-delivery-add").addEventListener("click", () => {
  closeDeliveryModal();
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
    currentDeliveryShiftId = delivery.shift_id || selectedShiftIdForDeliveries;
    document.getElementById("delivery-modal-title").textContent =
      "Edit Delivery";
    document.querySelector(
      '#add-delivery-form button[type="submit"]',
    ).textContent = "Edit Delivery";
    document.getElementById("delivery-modal-driver-name").textContent =
      document.querySelector(".driver-list .active").textContent;
    document.getElementById("delivery-id").value = delivery.id;
    document.getElementById("delivery-date").value = delivery.date;
    currentDeliveryDate = delivery.date;
    document.getElementById("delivery-order-num").value =
      delivery.order_num !== undefined && delivery.order_num !== null
        ? delivery.order_num
        : "";
    setSelectedPaymentType(delivery.payment_type);
    document.getElementById("delivery-subtotal").value =
      delivery.order_subtotal;
    document.getElementById("delivery-collected").value =
      delivery.amount_collected;
    document.getElementById("delivery-mileage").value = delivery.mileage;

    // Set additional cash tip and toggle field
    const additionalTipInput = document.getElementById("delivery-cash-tip");
    additionalTipInput.value = delivery.cash_tip || "";
    toggleCardTipField();
    calculateTip(true);
    document.getElementById("add-delivery-modal").style.display = "block";
  });
});
