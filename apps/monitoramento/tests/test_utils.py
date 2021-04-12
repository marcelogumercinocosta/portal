import pytest
from apps.monitoramento.utils.echarts import  AxisData, AxisBase, Legend, Tooltip, Toolbox, Grid, Echarts, LineArea, Line


def test_echarts_line_area() -> None:
    time = ['15:00','15:05','15:10','15:15','15:20']
    service = [39, 39, 39, 39, 39]
    down = [23, 23, 23, 23, 23]
    free = [575, 552, 549, 550, 580]
    running = [131, 154, 157, 156, 126]
    jobs = [23, 23, 23, 23, 23]

    grafico = Echarts()
    grafico.set_color(["red", "#ffa726", "green", "#0277bd"])
    x_axis = AxisData("category", "bottom", time)
    x_axis.set_axis_label({"rotate": 45, "textStyle": {"fontSize": 8}})
    grafico.add_x_axis(x_axis)
    y_axis = AxisBase("value")
    y_axis.set_max(768)
    y_axis.set_min(10)
    grafico.add_y_axis(y_axis)
    grafico.add_series(LineArea("down", down))
    grafico.add_series(LineArea("service", service))
    grafico.add_series(LineArea("running", running))
    grafico.add_series(LineArea("free", free))
    grafico.set_tooltip(Tooltip())
    grafico.set_legend(Legend())
    grafico.set_grid(Grid())
    grafico.set_toolbox(Toolbox())
    assert grafico.export()['grid'] == {'bottom': '2%', 'containLabel': 'true', 'left': '1%', 'right': '1%', 'top': '3%'}


def test_echarts_line() -> None:
    time = ['15:00','15:05','15:10','15:15','15:20']
    service = [39, 39, 39, 39, 39]
    down = [23, 23, 23, 23, 23]
    free = [575, 552, 549, 550, 580]
    running = [131, 154, 157, 156, 126]
    jobs = [23, 23, 23, 23, 23]

    grafico = Echarts()
    grafico.set_color(["red", "#ffa726", "green", "#0277bd"])
    x_axis = AxisData("category", "bottom", time)
    x_axis.set_axis_label({"rotate": 45, "textStyle": {"fontSize": 8}})
    grafico.add_x_axis(x_axis)
    y_axis = AxisBase("value")
    y_axis.set_max(768)
    y_axis.set_min(10)
    grafico.add_y_axis(y_axis)
    grafico.add_series(Line("down", down))
    grafico.add_series(Line("service", service))
    grafico.add_series(Line("running", running))
    grafico.add_series(Line("free", free))
    grafico.set_tooltip(Tooltip())
    grafico.set_legend(Legend())
    grafico.set_grid(Grid())
    grafico.set_toolbox(Toolbox())
    assert grafico.export()['grid'] == {'bottom': '2%', 'containLabel': 'true', 'left': '1%', 'right': '1%', 'top': '3%'}