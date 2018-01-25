function setUpChart(type, labels, data, seriesnames, colors, title, legend, minx, maxx, xlabel, canvasid) {
    if (type == 'line') {
        var ctx = document.getElementById(canvasid);
        ctx.height = 100;
        var datasets = [];
        for (i = 0; i < data.length; i++) {
            datasets.push({
                label: seriesnames[i],
                data: data[i],
                borderColor: colors[i],
                backgroundColor: colors[i],
                borderWidth: 2,
                pointRadius: 1,
                pointHoverRadius: 6,
                fill: false
            })
        };
        if (legend == 'True') {
            var legend = {display: true, position: 'right'}
        }
        else {
            var legend = {display: false}
        }
        if (minx != 'None' && maxx != 'None') {
            var scales = {
                    xAxes: [{
                        type: "time",
                        time: {
                            min: minx,
                            max: maxx
                        }
                    }]
                }
        }
        else if (xlabel != 'None') {
            var scales = {
                xAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: xlabel
                    }
                }]
            } 
        }
        else {
            var scales = {}
        }
        var myChart = new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                legend: legend,
                title: {
                    display: true,
                    text: title,
                    fontSize: 18,
                    fontFamily: 'Helvetica Neue'
                },
                scales: scales
            }
        });
    }
    else {
        var ctx = document.getElementById(canvasid);
        ctx.height = 100;
        var datasets = [];
        datasets.push({
            label: "Number of Calls",
            data: data,
            backgroundColor: colors
        })
        var legend = {display: true, position: 'right'};
        var myChart = new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                legend: legend,
                title: {
                    display: true,
                    text: title,
                    fontSize: 18,
                    fontFamily: 'Helvetica Neue'
                }
            }
        });
    }

};