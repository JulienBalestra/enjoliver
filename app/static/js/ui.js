function createMachineTable() {
    $.ajax({
        url: "/ui/view/machine", success: function (response) {
            if (response.length < 2) {
                return
            }
            $("#machine-nb").text(response.length - 1);
            var machine_table = $("#machine_table");
            var thead, tbody, row;

            thead = $("<thead>").appendTo(machine_table);
            row = $("<tr>").appendTo(thead);

            for (var i = 0; i < response[0].length; i++) {
                $("<th>").appendTo(row).text(response[0][i]);
            }

            tbody = $("<tbody>").appendTo(machine_table);
            for (var j = 1; j < response.length; j++) {
                row = $("<tr>").appendTo(tbody);
                for (var k = 0; k < response[j].length; k++) {
                    $("<td>").appendTo(row).text(response[j][k]);
                }
            }
            machine_table.DataTable();
        }, async: true
    });
}

function main() {
    createMachineTable();
}

main();