function createTable() {
    $.ajax({
        url: "/ui/view/machine", success: function (response) {
            var machine_table = $("#machine_table");
            var thead, tbody, row, cell;

            thead = $("<thead>").appendTo(machine_table);
            row = $("<tr>").appendTo(thead);

            for (var i = 0; i < response[i].length; i++) {
                $("<th>").appendTo(row).text(response[0][i]);
            }

            tbody = $("<tbody>").appendTo(machine_table);
            for (var j = 1; j < response.length; j++) {
                row = $("<tr>").appendTo(tbody);
                for (var k = 0; k < response[k].length; k++) {
                    $("<td>").appendTo(row).text(response[j][k]);
                }
            }
            machine_table.DataTable();
        }, async: true
    });
}

function main() {
    createTable();
}

main();