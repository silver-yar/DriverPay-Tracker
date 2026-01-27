const table = document.getElementById("shift-table");

const shifts = [
    {
        date: "04/01/2024",
        start: "10:00 AM",
        end: "4:00 PM",
        mileage: 45,
        cash: "$30.00",
        credit: "$25.00",
        owed: "$15.00",
        hourly: "$18.50"
    },
    {
        date: "04/02/2024",
        start: "11:30 AM",
        end: "5:30 PM",
        mileage: 60,
        cash: "$25.00",
        credit: "$35.00",
        owed: "$20.00",
        hourly: "$20.00"
    }
];

shifts.forEach(shift => {
    const row = document.createElement("tr");
    row.innerHTML = `
        <td>${shift.date}</td>
        <td>${shift.start}</td>
        <td>${shift.end}</td>
        <td>${shift.mileage}</td>
        <td class="green">${shift.cash}</td>
        <td class="green">${shift.credit}</td>
        <td class="red">${shift.owed}</td>
        <td>${shift.hourly}</td>
    `;
    table.appendChild(row);
});
