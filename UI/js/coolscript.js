var data = {}

function countrySelect()
{
    var d = document.getElementById("countrySelect");
    var displayedCountry = d.options[d.selectedIndex].text;
    async function getUsers() {
        let response = await fetch("https://api.covid19api.com/live/country/"+displayedCountry)
        let data = await response.json()
        return data;
    }
    
    getUsers().then(data => 
        document.getElementById("txtvalue").innerHTML = data[0]['Active']
    )
}