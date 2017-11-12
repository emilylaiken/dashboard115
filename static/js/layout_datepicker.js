function setUpPicker() {
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
    
    ////////////////////////////// SET UP REDIRECT URLS FOR WHEN A NEW RANGE IS SELECTED //////////////////////////////////////
    // Reload page to same URL with new parameters when a new date is selected
    function refresh_page(start, end) {
        duration_start = '0'
        duration_end = 'end'
        if (getUrlParameter('durationstart') != true) {
            duration_start = getUrlParameter('durationstart')
        }
        if (getUrlParameter('durationend') != true) {
            duration_end = getUrlParameter('durationend')
        }
        url = window.location.href;
        if (url.includes('overview')) {
            window.location.href = "/overview?durationstart=" + duration_start + "&durationend=" + duration_end + "&datestart=" + start.format('YYYY-MM-DD') + "&dateend=" + end.format('YYYY-MM-DD');
        }
        else if (url.includes('download')) {
            window.location.href = "/download?datestart=" + start.format('YYYY-MM-DD') + "&dateend=" + end.format('YYYY-MM-DD');
        }
        else if (url.includes('hcreports')) {
            window.location.href = "/hcreports?datestart=" + start.format('YYYY-MM-DD') + "&dateend=" + end.format('YYYY-MM-DD');
        }
        else {
            window.location.href = "/public?durationstart=" + duration_start + "&durationend=" + duration_end + "&datestart=" + start.format('YYYY-MM-DD') + "&dateend=" + end.format('YYYY-MM-DD');
        }
    }

    ///////////////////////////// SET UP WHICH RANGE WILL BE DEFAULT SELECTED AND PRE-CHOSEN OPTIONS ////////////////////////
    // Function to get most recent Wednesday--used in finding last week
    function get_last_wed() {
        today = moment().day()
        if (today > 3) {
            return moment().subtract(today - 3, 'd')
        }
        else {
            return moment().subtract(today + 4, 'd')
        }
    };
    // Function to get most recent period based on number of months (quarter, semeseter, or year)
    function getPeriod(numMonths) {
        thisMonth = moment().month();
        return [moment().startOf('month').subtract(numMonths + (thisMonth % numMonths), 'months'), moment().startOf('month').subtract(thisMonth % numMonths, 'months').subtract(1, 'days')]
    }
    
    // Choose which dates are selected according to URL parameters and display them in datepicker
    start = getUrlParameter('datestart');
    start = moment(start);
    end = getUrlParameter('dateend');
    end = moment(end);

    $('#reportrange span').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY'));
    $('#reportrangespan').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY')); 
    
    $('#reportrange').daterangepicker({
        startDate: start,
        endDate: end,
        ranges: {
            'Past Week': [get_last_wed().subtract(1, 'weeks'), get_last_wed().subtract(1, 'days')],
            'Past Month': [moment().startOf('month').subtract(1, 'months'), moment().startOf('month').subtract(1, 'days')],
            'Past Quarter': getPeriod(3),
            'Past Semester': getPeriod(6),
            'Past Year': getPeriod(12)
        }
    }, refresh_page);

    /////////////////////////////////////// SET UP MENU BAR URLS BASED ON CURRENT PARAMETERS /////////////////////////////
    function getMenuUrl(base) {
        if (base == '/overview' || base == '/public') {
            return base + '?datestart=' + getUrlParameter('datestart') + '&dateend=' + getUrlParameter('dateend') + "&durationstart=" + getUrlParameter('durationstart') + "&durationend=" + getUrlParameter('durationend');
        }
        else {
            return base + '?datestart=' + getUrlParameter('datestart') + '&dateend=' + getUrlParameter('dateend');
        }
    };
    function setUpMenu() {
        var menuButtons = ['overview', 'public', 'hcreports', 'download'];
        for (i=0; i < menuButtons.length; i++) {
            document.getElementById(menuButtons[i] + 'link').href = getMenuUrl('/' + menuButtons[i]);
        }
        return false;
    };
    setUpMenu();
};
