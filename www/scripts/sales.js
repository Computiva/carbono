update_products_list = function() {
    $("table#products_list tbody").empty();
    total = 0;
    for (i in products_list) {
        partial = products_list[i].amount * products_list[i].price;
        total += partial;
        table_line = $("<tr id=\"product_" + products_list[i].id + "\" />");
        table_line.append($("<td />").text(products_list[i].name));
        table_line.append($("<td />").text(products_list[i].amount));
        table_line.append($("<td />").text(("R$ " + products_list[i].price.toFixed(2)).replace(".", ",")));
        table_line.append($("<td />").text(("R$ " + partial.toFixed(2)).replace(".", ",")));
        table_line.append($("<td />").append("<a id=\"remove_" + products_list[i].id + "\" href=\"#\"><i class=\"fa fa-times\" /></a>"));
        $("a#remove_" + products_list[i].id).click(function() {
            products_list.splice(i, 1);
            update_products_list();
        });
        $("table#products_list tbody").append(table_line);
    };
    $("span#total").text(("R$ " + total.toFixed(2)).replace(".", ","));
};

$(document).ready(function() {
    $("input#registered_client").button();
    $("input#registered_client").click(function() {
        $("input#client_name").toggle();
    });
    $("input#initial_date").datepicker({
        dateFormat: "dd/mm/yy",
    });
    $("input#client_name").autocomplete({
        source: clients,
    });
    products_names = [];
    for (i in products) {
        products_names.push(products[i].name);
    }
    $("input#product_name").autocomplete({
        source: products_names,
        appendTo: "div#add_product_form",
    });
    products_list = [];
    add_product_dialog = $("div#add_product_form").dialog({
        autoOpen: false,
        buttons: {
            "Ok": function() {
                name = $("input#product_name")[0].value;
                amount = $("input#product_amount")[0].value;
                for (i in products) {
                    if (name == products[i].name) {
                        price = products[i].price;
                        id = products[i].id;
                        break;
                    }
                }
                products_list.push({
                    name: name,
                    amount: parseInt(amount),
                    price: price,
                    id: id,
                });
                update_products_list();
                add_product_dialog.dialog("close");
            },
            "Cancel": function() {
                add_product_dialog.dialog("close");
            },
        },
    });
    $("a#add_product").button();
    $("a#add_product").click(function() {
        add_product_dialog.dialog("open");
    });
});
