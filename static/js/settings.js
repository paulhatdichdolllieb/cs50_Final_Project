$(" #restet").on("click", function() {
    $(" #col_private").val("#248bf5")
    $(" #col_public").val("#e5e5ea")
    $(" #col_friends").val("#25D366")
    $(" #text_col_private").val("#FFFFFF")
    $(" #text_col_friends").val("#000000")
    $(" #text_col_public").val("#000000")
})



$(document).ready(() => {
    $("#profile_picture").change(function() {
        const file = this.files[0];
        if (file) {
            let reader = new FileReader();
            reader.onload = function(event) {
                $("#imgPreview")
                    .attr("src", event.target.result);
            };
            reader.readAsDataURL(file);
        }
    });
});