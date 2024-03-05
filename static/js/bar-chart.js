// bar-chart.js

try {
    var graphData = JSON.parse(document.getElementById('bar-chart').getAttribute('data-bar-chart-data'));
    // console.log(graphData);

    // Extract data from JSON
    var hours = graphData.map(item => item.hour);
    var defectCounts = graphData.map(item => item.defect_count);
    var rotationCounts = graphData.map(item => item.rotation_count);

    // Configuration for the bar chart
    var options = {
        chart: {
            type: 'bar',
            height: 345, // Set the desired height in pixels
            zoom: {
                enabled: true,
                type: 'x',
                zoomedArea: {
                    fill: {
                        color: 'red',
                        opacity: 0.4
                    },
                    stroke: {
                        color: 'blue',
                        opacity: 0.7,
                        width: 1
                    }
                }
            }
        },
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: '50%',
                endingShape: 'flat'
            },
        },
        series: [
            {
                name: 'Rotation Count',
                data: rotationCounts,
                color: '#3498db' // Change the color for Rotation Count (blue)
            },
            {
                name: 'Defect Count',
                data: defectCounts,
                color: '#e74c3c', // Change the color for Defect Count (red)
                type: 'line', // Use a line series for "Defect Count"
                yAxisIndex: 1 // Assign to the secondary y-axis
            }
        ],
        xaxis: {
            categories: hours
        },
        yaxis: [
            {}, // Primary y-axis for "Rotation Count"
            {
                opposite: true, // Position the secondary y-axis on the right
                show: true,
                seriesName: 'Defect Count', // Match the series name
                title: {
                    text: 'Defect Count',
                    style: {
                        color: '#000000' // Change the color for the Defect Count text to black
                    }
                }
            }
        ],
        dataLabels: {
            style: {
                colors: ['#000000', '#000000'] // Change the colors for data labels to black
            }
        },
        toolbar: {
            show: true,
            tools: {
                download: false,
                selection: true,
                zoom: true,
                zoomin: true,
                zoomout: true,
                pan: true,
                reset: true
            },
            autoSelected: 'zoom'
        }
    };

    var chart = new ApexCharts(document.querySelector("#bar-chart"), options);
    chart.render();
} catch (error) {
    console.error("Error parsing JSON:", error);
}
