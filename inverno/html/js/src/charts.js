'use strict';

// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

const COLORS_LIGHT = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e70000', '#e15d03', '#fff69a',];
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
    toFixedFix = function (n, prec) {
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

function pick_colors(n) {
  let light = [];
  let dark = [];

  for (let i = 0; i < n; i++) {
    let color_idx = i % COLORS_LIGHT.length;
    light.push(COLORS_LIGHT[color_idx]);
    dark.push(COLORS_DARK[color_idx]);
  }

  return { light, dark };
}

// Pie Charts
function makePieChart(key, data, labels) {

  const ctx = document.getElementById(key);
  let colors = pick_colors(data.length);

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
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
          label: function (tooltipItem, chart) {
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
function makeAreaChart(element_id, datasets, labels, config) {
  var ctx = document.getElementById(element_id);

  let colors = pick_colors(datasets.length);
  let _datasets = [];
  for (let i = 0; i < datasets.length; i++) {
    _datasets.push(
      {
        label: datasets[i].label,
        lineTension: 0.3,
        backgroundColor: colors.light[i],
        borderColor: colors.dark[i],
        pointRadius: config.is_small ? 0.3 : 3,
        pointBackgroundColor: colors.dark[i],
        pointBorderColor: colors.dark[i],
        pointHoverRadius: 5,
        pointHoverBackgroundColor: colors.dark[i],
        pointHoverBorderColor: colors.dark[i],
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: datasets[i].data,
        fill: config.is_stacked ? true : false,
      }
    );
  }
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
          stacked: config.is_stacked,
          ticks: {
            maxTicksLimit: 5,
            padding: 10,
            // Include a dollar sign in the ticks
            callback: function (value, index, values) {
              switch (config.format) {
                case "percent":
                  return number_format(value) + " %";
                default:
                  return CURRENCY_SYM + number_format(value);
              }
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
        display: config.show_legend ? true : false,
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
          label: function (tooltipItem, chart) {
            var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
            switch (config.format) {
              case "percent":
                return datasetLabel + ': ' + number_format(tooltipItem.yLabel, 2) + " %";
              default:
                return datasetLabel + ': ' + CURRENCY_SYM + number_format(tooltipItem.yLabel, 2);
            }
          }
        }
      }
    }
  });
}



makeAreaChart("balance_chart", balances["datasets"], balances["labels"], { is_stacked: true })
makeAreaChart("earnings_chart", earnings["datasets"], earnings["labels"], { is_stacked: true })

class AttrChart extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selected: 0,
    };
  }

  getChartID(report) {
    return (
      this.props.attr_name + "_" +
      report.name + "_" +
      report.type
    );
  }

  getReports() {
    switch (this.props.report.type) {
      case 'multi':
        return this.props.report.reports;
      default:
        return [this.props.report];
    }
  }

  componentDidMount() {
    this.renderAllCharts();
  }

  componentDidUpdate() {
    this.renderAllCharts();
  }

  renderAllCharts() {
    this.getReports().forEach(
      (report) => this.renderChart(report)
    )
  }

  renderChart(report) {
    const chart_id = this.getChartID(report)

    switch (report.type) {
      case 'piechart':
        makePieChart(chart_id, report.data, report.labels);
        break;
      case 'areachart':
        makeAreaChart(chart_id, report.datasets, report.labels,
          { show_legend: report.show_legend, is_small: true, format: report.format })
        break;
      case 'areachart_stacked':
        makeAreaChart(chart_id, report.datasets, report.labels,
          { show_legend: report.show_legend, is_small: true, is_stacked: true, format: report.format });
        break;
      default:
        return;
    }
  }

  render() {
    return (
      <div className="card shadow mb-4">
        <div
          className="card-header py-3 d-flex flex-row align-items-center justify-content-between">
          <div className="row align-items-center">

            <div className="col-auto" style={{ paddingRight: '0' }}>
              <h6 className="m-0 font-weight-bold text-primary">{this.props.report.name}</h6>
            </div>

            <div className="col-auto">
              <i className="fas fa-info-circle text-gray-300"
                data-bs-toggle="tooltip"
                data-bs-placement="top"
                title={this.props.report.help}
              ></i>
            </div>

            {this.getReports().length > 1 ?
              (
                <div className="dropdown mb-4"
                  style={{ position: "absolute", right: "10px", top: "10px" }}>
                  <button className="btn btn-primary dropdown-toggle" type="button"
                    id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                    {this.getReports()[this.state.selected].name}
                  </button>
                  <div className="dropdown-menu animated--fade-in" aria-labelledby="dropdownMenuButton">
                    {
                      this.getReports().map(
                        (report, idx) => (
                          <a key={idx} className="dropdown-item" onClick={() => this.setState({ selected: idx })}>
                            {report.name}
                          </a>
                        )
                      )
                    }
                  </div>
                </div>)

              : <div />
            }
          </div>
        </div>
        <div className="card-body" style={{ height: '500px' }}>
          <div className="card-body" style={{ height: '500px' }}>
            <div className="chart-pie pt-4" style={{ width: '100%', height: '90%' }}>
              {
                this.getReports().map(
                  (report, idx) => (
                    <canvas key={idx} id={this.getChartID(report)}
                      style={{ "display": idx == this.state.selected ? "block" : "none" }}>
                    </canvas>
                  )
                )
              }
            </div>
          </div>
        </div>
      </div>
    );
  }
}

class AttrReports extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div>
        <div className="row">
          <div className="col-lg-12 mt-4 mb-1">
            <div className="card bg-primary text-white shadow">
              <div className="card-body">
                <div className="row">
                  <div className="col-auto" style={{ paddingRight: '0' }}>
                    <h4>{this.props.attr_data.name}</h4>
                  </div>
                  <div className="col-auto">
                    <i className="fas fa-info-circle text-gray-300"
                      data-bs-toggle="tooltip"
                      data-bs-placement="top"
                      style={{ verticalAlign: 'bottom' }}
                      title={"Reports for attribute " + this.props.attr_data.name}></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="row">
          {this.props.attr_data.reports.map(
            (report, idx) => (
              <div className="col-xl-4 col-lg-5" key={idx}>
                <AttrChart attr_name={this.props.attr_data.name} report={report} />
              </div>
            )
          )}
        </div>
      </div>

    )
  }
}

class AllAttrsReports extends React.Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    $('[data-toggle="tooltip"]').tooltip();
  }

  componentDidUpdate() {
    $('[data-toggle="tooltip"]').tooltip();
  }

  render() {
    return (
      <div>
        {this.props.reports.map(
          (attr, idx) => (
            <AttrReports attr_data={attr} key={idx} />
          )
        )}
      </div>

    )
  }
}
const domContainer = document.querySelector('#reports');
ReactDOM.render(<AllAttrsReports reports={reports_data} />, domContainer);






