$(document).ready(function() {
    $("input[type=submit], a.button").button();
    $("a#home").button({
        icons: {
            primary: "ui-icon-home",
        },
        text: false,
    });
    $("div.checkboxes").buttonset();
});
