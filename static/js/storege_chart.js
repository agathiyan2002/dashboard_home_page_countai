
try {
  var systemStorageData = JSON.parse(document.getElementById('pie-chart').getAttribute('data-system-storege'));
  // console.log(systemStorageData);

  // Extract data for 'home' and 'root' from the system_storage
  var homeStorage = systemStorageData['home'];
  var rootStorage = systemStorageData['root'];

  // Set the total storage for each partition
  var totalHomeStorage = homeStorage['Total storage'];
  var totalRootStorage = rootStorage['Total storage'];

  // Function to format storage values
  function formatStorage(value) {
    return value.toFixed(0) + ' GB';
  }

  // Build the dynamic content
  var storageInfoContent = `
                        Root ${formatStorage(rootStorage['Available storage'])} / ${formatStorage(totalRootStorage)} <br>
                        Home ${formatStorage(homeStorage['Available storage'])} / ${formatStorage(totalHomeStorage)}
                    `;

  // Update the content within the storage-info div
  document.getElementById('storage-info').innerHTML = storageInfoContent;
} catch (error) {
  console.error("Error parsing JSON:", error);
}






try {
  // Parse the JSON data from the attribute
  var system_storege_data = JSON.parse(document.getElementById('pie-chart').getAttribute('data-system-storege'));
  // console.log(system_storege_data);

} catch (error) {
  console.error("Error parsing JSON:", error);
}

// Extract data for 'home' and 'root' from the system_storege_data
var homeStorage = system_storege_data['home'];
var rootStorage = system_storege_data['root'];

// Set the total storage for each partition
var totalHomeStorage = homeStorage['Total storage'];
var totalRootStorage = rootStorage['Total storage'];

// Calculate percentages
var percentageHome = (homeStorage['Used storage'] / totalHomeStorage) * 100;
var percentageRoot = (rootStorage['Used storage'] / totalRootStorage) * 100;

var options = {
  chart: {
    type: 'radialBar',
    height: 280, // Adjust the height as needed
    width: '100%', // Adjust the width as needed
  },
  series: [percentageHome.toFixed(2), percentageRoot.toFixed(2)],
  labels: ['Home Storage', 'Root Storage'],
  plotOptions: {
    radialBar: {
      hollow: {
        size: '70%',
      },
      dataLabels: {
        name: {
          offsetY: -10,
          show: true,
          color: '#888',
          fontSize: '13px',
        },
        value: {
          color: '#111',
          fontSize: '20px', // Adjust the font size as needed
          show: true,
        },
      },
    },
  },
  colors: ['#3498db', '#e74c3c'], // Set different colors for Home and Root storage
  tooltip: {
    enabled: true,
    y: {
      formatter: function (val) {
        return val + "%";
      },
    },
  },
};

// Use the correct ID here
var chart = new ApexCharts(document.querySelector("#pie-chart"), options);
chart.render();
