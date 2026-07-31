// chartUtils.js
import * as d3 from "d3";

// 渲染折线图（line）
export function renderLineChart(chartRef, data, options) {
    if (!chartRef) {
        console.error("图表容器未找到");
        return;
    }

    console.log("渲染折线图数据:", data);

    const margin = { top: 20, right: 100, bottom: 50, left: 50 };
    const width = 800 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    // 清空之前的图表
    d3.select(chartRef).html("");

    // 创建 SVG 容器
    const svg = d3
        .select(chartRef)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const labels = data.labels;
    const datasets = data.datasets;

    // 清理数据
    const cleanedLabels = labels.map(label =>
        label === undefined || label === null ? "" : label
    );
    const cleanedDatasets = datasets.map(dataset => ({
        ...dataset,
        data: dataset.data.map(d => (d === undefined || d === null ? 0 : d))
    }));

    console.log("清理后的 labels:", cleanedLabels);
    console.log("清理后的 datasets:", cleanedDatasets);

    // 设置 X 轴比例尺
    const x = d3
        .scaleBand()
        .domain(cleanedLabels)
        .range([0, width])
        .padding(0.1);

    // 设置 Y 轴比例尺
    const y = d3
        .scaleLinear()
        .domain([0, d3.max(cleanedDatasets.flatMap(d => d.data))])
        .range([height, 0]);

    console.log("X 比例尺 domain:", x.domain());
    console.log("X 比例尺 range:", x.range());
    console.log("Y 比例尺 domain:", y.domain());
    console.log("Y 比例尺 range:", y.range());

    // 添加 X 轴
    svg
        .append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

    // 添加 Y 轴
    svg.append("g").call(d3.axisLeft(y));

    // 添加 X 轴标题
    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", height + margin.bottom - 10)
        .style("text-anchor", "middle")
        .text(options.scales.x.title.text);

    // 添加 Y 轴标题
    svg
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", -margin.left + 20)
        .style("text-anchor", "middle")
        .text(options.scales.y.title.text);

    // 绘制折线
    cleanedDatasets.forEach(dataset => {
        const line = d3
            .line()
            .x((d, i) => {
                const xValue = x(cleanedLabels[i]) + x.bandwidth() / 2;
                if (isNaN(xValue)) {
                    console.error(
                        "无效的 x 值:",
                        xValue,
                        "labels[i]:",
                        cleanedLabels[i]
                    );
                }
                return xValue;
            })
            .y(d => {
                const yValue = y(d);
                if (isNaN(yValue)) {
                    console.error("无效的 y 值:", yValue, "d:", d);
                }
                return yValue;
            });

        svg
            .append("path")
            .datum(dataset.data)
            .attr("fill", "none")
            .attr("stroke", dataset.borderColor)
            .attr("stroke-width", 2)
            .attr("d", line);

        // 添加数据点
        svg
            .selectAll(`.dot-${CSS.escape(dataset.label)}`)
            .data(dataset.data)
            .enter()
            .append("circle")
            .attr("cx", (d, i) => {
                const cxValue = x(cleanedLabels[i]) + x.bandwidth() / 2;
                if (isNaN(cxValue)) {
                    console.error(
                        "无效的 cx 值:",
                        cxValue,
                        "labels[i]:",
                        cleanedLabels[i]
                    );
                }
                return cxValue;
            })
            .attr("cy", d => {
                const cyValue = y(d);
                if (isNaN(cyValue)) {
                    console.error("无效的 cy 值:", cyValue, "d:", d);
                }
                return cyValue;
            })
            .attr("r", 4)
            .attr("fill", dataset.borderColor);
    });

    // 添加图例
    const legend = svg
        .append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width + margin.right - 100}, 20)`);

    cleanedDatasets.forEach((dataset, index) => {
        const legendItem = legend
            .append("g")
            .attr("transform", `translate(0, ${index * 20})`);

        // 添加颜色方块
        legendItem
            .append("rect")
            .attr("width", 18)
            .attr("height", 18)
            .attr("fill", dataset.borderColor);

        // 添加标签
        legendItem
            .append("text")
            .attr("x", 24)
            .attr("y", 9)
            .attr("dy", "0.35em")
            .text(dataset.label)
            .style("font-size", "10px"); // 设置字体大小为16像素
    });
}

// 渲染柱状图（bar）
export function renderBarChart(chartRef, data) {
    if (!chartRef) {
        console.error("图表容器未找到");
        return;
    }

    console.log("渲染bar_chart数据:", data);

    // 定义最小尺寸
    const minWidth = 800;
    const minHeight = 300;

    // 获取容器的尺寸
    const container = d3.select(chartRef).node();
    const containerWidth = container.getBoundingClientRect().width;
    const containerHeight = container.getBoundingClientRect().height;

    // 使用容器尺寸或最小尺寸
    const width = Math.max(containerWidth, minWidth) - 100; // 减去 margin 的左右部分
    const height = Math.max(containerHeight, minHeight) - 70; // 减去 margin 的上下部分

    const margin = { top: 20, right: 100, bottom: 50, left: 50 };

    // 清空之前的图表
    d3.select(chartRef).html("");

    // 创建 SVG 容器
    const svg = d3
        .select(chartRef)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // X轴：使用 scaleBand 处理分类数据
    const x = d3
        .scaleBand()
        .domain(data.xAxis.data)
        .range([0, width])
        .padding(0.1);

    // Y轴：使用 scaleLinear 处理数值数据
    const y = d3
        .scaleLinear()
        .domain([0, d3.max(data.datasets, d => d3.max(d.data))])
        .range([height, 0]);

    // 颜色生成器
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // 添加 X 轴
    svg
        .append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x));

    // 添加 Y 轴
    svg.append("g").call(d3.axisLeft(y));

    // 添加 X 轴标注
    svg
        .append("text")
        .attr("class", "axis-label")
        .attr("x", width / 2)
        .attr("y", height + margin.bottom - 10)
        .style("text-anchor", "middle")
        .text(data.xAxis.label);

    // 添加 Y 轴标注
    svg
        .append("text")
        .attr("class", "axis-label")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", -margin.left + 20)
        .style("text-anchor", "middle")
        .text(data.yAxis.label);

    // 计算柱状图宽度
    const barWidth = x.bandwidth() / data.datasets.length;

    // 绘制柱状图
    data.datasets.forEach((dataset, i) => {
        svg
            .selectAll(`.bar-${i}`)
            .data(dataset.data)
            .enter()
            .append("rect")
            .attr("class", `bar-${i}`)
            .attr("x", (d, j) => x(data.xAxis.data[j]) + i * barWidth)
            .attr("y", d => y(d))
            .attr("width", barWidth)
            .attr("height", d => height - y(d))
            .attr("fill", color(i));
    });

    // 添加图注
    const legend = svg
        .selectAll(".legend")
        .data(data.datasets)
        .enter()
        .append("g")
        .attr("class", "legend")
        .attr("transform", (d, i) => `translate(${width + 20},${i * 20})`); // 将图注放在图表右侧

    legend
        .append("rect")
        .attr("width", 18)
        .attr("height", 18)
        .attr("fill", (d, i) => color(i));

    legend
        .append("text")
        .attr("x", 24)
        .attr("y", 9)
        .attr("dy", ".35em")
        .style("text-anchor", "start")
        .text(d => d.label);
}


// 渲染饼图（pie）
export function renderPieChart(chartRef, data, options) {
    console.log("渲染饼图数据:", data);
}

// 渲染非可视化数据的默认占位图表
export function renderNonVisualChart(chartRef, data, options) {
    if (!chartRef) {
        console.error("图表容器未找到");
        return;
    }

    console.log("渲染非可视化数据图表:", data);

    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const width = 300 - margin.left - margin.right; // 图表宽度
    const height = 200 - margin.top - margin.bottom; // 图表高度

    // 清空容器，确保重新渲染
    d3.select(chartRef).html("");

    // 创建 SVG 容器
    const svg = d3
        .select(chartRef)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // 添加背景矩形
    svg.append("rect")
        .attr("width", width)
        .attr("height", height)
        .attr("fill", "#f8f9fa") // 轻灰色背景
        .attr("rx", 12) // 圆角边框
        .attr("ry", 12)
        .style("stroke", "#ccc") // 边框颜色
        .style("stroke-width", 1);

    // 添加占位文本
    svg.append("text")
        .attr("x", width / 2)
        .attr("y", height / 2 - 10)
        .attr("text-anchor", "middle")
        .attr("font-size", "16px")
        .attr("fill", "#555")
        .style("font-weight", "bold")
        .text("数据不可视化");

    // 添加可选的提示信息
    if (options?.message) {
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2 + 20)
            .attr("text-anchor", "middle")
            .attr("font-size", "14px")
            .attr("fill", "#777")
            .text(options.message);
    }
}

//渲染雷达图
export function renderRadarChart(chartRef, data) {
    // 参数校验
    if (!chartRef) {
        console.error("图表容器未找到");
        return;
    }

    if (!data || typeof data !== "object") {
        console.error("无效的图表数据格式", data);
        return;
    }

    // 数据格式校验
    const requiredFields = ["metrics", "datasets"];
    if (requiredFields.some(field => !data[field])) {
        console.error("缺失必要字段，需要包含 metrics 和 datasets", data);
        return;
    }

    if (!Array.isArray(data.metrics) || data.metrics.length === 0) {
        console.error("metrics 必须是非空数组", data.metrics);
        return;
    }

    if (!Array.isArray(data.datasets) || data.datasets.length === 0) {
        console.error("datasets 必须是非空数组", data.datasets);
        return;
    }

    console.log("渲染radar_chart数据:", data);

    // 配置参数
    const margin = { top: 60, right: 160, bottom: 60, left: 60 };
    const width = 600 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;
    const radius = Math.min(width, height) / 2;

    // 清空之前的图表
    d3.select(chartRef).html("");

    // 创建 SVG 容器
    const svg = d3
        .select(chartRef)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left + width / 2},${margin.top + height / 2})`);

    // 颜色生成器
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // 计算角度切片
    const angleSlice = (Math.PI * 2) / data.metrics.length;

    // 计算数据范围
    const maxValue = d3.max(data.datasets, d => d3.max(d.data));
    const minValue = d3.min(data.datasets, d => d3.min(d.data));

    // 半径比例尺
    const rScale = d3.scaleLinear()
        .domain([minValue * 0.9, maxValue * 1.1]) // 留出10%的边距
        .range([0, radius]);

    // 绘制辅助网格线
    const gridValues = Array.from({ length: 5 }, (_, i) => minValue + (maxValue - minValue) * i / 4);
    gridValues.forEach(value => {
        svg.append("circle")
            .attr("r", rScale(value))
            .style("stroke", "#eee")
            .style("fill", "none")
            .style("stroke-dasharray", "2,2");
    });

    // 绘制轴线
    const axes = svg.selectAll(".axis")
        .data(data.metrics)
        .enter()
        .append("g")
        .attr("class", "axis");

    axes.append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", (d, i) => radius * Math.cos(angleSlice * i - Math.PI / 2))
        .attr("y2", (d, i) => radius * Math.sin(angleSlice * i - Math.PI / 2))
        .style("stroke", "#999")
        .style("stroke-width", 1);

    // 添加轴标签
    axes.append("text")
        .attr("class", "axis-text")
        .style("font-size", "12px")
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .attr("x", (d, i) => (radius + 15) * Math.cos(angleSlice * i - Math.PI / 2))
        .attr("y", (d, i) => (radius + 15) * Math.sin(angleSlice * i - Math.PI / 2))
        .text(d => d);

    // 创建雷达图绘制器
    const radarLine = d3.lineRadial()
        .curve(d3.curveLinearClosed)
        .radius(d => rScale(d))
        .angle((d, i) => i * angleSlice);

    // 绘制数据路径
    data.datasets.forEach((dataset, i) => {
        svg.append("path")
            .datum(dataset.data)
            .attr("class", `radar-area-${i}`)
            .attr("d", radarLine)
            .style("fill", color(i))
            .style("fill-opacity", 0.3)
            .style("stroke", color(i))
            .style("stroke-width", 2);
    });

    // 添加独立图注
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${radius + 50},${-height / 2 + 30})`);

    legend.selectAll(".legend-item")
        .data(data.datasets)
        .enter()
        .append("g")
        .attr("class", "legend-item")
        .attr("transform", (d, i) => `translate(0,${i * 25})`);

    legend.selectAll(".legend-item")
        .append("rect")
        .attr("width", 16)
        .attr("height", 16)
        .attr("fill", (d, i) => color(i));

    legend.selectAll(".legend-item")
        .append("text")
        .attr("x", 24)
        .attr("y", 8)
        .attr("dy", "0.35em")
        .style("font-size", "12px")
        .text(d => d.label);
}

//渲染堆叠图
export function renderStackedBarChart(chartRef, chartData) {
    if (!chartRef) {
        console.error("图表容器未找到");
        return;
    }

    const { labels, values } = chartData.data;
    const { colors } = chartData.options;

    // 图表边距和尺寸
    const margin = { top: 20, right: 120, bottom: 50, left: 60 };
    const width = 600 - margin.left - margin.right;
    const height = 350 - margin.top - margin.bottom;

    // 清空之前的图表
    d3.select(chartRef).html("");

    // 创建 SVG 画布
    const svg = d3
        .select(chartRef)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // 数据转换：从对象形式转换为按统计项分类的数组
    const categories = Object.keys(values[0]); // 获取所有的类别：GP, GS, MPG, ...
    const stack = d3
        .stack()
        .keys(categories)
        .order(d3.stackOrderNone)
        .offset(d3.stackOffsetNone);

    const stackedData = stack(values);

    // X 轴比例尺
    const x = d3.scaleBand().domain(labels).range([0, width]).padding(0.2);

    // Y 轴比例尺
    const y = d3
        .scaleLinear()
        .domain([0, d3.max(stackedData[stackedData.length - 1], d => d[1])])
        .nice()
        .range([height, 0]);

    // 添加 X 轴
    svg
        .append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "rotate(-30)")
        .style("text-anchor", "end");

    // 添加 Y 轴
    svg.append("g").call(d3.axisLeft(y));

    // 绘制堆叠柱状图
    svg
        .selectAll(".serie")
        .data(stackedData)
        .enter()
        .append("g")
        .attr("class", "serie")
        .selectAll(".bar")
        .data(d => d)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", d => x(labels[d.index]))
        .attr("y", d => y(d[1]))
        .attr("width", x.bandwidth())
        .attr("height", d => y(d[0]) - y(d[1]))
        .attr("fill", (d, i) => colors[i]);

    // **添加图例**
    const legend = svg
        .append("g")
        .attr("transform", `translate(${width + 20}, 20)`); // 右侧放置

    categories.forEach((category, i) => {
        const legendItem = legend
            .append("g")
            .attr("transform", `translate(0, ${i * 20})`);

        legendItem
            .append("rect")
            .attr("width", 15)
            .attr("height", 15)
            .attr("fill", colors[i]);

        legendItem
            .append("text")
            .attr("x", 20)
            .attr("y", 12)
            .text(category)
            .style("font-size", "14px")
            .attr("fill", "#333");
    });

    // X 轴标题
    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", height + margin.bottom - 10)
        .style("text-anchor", "middle")
        .text("Year");

    // Y 轴标题
    svg
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", -margin.left + 20)
        .style("text-anchor", "middle")
        .text("Statistics");
}

//渲染散点图
export function renderScatterChart(chartRef, data) {
    // 参数校验
    if (!chartRef) {
        console.error("图表容器未找到");
        return;
    }

    if (!data || typeof data !== "object") {
        console.error("无效的图表数据格式", data);
        return;
    }

    // 检查必要字段
    const requiredFields = ["xAxis", "yAxis", "datasets"];
    if (requiredFields.some(field => !data[field])) {
        console.error("缺失必要字段，需要包含 xAxis、yAxis 和 datasets", data);
        return;
    }

    console.log("渲染scatter_chart数据:", data);

    // 配置参数
    const margin = { top: 50, right: 100, bottom: 50, left: 50 };
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // 清空之前的图表
    d3.select(chartRef).html("");

    // 创建 SVG 容器
    const svg = d3
        .select(chartRef)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // X轴比例尺
    const x = d3.scaleLinear()
        .domain([d3.min(data.xAxis.data), d3.max(data.xAxis.data)]) // 根据 xAxis.data 定义范围
        .range([0, width]);

    // Y轴比例尺
    const y = d3.scaleLinear()
        .domain([d3.min(data.yAxis.data), d3.max(data.yAxis.data)]) // 根据 yAxis.data 定义范围
        .range([height, 0]);

    // 颜色生成器
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // 添加 X 轴
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(x));

    // 添加 Y 轴
    svg.append("g")
        .call(d3.axisLeft(y));

    // 添加 X 轴标注
    svg.append("text")
        .attr("class", "axis-label")
        .attr("x", width / 2)
        .attr("y", height + margin.bottom - 10)
        .style("text-anchor", "middle")
        .text(data.xAxis.label);

    // 添加 Y 轴标注
    svg.append("text")
        .attr("class", "axis-label")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", -margin.left + 20)
        .style("text-anchor", "middle")
        .text(data.yAxis.label);

    // 绘制散点
    data.datasets.forEach((dataset, i) => {
        svg.selectAll(`.dot-${i}`)
            .data(dataset.data)
            .enter()
            .append("circle")
            .attr("class", `dot-${i}`)
            .attr("cx", d => x(d.x))
            .attr("cy", d => y(d.y))
            .attr("r", 5) // 点的大小
            .attr("fill", color(i))
            .attr("opacity", 0.8);
    });

    // 添加图注
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width + 20},${20})`);

    data.datasets.forEach((dataset, i) => {
        legend.append("rect")
            .attr("x", 0)
            .attr("y", i * 20)
            .attr("width", 16)
            .attr("height", 16)
            .attr("fill", color(i));

        legend.append("text")
            .attr("x", 24)
            .attr("y", i * 20 + 8)
            .attr("dy", "0.35em")
            .style("font-size", "12px")
            .text(dataset.label);
    });
}