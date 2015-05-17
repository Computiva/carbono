$(document).ready(function() {
    $("input[type=submit], a.button").button();
    $("a#home").button({
        icons: {
            primary: "ui-icon-home",
        },
        text: false,
    });
    $("a.remove").button({
        icons: {
            primary: "ui-icon-trash",
        },
        text: false,
    });
    $("span.list_item").buttonset();
    $("div.checkboxes").buttonset();
});
