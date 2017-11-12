$(document).ready(function() {
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

    // Set up default date ranges in datepicker
    var start = moment().subtract(1, 'months');
    var end = moment();
    // Choose which dates are selected (either according to URL parameters or, if no parameters, by default) and display them in datepicker
    if (getUrlParameter('datestart') != true) {
        start = getUrlParameter('datestart');
        start = moment(start);
    };
    if (getUrlParameter('dateend') != true) {
        end = getUrlParameter('dateend');
        end = moment(end);
    };
    $('#reportrange span').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY'));
    $('#reportrangespan').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY')); 

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
    // Set up default ranges in datepicker
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

    // Set up menu bar with current URL parameters
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
});
