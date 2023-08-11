var template = document.querySelector("#pb_template")
var results = document.querySelector("#results")
var lastClick = 0;
var delay = 2000;

function loadItems() {
    //delete the old results
    var search = $("#search").val();
    fetch('/laod_search?c=' + search).then((response) => {
        response.json().then((data) => {

            if (data["no_results"]) {
                document.getElementById("no_results").innerHTML = "The search has no result, maybe try another spelling";
            } else {
                for (var i = 0; i < data["not_followed"].length; i++) {
                    document.getElementById("no_results").innerHTML = "";
                    let template_clone = template.content.cloneNode(true);
                    template_clone.querySelector("#profile_picture").src = "static/profilepictures/" + data["not_followed"][i]["profile_picture"]
                    template_clone.querySelector('#username').innerHTML = data["not_followed"][i]["username"];
                    template_clone.querySelector('#blogs').innerHTML = data["not_followed"][i]["blogs_int"];

                    results.appendChild(template_clone);
                }
            }
        })
    })
}

function myFunction() {
    var elements = document.getElementsByClassName("result");
    var wrapper = document.getElementsByClassName("wrapper");
    var no_result = document.getElementById("no_result");
    var no_results = document.getElementById("no_results");

    if (elements.length > 0) {
        while (elements[0]) {
            elements[0].parentNode.removeChild(elements[0]);
        }
    }

    if (wrapper.length > 0) {
        while (wrapper[0]) {
            wrapper[0].parentNode.removeChild(wrapper[0]);
        }
    }
    if (no_result != null) {
        no_result.remove()
    }

    loadItems()
}

function x() {
    if (lastClick <= (Date.now() - delay)) {
        myFunction()
    }
    lastClick = Date.now();}
