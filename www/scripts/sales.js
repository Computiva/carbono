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
        $("table#products_list tbody").append(table_line);
        $("a#remove_" + products_list[i].id).click(function() {
            for (j in products_list) {
                if (products_list[j].id == this.id.split("_")[1]) {
                    products_list.splice(j, 1);
                    update_products_list();
                };
            };
        });
    };
    $("span#total").text(("R$ " + total.toFixed(2)).replace(".", ","));
    $("input#products_list").val(JSON.stringify(products_list));
    update_partials();
};

update_partials = function() {
    total = 0;
    for (i in products_list) {
        partial = products_list[i].amount * products_list[i].price;
        total += partial;
    };
    $("table#partials tbody").empty();
    date = $.datepicker.parseDate("dd/mm/yy", $("input#initial_date").val());
    times = parseInt($("input#times").val());
    for (i=0; i < times; i++) {
        table_line = $("<tr />");
        table_line.append($("<td />").text($.datepicker.formatDate("dd/mm/yy", date)));
        table_line.append($("<td />").text(("R$ " + (total / times).toFixed(2)).replace(".", ",")));
        table_line.append($("<td />").append("<input type=\"checkbox\">"));
        $("table#partials tbody").append(table_line);
        date.setMonth(date.getMonth() + 1);
    };
};

$(document).ready(function() {
    $("div#installment_sale_params input").change(function() {
        update_partials();
    });
    $("input#registered_client").button();
    $("input#registered_client").click(function() {
        $("input#client_name").val("");
        $("input#client_name").toggle("slow");
    });
    $("div#sale_terms input").click(function() {
        if ($("div#sale_terms input:checked").val() == "installment_sale") {
            $("div#installment_sale_params").show("slow");
        } else {
            $("div#installment_sale_params").hide("slow");
            $("input#initial_date").val($.datepicker.formatDate("dd/mm/yy", new Date()));
            $("input#times").val("1");
            update_partials();
        };
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
                product_already_in_list = false;
                for (i in products_list) {
                    if (products_list[i].id == id) {
                        products_list[i].amount += parseInt(amount);
                        product_already_in_list = true;
                    }
                }
                if (!product_already_in_list) {
                    products_list.push({
                        name: name,
                        amount: parseInt(amount),
                        price: price,
                        id: id,
                    });
                }
                update_products_list();
                add_product_dialog.dialog("close");
                $("input#product_name").val("");
                $("input#product_amount").val("");
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
    update_partials();
});
