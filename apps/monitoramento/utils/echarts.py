# -*- coding: utf-8 -*-


class Base:
    @property
    def export(self):
        result = {k: self.__getattribute__(k) for k in self.__dict__ if self.__getattribute__(k) is not None}
        return result


class AxisData(Base):
    def __init__(self, type_of, position=None, data=None):
        assert type_of in ("category", "value", "time")
        assert position in ("bottom", "top", "left", "right")
        self.type = type_of
        self.position = position
        self.data = data or []
        self.axisLabel = None

    def set_axis_label(self, value):
        self.axisLabel = value


class AxisBase(Base):
    def __init__(self, type_of):
        assert type_of in ("category", "value", "time")
        self.type = type_of
        self.max = None
        self.min = None

    def set_max(self, value):
        self.max = round(value, 2)

    def set_min(self, value):
        self.min = round(value, 2)


class Legend(Base):
    def __init__(self, orient="horizontal"):
        assert orient in ("horizontal", "vertical")
        self.orient = orient
        self.position = ("center", "bottom")
        self.data = []

    def set_dataseries(self, series):
        for serie in series:
            self.data.append(serie.name)

    @property
    def export(self):
        export = {"data": self.data, "orient": self.orient, "x": self.position[0], "y": self.position[1], "type": "plain"}
        return export


class Tooltip(Base):
    """A tooltip when hovering."""

    def __init__(
        self, trigger="axis",
    ):
        assert trigger in ("axis", "item")
        self.trigger = trigger


class Serie(Base):
    def __init__(self, type_of, name=None, data=None, **kwargs):
        types = (
            "bar",
            "boxplot",
            "candlestick",
            "chord",
            "effectScatter",
            "eventRiver",
            "force",
            "funnel",
            "gauge",
            "graph",
            "heatmap",
            "k",
            "line",
            "lines",
            "map",
            "parallel",
            "pie",
            "radar",
            "sankey",
            "scatter",
            "tree",
            "treemap",
            "venn",
            "wordCloud",
        )
        assert type_of in types
        self.type = type_of
        self.name = name
        self.data = data or []


class Toolbox(Base):
    """ A toolbox for visitor. """

    def __init__(self, orient="horizontal", position=None):
        assert orient in ("horizontal", "vertical")
        self.orient=orient
        self.position = position
        if not position:
            self.position = ("right", "top")

    @property
    def export(self):
        """JSON format data."""
        export = {"orient": self.orient, "x": self.position[0], "y": self.position[1]}
        return export


class Grid(Base):
    def __init__(self, left="1%", right="1%", bottom="2%", top="3%"):
        self.left = left
        self.right = right
        self.bottom = bottom
        self.top = top
        self.containLabel = "true"


class Echarts(Base):
    def __init__(self, title=None, subtext=None, axis=True):
        self.title = {
            "text": title,
            "subtext": subtext,
        }
        self.axis = axis
        if self.axis:
            self.x_axis = []
            self.y_axis = []
        self.series = []
        self.legend = None
        self.tooltip = None
        self.tooltip = None
        self.toolbox = None
        self.color = None
        self.grid = None
        self.series = []

    def set_legend(self, legend):
        self.legend = legend
        self.legend.set_dataseries(self.series)

    def set_tooltip(self, tooltip):
        self.tooltip = tooltip

    def set_grid(self, grid):
        self.grid = grid

    def add_series(self, serie):
        self.series.append(serie)

    def set_color(self, color):
        self.color = color

    def set_toolbox(self, toolbox):
        self.toolbox = toolbox

    def add_x_axis(self, axis):
        self.x_axis.append(axis)

    def add_y_axis(self, axis):
        self.y_axis.append(axis)

    def export(self):
        """JSON format data."""
        # export = {'title': self.title}
        export = {"color": self.color}
        if self.axis:
            export["xAxis"] = [x.export for x in self.x_axis]
            export["yAxis"] = [y.export for y in self.y_axis]
        if self.legend:
            export["legend"] = self.legend.export
        if self.tooltip:
            export["tooltip"] = self.tooltip.export
        if self.toolbox:
            export["toolbox"] = self.toolbox.export
        if self.grid:
            export["grid"] = self.grid.export
        if self.series:
            export["series"] = [s.export for s in self.series]
        return export


class LineArea(Serie):
    def __init__(self, name=None, data=None, **kwargs):
        self.smooth = False
        self.areaStyle = "{normal: {}}"
        self.stack = True
        self.showSymbol = False
        super(LineArea, self).__init__("line", name=name, data=data, **kwargs)


class Line(Serie):
    def __init__(self, name=None, data=None, **kwargs):
        self.smooth = False
        self.showSymbol = False
        super(Line, self).__init__("line", name=name, data=data, **kwargs)
