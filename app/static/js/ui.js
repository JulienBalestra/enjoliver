function createMachineTable() {
    $.ajax({
        url: "/ui/view/machine", success: function (response) {
            if (response.length == 0) {
                return
            }
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

function recurseHealth(object) {
    var health_status = $("#health_status");
    var label, li;

    for (var key in object) {
        if (object.hasOwnProperty(key)) {
            if (typeof(object[key]) != "boolean") {
                //TODO display the parent
                recurseHealth(object[key]);
                continue
            }
            li = $("<li>").appendTo(health_status);
            if (object[key] == true) {
                label = $("<span class=\"label label-success\">").appendTo(li).text(key);
            } else {
                label = $("<span class=\"label label-danger\">").appendTo(li).text(key);
            }

            // $(key).appendTo(label);
            console.log(key + " -> " + object[key]);
        }
    }
}

function createHealth() {
    $.ajax({
        url: "/healthz", success: function (response) {

            recurseHealth(response);
        }, async: true
    });
}

function main() {
    createMachineTable();
    createHealth();
}

main();