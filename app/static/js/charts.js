/**
 * Analytics & Visualizations Engine using Chart.js
 */
let tierChartInstance = null;
let scoreDistChartInstance = null;

function renderAnalyticsCharts(stats, allStudents) {
  if (typeof Chart === 'undefined') return;

  // Chart Global Config
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = "'Outfit', 'Inter', sans-serif";

  // 1. Tier Distribution Donut Chart
  const tierCtx = document.getElementById('tierDonutChart');
  if (tierCtx) {
    if (tierChartInstance) {
      tierChartInstance.destroy();
    }

    const advCount = stats.advanced_count || 0;
    const avgCount = stats.average_count || 0;
    const slowCount = stats.slow_count || 0;

    tierChartInstance = new Chart(tierCtx, {
      type: 'doughnut',
      data: {
        labels: ['Advanced Learners', 'Average Learners', 'Slow Learners'],
        datasets: [{
          data: [advCount, avgCount, slowCount],
          backgroundColor: ['#10b981', '#0ea5e9', '#f43f5e'],
          borderColor: '#0f172a',
          borderWidth: 3,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 16,
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.9)',
            titleColor: '#fff',
            bodyColor: '#cbd5e1',
            padding: 12,
            borderColor: 'rgba(148, 163, 184, 0.2)',
            borderWidth: 1
          }
        },
        cutout: '72%'
      }
    });
  }

  // 2. Score / CGPA Distribution Bar Chart
  const scoreCtx = document.getElementById('scoreDistChart');
  if (scoreCtx) {
    if (scoreDistChartInstance) {
      scoreDistChartInstance.destroy();
    }

    // Bucket into brackets: < 5.0, 5.0-5.99, 6.0-6.99, 7.0-7.99, 8.0-8.99, 9.0-10.0
    // Or for CIE marks: < 8, 8-11, 12-14, 15-17, 18-20
    const hasCie = allStudents.some(s => s.cie_marks !== null);
    const hasCgpa = allStudents.some(s => s.cgpa !== null);

    let labels = [];
    let counts = [];

    if (hasCgpa) {
      labels = ['< 6.0 (Slow)', '6.0 - 6.99', '7.0 - 7.49', '7.5 - 8.49', '8.5 - 10.0 (Top)'];
      counts = [0, 0, 0, 0, 0];
      allStudents.forEach(s => {
        const val = s.cgpa || s.sgpa || 0;
        if (val < 6.0 || s.backlog_count > 0) counts[0]++;
        else if (val < 7.0) counts[1]++;
        else if (val < 7.5) counts[2]++;
        else if (val < 8.5) counts[3]++;
        else counts[4]++;
      });
    } else if (hasCie) {
      labels = ['< 10 Marks (Slow)', '10 - 12 Marks', '13 - 14 Marks', '15 - 17 Marks', '18 - 20 Marks (Top)'];
      counts = [0, 0, 0, 0, 0];
      allStudents.forEach(s => {
        const val = s.cie_marks || 0;
        if (val < 10) counts[0]++;
        else if (val <= 12) counts[1]++;
        else if (val <= 14) counts[2]++;
        else if (val <= 17) counts[3]++;
        else counts[4]++;
      });
    } else {
      labels = ['Slow Tier', 'Average Tier', 'Advanced Tier'];
      counts = [stats.slow_count || 0, stats.average_count || 0, stats.advanced_count || 0];
    }

    scoreDistChartInstance = new Chart(scoreCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Number of Students',
          data: counts,
          backgroundColor: [
            'rgba(244, 63, 94, 0.75)',
            'rgba(14, 165, 233, 0.65)',
            'rgba(14, 165, 233, 0.85)',
            'rgba(16, 185, 129, 0.75)',
            'rgba(16, 185, 129, 0.95)'
          ],
          borderRadius: 8,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(148, 163, 184, 0.1)'
            },
            ticks: {
              stepSize: 5
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.9)',
            padding: 12,
            borderColor: 'rgba(148, 163, 184, 0.2)',
            borderWidth: 1
          }
        }
      }
    });
  }
}
