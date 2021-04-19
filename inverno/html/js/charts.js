// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

// Pie Charts
const BACKGROUND_COLORS = ['#4e73df', '#1cc88a', '#36b9cc'];
const HOVER_BACKFROUND_COLORS = ['#2e59d9', '#17a673', '#2c9faf'];

for (const [key, value] of Object.entries(piecharts)) {
    console.log(`${key}: ${value}`);

    const ctx = document.getElementById(key);
    let backgroundColor = [];
    let hoverBackgroundColor = [];
    for (let i = 0; i < value['data'].length; i++){
        let color_idx = i % BACKGROUND_COLORS.length;
        console.log(color_idx);
        backgroundColor.push(BACKGROUND_COLORS[color_idx]);
        hoverBackgroundColor.push(HOVER_BACKFROUND_COLORS[color_idx]);
    }
    console.log(backgroundColor)

    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: value['labels'],
        datasets: [{
          data: value['data'],
          backgroundColor,
          hoverBackgroundColor,
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
        },
        legend: {
          display: true 
        },
        cutoutPercentage: 80,
      },
    });
}
