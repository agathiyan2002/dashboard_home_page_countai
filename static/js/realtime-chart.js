// realtime-chart.js

try {
    // Parse the JSON data from the attribute
    var uptimeData = JSON.parse(document.getElementById('realtime-chart').getAttribute('data-uptime'));
    // Continue with your code using uptimeData
    // console.log(uptimeData);
} catch (error) {
    console.error("Error parsing JSON:", error);
}

// Sample data for each series
var cpuUtilizationData = uptimeData.map(entry => ({ x: new Date(entry.timestamp).getTime(), y: entry.cpu_utilization }));
var gpuUtilizationData = uptimeData.map(entry => ({ x: new Date(entry.timestamp).getTime(), y: entry.gpu_utilization }));
var machineStatusData = uptimeData.map(entry => ({ x: new Date(entry.timestamp).getTime(), y: entry.machine_status }));
var memoryUtilizationData = uptimeData.map(entry => ({ x: new Date(entry.timestamp).getTime(), y: entry.memory_utilization }));
var ramUsageData = uptimeData.map(entry => ({ x: new Date(entry.timestamp).getTime(), y: entry.ram_usage }));
var temperatureData = uptimeData.map(entry => ({ x: new Date(entry.timestamp).getTime(), y: entry.temperature }));

// Configuration for the real-time line chart
var options = {
    chart: {
        height: 350,
        width: '100%', // Set the width to 100%
        type: 'line',
        animations: {
            enabled: true,
            easing: 'linear',
            dynamicAnimation: {
                speed: 1000
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
            autoSelected: 'zoom',
        },
        colors: ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948'] // Different shades of blue
    },
    series: [
        { name: 'CPU Utilization', data: cpuUtilizationData, lineWidth: 1 },
        { name: 'GPU Utilization', data: gpuUtilizationData, lineWidth: 1 },
        { name: 'Machine Status', data: machineStatusData, lineWidth: 1 },
        { name: 'Memory Utilization', data: memoryUtilizationData, lineWidth: 1 },
        { name: 'RAM Usage', data: ramUsageData, lineWidth: 1 },
        { name: 'Temperature', data: temperatureData, lineWidth: 1 }
    ],
    xaxis: {
        type: 'datetime',
    },
    yaxis: {
        max: 100.0 // Set a reasonable maximum value for the y-axis
    },
    legend: {
        show: true,
        position: 'bottom' // Set the legend position to 'bottom'
    }
};

// Initialize the real-time line chart
var chart = new ApexCharts(document.querySelector("#realtime-chart"), options);
chart.render();
