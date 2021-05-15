// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

const COLORS_LIGHT = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e','#e70000','#e15d03', '#fff69a',];
const COLORS_DARK = ['#2e59d9', '#17a673', '#2c9faf', '#deaf38', '#ce0018', '#ca5302', '#e5dd8a'];

function number_format(number, decimals, dec_point, thousands_sep) {
  // *     example: number_format(1234.56, 2, ',', ' ');
  // *     return: '1 234,56'
  number = (number + '').replace(',', '').replace(' ', '');
  var n = !isFinite(+number) ? 0 : +number,
    prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
    sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
    dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
    s = '',
    toFixedFix = function(n, prec) {
      var k = Math.pow(10, prec);
      return '' + Math.round(n * k) / k;
    };
  // Fix for IE parseFloat(0.55).toFixed(0) = 0;
  s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
  if (s[0].length > 3) {
    s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
  }
  if ((s[1] || '').length < prec) {
    s[1] = s[1] || '';
    s[1] += new Array(prec - s[1].length + 1).join('0');
  }
  return s.join(dec);
}

function pick_colors(n){
    let light = [];
    let dark = [];

    for (let i = 0; i < n; i++){
        let color_idx = i % COLORS_LIGHT.length;
        light.push(COLORS_LIGHT[color_idx]);
        dark.push(COLORS_DARK[color_idx]);
    }

    return {light, dark};
}

// Pie Charts
for (const [key, value] of Object.entries(piecharts)) {

    const ctx = document.getElementById(key);
    let colors = pick_colors(value['data'].length);

    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: value['labels'],
        datasets: [{
          data: value['data'],
          backgroundColor: colors.light,
          hoverBackgroundColor: colors.dark,
          hoverBorderColor: "rgba(234, 236, 244, 1)",
        }],
      },
      options: {
        maintainAspectRatio: false,
        tooltips: {
          backgroundColor: "rgb(255,255,255)",
          bodyFontColor: "#858796",
          borderColor: '#dddfeb',
          borderWidth: 1,
          xPadding: 15,
          yPadding: 15,
          displayColors: false,
          caretPadding: 10,
          callbacks: {
            label: function(tooltipItem, chart) {
             var val = chart.datasets[tooltipItem.datasetIndex].data[tooltipItem.index];
             return CURRENCY_SYM + number_format(val);
            }
        }
        },
        legend: {
          display: true 
        },
        cutoutPercentage: 80,
      },
    });
}


// Area chart
function makeAreaChart(element_id, datasets, labels, is_small, is_stacked){
  var ctx = document.getElementById(element_id);

  let colors = pick_colors(datasets.length);
  let _datasets = [];
  for (let i=0; i < datasets.length; i++){
      _datasets.push(
        {
            label: datasets[i].label,
            lineTension: 0.3,
            backgroundColor: colors.light[i],
            borderColor: colors.dark[i],
            pointRadius: is_small ? 0.3 : 3,
            pointBackgroundColor: colors.dark[i],
            pointBorderColor: colors.dark[i],
            pointHoverRadius: 5,
            pointHoverBackgroundColor: colors.dark[i],
            pointHoverBorderColor: colors.dark[i],
            pointHitRadius: 10,
            pointBorderWidth: 2,
            data: datasets[i].data,
            fill: is_stacked,
        }
      );
  }
  console.log(_datasets)
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: _datasets,
    },
    options: {
      maintainAspectRatio: false,
      layout: {
        padding: {
          left: 10,
          right: 25,
          top: 25,
          bottom: 0
        }
      },
      scales: {
        xAxes: [{
          time: {
            unit: 'date'
          },
          gridLines: {
            display: false,
            drawBorder: false
          },
          ticks: {
            maxTicksLimit: 7
          }
        }],
        yAxes: [{
          stacked: is_stacked,
          ticks: {
            maxTicksLimit: 5,
            padding: 10,
            // Include a dollar sign in the ticks
            callback: function(value, index, values) {
              return CURRENCY_SYM + number_format(value);
            }
          },
          gridLines: {
            color: "rgb(234, 236, 244)",
            zeroLineColor: "rgb(234, 236, 244)",
            drawBorder: false,
            borderDash: [2],
            zeroLineBorderDash: [2]
          }
        }],
      },
      legend: {
        display: false
      },
      tooltips: {
        backgroundColor: "rgb(255,255,255)",
        bodyFontColor: "#858796",
        titleMarginBottom: 10,
        titleFontColor: '#6e707e',
        titleFontSize: 14,
        borderColor: '#dddfeb',
        borderWidth: 1,
        xPadding: 15,
        yPadding: 15,
        displayColors: false,
        intersect: false,
        mode: 'index',
        caretPadding: 10,
        callbacks: {
          label: function(tooltipItem, chart) {
            var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
            return datasetLabel + ': ' + CURRENCY_SYM + number_format(tooltipItem.yLabel);
          }
        }
      }
    }
  });
}

for (const [key, value] of Object.entries(areacharts)) {
    makeAreaChart(key, value['datasets'], value['labels'], true, false);
}

for (const [key, value] of Object.entries(areacharts_stacked)) {
    makeAreaChart(key, value['datasets'], value['labels'], true, true);
}

makeAreaChart("balance_chart", balances["datasets"], balances["labels"], false, true)
makeAreaChart("earnings_chart", earnings["datasets"], earnings["labels"], false, true)
