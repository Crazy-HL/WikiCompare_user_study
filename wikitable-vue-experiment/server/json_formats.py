# chart_formats.py

def get_bar_chart_format():
    return [{
        "type": "bar",
        "data": {
            "labels": ["类别1", "类别2", "类别3", "类别4"],  # 类别或分组
            "datasets": [{
                "label": "数据集1",
                "data": [12, 19, 3, 5],  # 每个类别的数值
                "backgroundColor": "#FF6384",  # 柱形的背景颜色
                "borderColor": "#FF6384",  # 边框颜色
                "borderWidth": 1  # 边框宽度
            }]
        },
        "options": {
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": "类别"
                    }
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": "值"
                    },
                    "beginAtZero": True  # Y 轴从0开始
                }
            }
        }
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
        "type": "bar",
        "data": {
            "labels": ["类别1", "类别2", "类别3", "类别4"],
            "datasets": [{
                "label": "数据集1",
                "data": [12, 19, 3, 5],
                "backgroundColor": "#FF6384"
            }, {
                "label": "数据集2",
                "data": [7, 11, 5, 8],
                "backgroundColor": "#36A2EB"
            }]
        },
        "options": {
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": "类别"
                    }
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": "值"
                    },
                    "beginAtZero": True
                }
            },
            "plugins": {
                "legend": {
                    "position": "top"
                }
            }
        }
    }]

def get_scatter_plot_format():
    return [{
        "type": "scatter",
        "data": {
            "datasets": [{
                "label": "数据集1",
                "data": [{"x": 10, "y": 20}, {"x": 15, "y": 25}, {"x": 20, "y": 30}],
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
                        "text": "X轴"
                    }
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": "Y轴"
                    }
                }
            }
        }
    }]


