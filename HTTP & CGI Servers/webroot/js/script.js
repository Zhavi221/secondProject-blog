var data = null;
getdata()
function getdata() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            data = JSON.parse(this.responseText)
        }
    }

    var url = "/coronadata.json";

    xhttp.open("GET", url, false);
    xhttp.setRequestHeader("X-Requested-With", "XMLHttpRequest");

    xhttp.send();
}


function countrySelect()
{
    var d = document.getElementById("countrySelect");
    var displayedCountry = d.options[d.selectedIndex].text;
    console.log(data[displayedCountry])
    document.getElementById("txtvalue").innerHTML = data[displayedCountry]
}