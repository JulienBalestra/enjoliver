function createMachineTable() {
    $.ajax({
        url: "/ui/view/machine", success: function (response) {
            if (response.length == 0) {
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
                for (var k = 0; k < response[k].length; k++) {
                    $("<td>").appendTo(row).text(response[j][k]);
                }
            }
            machine_table.DataTable();
        }, async: true
    });
}

function recurseHealth(object, parent) {
    var label, li, new_parent;

    for (var key in object) {
        if (object.hasOwnProperty(key)) {
            if (typeof(object[key]) != "boolean") {
                li = $("<li>").appendTo(parent);
                $("<span class=\"label label-default\">").appendTo(li).text(key);
                new_parent = $("<ul>").appendTo(parent);
                recurseHealth(object[key], new_parent);
                continue
            }
            li = $("<li>").appendTo(parent);
            if (object[key] == true) {
                $("<span class=\"label label-success\">").appendTo(li).text(key);
            } else {
                $("<span class=\"label label-danger\">").appendTo(li).text(key);
            }
        }
    }
}

function createHealth() {
    $.ajax({
        url: "/healthz", success: function (response) {
            recurseHealth(response, $("<ul>").appendTo($("#health_status")));
        }, async: true
    });
}

function main() {
    createMachineTable();
    createHealth();
}

main();

$(document).ready(function(){
    $("#refresh-button").click(function () {
        console.log("click catch");
    });
});