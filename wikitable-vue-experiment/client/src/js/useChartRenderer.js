import { renderLineChart, renderBarChart } from '@/js/chartUtils'

export function useChartRenderer() {
  const renderChart = (container, data) => {
    if (!container || !data) return
    
    try {
      container.innerHTML = ''
      
      switch (data.chartType) {
        case 'line':
          renderLineChart(container, data)
          break
        case 'bar':
          renderBarChart(container, data)
          break
        default:
          renderLineChart(container, data)
      }
    } catch (error) {
      console.error('图表渲染失败:', error)
      container.innerHTML = '<div class="chart-error">渲染失败</div>'
    }
  }

  return { renderChart }
}