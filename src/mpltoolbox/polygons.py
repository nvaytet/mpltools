# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Mpltoolbox contributors (https://github.com/mpltoolbox)

from .lines import Lines
from .utils import make_color
import numpy as np
from functools import partial
from matplotlib.pyplot import Artist, Axes
from matplotlib.backend_bases import Event


class Polygons(Lines):

    def __init__(self, ax: Axes, alpha=0.05, **kwargs):
        super().__init__(ax, n=0, **kwargs)
        self._distance_from_first_point = 0.05
        self._first_point_position = None
        self._finalize_polygon = False
        self._alpha = alpha
        # self._fills = []

    def _make_new_line(self, x: float, y: float):
        super()._make_new_line(x=x, y=y)
        self._first_point_position_data = (x, y)
        self._first_point_position_axes = self._data_to_axes_transform(x, y)
        line = self.lines[-1]
        fill, = self._ax.fill(line.get_xdata(),
                              line.get_ydata(),
                              color=line.get_color(),
                              alpha=self._alpha)
        line._fill = fill

    def _data_to_axes_transform(self, x, y):
        trans = self._ax.transData.transform((x, y))
        return self._ax.transAxes.inverted().transform(trans)

    def _compute_distance_from_first_point(self, event):
        xdisplay, ydisplay = self._data_to_axes_transform(event.xdata, event.ydata)
        dist = np.sqrt((xdisplay - self._first_point_position_axes[0])**2 +
                       (ydisplay - self._first_point_position_axes[1])**2)
        return dist

    def _on_motion_notify(self, event: Event):
        if self._compute_distance_from_first_point(
                event) < self._distance_from_first_point:
            event.xdata = self._first_point_position_data[0]
            event.ydata = self._first_point_position_data[1]
            self._finalize_polygon = True
        else:
            self._finalize_polygon = False
        self._move_vertex(event=event, ind=-1, line=self.lines[-1])

    def _persist_dot(self, event: Event):
        if self._finalize_polygon:
            self._fig.canvas.mpl_disconnect(self._connections['motion_notify_event'])
            del self._connections['motion_notify_event']
            self._finalize_line(event)
            self._finalize_polygon = False
        else:
            new_data = self.lines[-1].get_data()
            self.lines[-1].set_data(
                (np.append(new_data[0],
                           new_data[0][-1]), np.append(new_data[1], new_data[1][-1])))
            self._draw()

    def _move_vertex(self, event: Event, ind: int, line: Artist):
        if event.inaxes != self._ax:
            return
        new_data = line.get_data()
        if ind in (0, len(new_data[0])):
            ind = [0, -1]
        new_data[0][ind] = event.xdata
        new_data[1][ind] = event.ydata
        line.set_data(new_data)
        line._fill.set_xy(np.array(new_data).T)
        self._draw()

    def _move_line(self, event: Event):
        if event.inaxes != self._ax:
            return
        dx = event.xdata - self._grab_mouse_origin[0]
        dy = event.ydata - self._grab_mouse_origin[1]
        new_data = (self._grab_artist_origin[0] + dx, self._grab_artist_origin[1] + dy)
        self._grab_artist.set_data(new_data)
        self._grab_artist._fill.set_xy(np.array(new_data).T)
        self._draw()
