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


        // COMBINE WITH DATEPICKER FUNCTION FOR ALL RELOADS
        // Function to get current URL with new duration parameters
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

        // Function to get overview/public URL with current duration and date parameters (for overview and public pages)
        function getOverviewPublicUrl(base) {
            return base + 'datestart=' + getUrlParameter('datestart') + '&dateend=' + getUrlParameter('dateend') + "&durationstart=" + getUrlParameter('durationstart') + "&durationend=" + getUrlParameter('durationend');
        };

        // Function to get HC URL with current date parameters
        function getHcUrl() {
            return '/hcreports?' + 'datestart=' + getUrlParameter('datestart') + '&dateend=' + getUrlParameter('dateend');
        };

        window.onload = function() {
        	// MOVE THIS BACK TO LAYOUT_DURATIONFILTER
            // Set up druation filter text
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

            // MOVE THIS TO LAYOUT.HTML
            // Set up nav bar links
            document.getElementById('overviewlink').href = getOverviewPublicUrl('/overview?')
            document.getElementById('publiclink').href = getOverviewPublicUrl('/public?')
            document.getElementById('hcreportslink').href = getHcUrl()
            return false;
         };
