# chart_formats.py

def get_bar_chart_format():
    return [{
				"chartType": "bar",
				"title": "AAAA",
				"xAxis": { "label": "Year", "data": ["2021", "2023", "2024"] },
				"yAxis": { "label": "Value" },
				"datasets": [
					{ "label": "PPG", "data": [22.0, 30.0, 23.0] },
					{ "label": "RPG", "data": [11.0, 10.0, 9.0] }
				]
			}]

def get_pie_chart_format():
    return [{
        "type": "pie",
        "data": {
            "labels": ["类别1", "类别2", "类别3", "类别4"],  # 类别
            "datasets": [{
                "data": [12, 19, 3, 5],  # 每个类别的数值
                "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"],  # 每个扇区的颜色
                "hoverBackgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {
                    "position": "top"
                },
                "tooltip": {
                    "enabled": True
                }
            }
        }
    }]

def get_line_chart_format():
    return [{
        "type": "line",
        "data": {
            "labels": ["Jan", "Feb", "Mar", "Apr"],  # 时间或其他类型的连续数据
            "datasets": [{
                "label": "数据集1",
                "data": [65, 59, 80, 81],  # 每个数据点的数值
                "borderColor": "#FF6384",  # 线条颜色
                "fill": False  # 是否填充面积
            }]
        },
        "options": {
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": "月份"
                    }
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": "值"
                    },
                    "beginAtZero": True
                }
            }
        }
    }]

def get_horizontal_bar_chart_format():
    return [{
        "type": "bar",
        "data": {
            "labels": ["类别1", "类别2", "类别3", "类别4"],
            "datasets": [{
                "label": "数据集1",
                "data": [12, 19, 3, 5],
                "backgroundColor": "#FF6384",
                "borderColor": "#FF6384",
                "borderWidth": 1
            }]
        },
        "options": {
            "indexAxis": "y",  # 横向条形图
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": "值"
                    }
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": "类别"
                    }
                }
            }
        }
    }]

def get_histogram_format():
    return [{
        "type": "bar",
        "data": {
            "labels": ["0-10", "10-20", "20-30", "30-40"],  # 数据分组（区间）
            "datasets": [{
                "label": "数据集1",
                "data": [12, 19, 3, 5],
                "backgroundColor": "#FF6384",
                "borderColor": "#FF6384",
                "borderWidth": 1
            }]
        },
        "options": {
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": "数据范围"
                    }
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": "频率"
                    },
                    "beginAtZero": True
                }
            }
        }
    }]

def get_stacked_bar_chart_format():
    return [{
    "type": "stackedBar",
    "data": {
        "labels": ["Label1", "Label2", "Label3"],
        "values": [
            { "key1": 10, "key2": 15 },
            { "key1": 20, "key2": 25 },
            { "key1": 30, "key2": 35 }
        ]
    },
    "options": {
        "colors": ["#ff5733", "#33ff57"]
    }
}]

def get_scatter_plot_format():
    return [{
    "xAxis": {
        "label": "X轴标签",
        "data": [1, 2, 3, 4, 5] 
    },
    "yAxis": {
        "label": "Y轴标签",
        "data": [10, 20, 30, 40, 50] 
    },
    "datasets": [
        {
            "label": "数据集1",
            "data": [
                { "x": 1, "y": 10 },
                { "x": 2, "y": 20 },
                { "x": 3, "y": 30 },
                { "x": 4, "y": 40 },
                { "x": 5, "y": 50 }
            ]
        },
        {
            "label": "数据集2",
            "data": [
                { "x": 1, "y": 15 },
                { "x": 2, "y": 25 },
                { "x": 3, "y": 35 },
                { "x": 4, "y": 45 },
                { "x": 5, "y": 55 }
            ]
        }
    ]
}]

def get_radar_chart_format():
    return [{
				"metrics": [
					"GP",
					"GS",
					"MPG",
					"FG%",
					"3P%",
					"FT%",
					"RPG",
					"APG",
					"SPG",
					"BPG"
				],
				"datasets": [
					{
						"label": "2021",
						"data": [1, 1, 34.9, 0.412, 0.5, 0.667, 11, 10, 2, 1]
					},
					{ "label": "2023", "data": [1, 1, 45.3, 0.571, 0.5, 1.0, 10, 6, 1, 2] },
					{ "label": "2024", "data": [1, 1, 40.9, 0.3, 0.2, 1.0, 9, 9, 3, 2] },
					{
						"label": "Career",
						"data": [3, 3, 40.4, 0.431, 0.4, 0.864, 10, 8.3, 2, 1.7]
					}
				]
			}]



def get_table_format():
    return[{
  "title": "表格标题",
  "rows": ["属性1", "属性2"], 
  "columns": [
    { "name": "记录1", "data": {"属性1": "值1", "属性2": "值1"} },
    { "name": "记录2", "data": {"属性1": "值2", "属性2": "值2"} },
  ]
}]