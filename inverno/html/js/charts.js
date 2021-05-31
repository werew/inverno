'use strict';

// Set new default font family and font color to mimic Bootstrap's default styling

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

var COLORS_LIGHT = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e70000', '#e15d03', '#fff69a'];
var COLORS_DARK = ['#2e59d9', '#17a673', '#2c9faf', '#deaf38', '#ce0018', '#ca5302', '#e5dd8a'];

function number_format(number, decimals, dec_point, thousands_sep) {
  // *     example: number_format(1234.56, 2, ',', ' ');
  // *     return: '1 234,56'
  number = (number + '').replace(',', '').replace(' ', '');
  var n = !isFinite(+number) ? 0 : +number,
      prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
      sep = typeof thousands_sep === 'undefined' ? ',' : thousands_sep,
      dec = typeof dec_point === 'undefined' ? '.' : dec_point,
      s = '',
      toFixedFix = function toFixedFix(n, prec) {
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
  var light = [];
  var dark = [];

  for (var i = 0; i < n; i++) {
    var color_idx = i % COLORS_LIGHT.length;
    light.push(COLORS_LIGHT[color_idx]);
    dark.push(COLORS_DARK[color_idx]);
  }

  return { light: light, dark: dark };
}

// Pie Charts
function makePieChart(key, data, labels) {

  var ctx = document.getElementById(key);
  var colors = pick_colors(data.length);

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors.light,
        hoverBackgroundColor: colors.dark,
        hoverBorderColor: "rgba(234, 236, 244, 1)"
      }]
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
          label: function label(tooltipItem, chart) {
            var val = chart.datasets[tooltipItem.datasetIndex].data[tooltipItem.index];
            return CURRENCY_SYM + number_format(val);
          }
        }
      },
      legend: {
        display: true
      },
      cutoutPercentage: 80
    }
  });
}

// Area chart
function makeAreaChart(element_id, datasets, labels, config) {
  var ctx = document.getElementById(element_id);

  var colors = pick_colors(datasets.length);
  var _datasets = [];
  for (var i = 0; i < datasets.length; i++) {
    _datasets.push({
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
      fill: config.is_stacked ? true : false
    });
  }
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: _datasets
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
            callback: function callback(value, index, values) {
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
        }]
      },
      legend: {
        display: config.show_legend ? true : false
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
          label: function label(tooltipItem, chart) {
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

makeAreaChart("balance_chart", balances["datasets"], balances["labels"], { is_stacked: true });
makeAreaChart("earnings_chart", earnings["datasets"], earnings["labels"], { is_stacked: true });

var AttrChart = function (_React$Component) {
  _inherits(AttrChart, _React$Component);

  function AttrChart(props) {
    _classCallCheck(this, AttrChart);

    var _this = _possibleConstructorReturn(this, (AttrChart.__proto__ || Object.getPrototypeOf(AttrChart)).call(this, props));

    _this.state = {
      selected: 0
    };
    return _this;
  }

  _createClass(AttrChart, [{
    key: 'getChartID',
    value: function getChartID(report) {
      return this.props.attr_name + "_" + report.name + "_" + report.type;
    }
  }, {
    key: 'getReports',
    value: function getReports() {
      switch (this.props.report.type) {
        case 'multi':
          return this.props.report.reports;
        default:
          return [this.props.report];
      }
    }
  }, {
    key: 'componentDidMount',
    value: function componentDidMount() {
      this.renderAllCharts();
    }
  }, {
    key: 'componentDidUpdate',
    value: function componentDidUpdate() {
      this.renderAllCharts();
    }
  }, {
    key: 'renderAllCharts',
    value: function renderAllCharts() {
      var _this2 = this;

      this.getReports().forEach(function (report) {
        return _this2.renderChart(report);
      });
    }
  }, {
    key: 'renderChart',
    value: function renderChart(report) {
      var chart_id = this.getChartID(report);

      switch (report.type) {
        case 'piechart':
          makePieChart(chart_id, report.data, report.labels);
          break;
        case 'areachart':
          makeAreaChart(chart_id, report.datasets, report.labels, { show_legend: report.show_legend, is_small: true, format: report.format });
          break;
        case 'areachart_stacked':
          makeAreaChart(chart_id, report.datasets, report.labels, { show_legend: report.show_legend, is_small: true, is_stacked: true, format: report.format });
          break;
        default:
          return;
      }
    }
  }, {
    key: 'render',
    value: function render() {
      var _this3 = this;

      return React.createElement(
        'div',
        { className: 'card shadow mb-4' },
        React.createElement(
          'div',
          {
            className: 'card-header py-3 d-flex flex-row align-items-center justify-content-between' },
          React.createElement(
            'div',
            { className: 'row align-items-center' },
            React.createElement(
              'div',
              { className: 'col-auto', style: { paddingRight: '0' } },
              React.createElement(
                'h6',
                { className: 'm-0 font-weight-bold text-primary' },
                this.props.report.name
              )
            ),
            React.createElement(
              'div',
              { className: 'col-auto' },
              React.createElement('i', { className: 'fas fa-info-circle text-gray-300',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'top',
                title: this.props.report.help
              })
            ),
            this.getReports().length > 1 ? React.createElement(
              'div',
              { className: 'dropdown mb-4',
                style: { position: "absolute", right: "10px", top: "10px" } },
              React.createElement(
                'button',
                { className: 'btn btn-primary dropdown-toggle', type: 'button',
                  id: 'dropdownMenuButton', 'data-toggle': 'dropdown', 'aria-haspopup': 'true', 'aria-expanded': 'false' },
                this.getReports()[this.state.selected].name
              ),
              React.createElement(
                'div',
                { className: 'dropdown-menu animated--fade-in', 'aria-labelledby': 'dropdownMenuButton' },
                this.getReports().map(function (report, idx) {
                  return React.createElement(
                    'a',
                    { key: idx, className: 'dropdown-item', onClick: function onClick() {
                        return _this3.setState({ selected: idx });
                      } },
                    report.name
                  );
                })
              )
            ) : React.createElement('div', null)
          )
        ),
        React.createElement(
          'div',
          { className: 'card-body', style: { height: '500px' } },
          React.createElement(
            'div',
            { className: 'card-body', style: { height: '500px' } },
            React.createElement(
              'div',
              { className: 'chart-pie pt-4', style: { width: '100%', height: '90%' } },
              this.getReports().map(function (report, idx) {
                return React.createElement('canvas', { key: idx, id: _this3.getChartID(report),
                  style: { "display": idx == _this3.state.selected ? "block" : "none" } });
              })
            )
          )
        )
      );
    }
  }]);

  return AttrChart;
}(React.Component);

var AttrReports = function (_React$Component2) {
  _inherits(AttrReports, _React$Component2);

  function AttrReports(props) {
    _classCallCheck(this, AttrReports);

    return _possibleConstructorReturn(this, (AttrReports.__proto__ || Object.getPrototypeOf(AttrReports)).call(this, props));
  }

  _createClass(AttrReports, [{
    key: 'render',
    value: function render() {
      var _this5 = this;

      return React.createElement(
        'div',
        null,
        React.createElement(
          'div',
          { className: 'row' },
          React.createElement(
            'div',
            { className: 'col-lg-12 mt-4 mb-1' },
            React.createElement(
              'div',
              { className: 'card bg-primary text-white shadow' },
              React.createElement(
                'div',
                { className: 'card-body' },
                React.createElement(
                  'div',
                  { className: 'row' },
                  React.createElement(
                    'div',
                    { className: 'col-auto', style: { paddingRight: '0' } },
                    React.createElement(
                      'h4',
                      null,
                      this.props.attr_data.name
                    )
                  ),
                  React.createElement(
                    'div',
                    { className: 'col-auto' },
                    React.createElement('i', { className: 'fas fa-info-circle text-gray-300',
                      'data-bs-toggle': 'tooltip',
                      'data-bs-placement': 'top',
                      style: { verticalAlign: 'bottom' },
                      title: "Reports for attribute " + this.props.attr_data.name })
                  )
                )
              )
            )
          )
        ),
        React.createElement(
          'div',
          { className: 'row' },
          this.props.attr_data.reports.map(function (report, idx) {
            return React.createElement(
              'div',
              { className: 'col-xl-4 col-lg-5', key: idx },
              React.createElement(AttrChart, { attr_name: _this5.props.attr_data.name, report: report })
            );
          })
        )
      );
    }
  }]);

  return AttrReports;
}(React.Component);

var AllAttrsReports = function (_React$Component3) {
  _inherits(AllAttrsReports, _React$Component3);

  function AllAttrsReports(props) {
    _classCallCheck(this, AllAttrsReports);

    return _possibleConstructorReturn(this, (AllAttrsReports.__proto__ || Object.getPrototypeOf(AllAttrsReports)).call(this, props));
  }

  _createClass(AllAttrsReports, [{
    key: 'componentDidMount',
    value: function componentDidMount() {
      $('[data-toggle="tooltip"]').tooltip();
    }
  }, {
    key: 'componentDidUpdate',
    value: function componentDidUpdate() {
      $('[data-toggle="tooltip"]').tooltip();
    }
  }, {
    key: 'render',
    value: function render() {
      return React.createElement(
        'div',
        null,
        this.props.reports.map(function (attr, idx) {
          return React.createElement(AttrReports, { attr_data: attr, key: idx });
        })
      );
    }
  }]);

  return AllAttrsReports;
}(React.Component);

var domContainer = document.querySelector('#reports');
ReactDOM.render(React.createElement(AllAttrsReports, { reports: reports_data }), domContainer);