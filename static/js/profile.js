$("input:checkbox").on("change", function() {
    var $box1 = $(" #public")
    var $box2 = $("#privat")
    var $box3 = $("#friends")
    if (!($box1.is(":checked")) && !($box2.is(":checked")) && !($box3.is(":checked"))) {
        $(".post").show(1000);
    } else {
        $("input:checkbox").each(function() {
            var value = $(this).attr("value");
            if ($(this).is(":checked")) {
                $(".post").filter("." + value).show(1000);
            } else {
                $(".post").filter("." + value).hide(1000);
            }
        })
    }
})