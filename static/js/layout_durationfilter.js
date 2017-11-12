// Function to get values of key-value pairs in URL 
var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)), sURLVariables = sPageURL.split('&'), sParameterName, i;
    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};

// Function to get current URL with new duration parameters, to reload page when new duration is selected
function getUrl(durationstart, durationend) {
    var dateStart = "none"
    var dateEnd = "none"
    if (getUrlParameter('datestart') != true) {
        datestart = getUrlParameter('datestart')
    }
    if (getUrlParameter('dateend') != true) {
        dateend = getUrlParameter('dateend')
    }
    url = window.location.href;
    if (url.includes('overview')) {
        window.location='/overview?' + 'datestart=' + datestart + '&dateend=' + dateend + "&durationstart=" + durationstart + "&durationend=" + durationend;
    }
    else {
        window.location='/public?' + 'datestart=' + datestart + '&dateend=' + dateend + "&durationstart=" + durationstart + "&durationend=" + durationend;
    }
    return false;
};

// Set up druation filter text
function setUpFilter() {
    if (getUrlParameter('durationstart') == true || getUrlParameter('durationstart') == true) {
        document.getElementById("dfilter").innerHTML = 'Duration: All <span class="caret"></span>';
    }
    else if (getUrlParameter('durationstart') == 0 && getUrlParameter('durationend') == 5) {
        document.getElementById("dfilter").innerHTML = 'Duration: 0-5 mins <span class="caret"></span>';
    }
    else if (getUrlParameter('durationstart') == 5 && getUrlParameter('durationend') == 10) {
        document.getElementById("dfilter").innerHTML = 'Duration: 5-10 mins <span class="caret"></span>';
    }
    else if (getUrlParameter('durationstart') == 10){
        document.getElementById("dfilter").innerHTML = 'Duration: 10+ mins <span class="caret"></span>';
    }
    else {
        document.getElementById("dfilter").innerHTML = 'Duration: All <span class="caret"></span>';
    }   
    return false;
};

