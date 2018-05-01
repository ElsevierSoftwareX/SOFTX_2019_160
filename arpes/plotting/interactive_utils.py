import warnings

import numpy as np
import xarray as xr
import colorcet as cc
from bokeh import palettes
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.models.widgets.markups import Div
from bokeh.io import show, output_notebook

from abc import ABC, abstractmethod

from arpes.analysis.general import rebin

import arpes.config
from arpes.io import load_dataset
from typing import Union

__all__ = ('BokehInteractiveTool', 'CursorTool',)

class CursorTool(object):
    _cursor = None
    _cursor_info = None
    _horiz_cursor_x = None
    _horiz_cursor_y = None
    _vert_cursor_x = None
    _vert_cursor_y = None
    _cursor_lines = None
    _cursor_dims = None

    @property
    def cursor_dims(self):
        return self._cursor_dims

    @cursor_dims.setter
    def cursor_dims(self, value):
        self._cursor_dims = value

    @property
    def cursor_dict(self):
        if self._cursor_dims is None:
            return None

        return dict(zip(self.cursor_dims, self.cursor))

    @property
    def cursor(self):
        return self._cursor

    def add_cursor_lines(self, figure):
        cursor_lines =  figure.multi_line(xs=[self._horiz_cursor_x, self._vert_cursor_x],
                                          ys=[self._horiz_cursor_y, self._vert_cursor_y],
                                          line_color='white', line_width=2, line_dash='dotted')
        self._cursor_lines = cursor_lines
        return cursor_lines

    @cursor.setter
    def cursor(self, values):
        self._cursor = values
        if self._cursor_info is None:
            self._cursor_info = Div(text='')
            self._horiz_cursor_x = list(self.data_range['x'])
            self._horiz_cursor_y = [0, 0]
            self._vert_cursor_x = [0, 0]
            self._vert_cursor_y = list(self.data_range['y'])
        else:
            self._vert_cursor_x[0] = self._vert_cursor_x[1] = self.cursor[0]
            self._horiz_cursor_y[0] = self._horiz_cursor_y[1] = self.cursor[1]

        self._cursor_info.text = '<h2>Cursor:</h2><span>({})</span>'.format(
            ', '.join("{0:.3f}".format(c) for c in self.cursor))

        if self._cursor_lines is not None:
            self._cursor_lines.data_source.data = {
                'xs': [self._horiz_cursor_x, self._vert_cursor_x],
                'ys': [self._horiz_cursor_y, self._vert_cursor_y],
            }


class BokehInteractiveTool(ABC):
    auto_rebin = True
    auto_zero_nans = True
    rebin_size = 800

    def init_bokeh_server(self):
        if 'bokeh_configured' not in arpes.config.CONFIG:
            arpes.config.CONFIG['bokeh_configured'] = True

            # use a longer load_timeout for heavy tools
            output_notebook(hide_banner=True, load_timeout=10000)

            # Don't need to manually start a server in the manner of
            # https://matthewrocklin.com/blog//work/2017/06/28/simple-bokeh-server
            # according to
            # https://github.com/bokeh/bokeh/blob/0.12.10/examples/howto/server_embed/notebook_embed.ipynb

    def load_settings(self, **kwargs):
        self.settings = arpes.config.SETTINGS.get('interactive', {}).copy()
        for k, v in kwargs.items():
            if k not in self.settings:
                self.settings[k] = v

    @property
    def default_palette(self):
        palette_options = {
            'viridis': palettes.viridis(256),
            'magma': palettes.magma(256),
            'coolwarm': cc.coolwarm,
        }

        return palette_options[self.settings.get('palette', 'viridis')]

    def __init__(self):
        self.settings = None
        self.app_context = {
            'data': None,
            'plots': {},
            'figures': {},
            'color_maps': {},
            'widgets': {},
        }

        self.init_bokeh_server()

    def __getattribute__(self, item):
        """
        Allow more convenient use of attributes from self.app_context. This is a bit strange.
        :param item:
        :return:
        """
        try:
            return super().__getattribute__(item)
        except AttributeError:
            if item in self.app_context:
                return self.app_context[item]

    @abstractmethod
    def tool_handler(self, doc):
        pass

    def make_tool(self, arr: Union[xr.DataArray, str], notebook_url=None,
                  notebook_handle=True, **kwargs):

        def generate_url(port):
            if port is None:
                return 'localhost:8888'

            return 'localhost:{}'.format(port)

        if notebook_url is None:
            if 'PORT' in arpes.config.CONFIG:
                notebook_url = 'localhost:{}'.format(arpes.config.CONFIG['PORT'])
            else:
                notebook_url = 'localhost:8888'

        if isinstance(arr, str):
            arr = load_dataset(arr)
            if 'cycle' in arr.dims and len(arr.dims) > 3:
                warnings.warn('Summing over cycle')
                arr = arr.sum('cycle', keep_attrs=True)

        if self.auto_zero_nans and len({'kx', 'ky', 'kz', 'kp'}.intersection(set(arr.dims))) > 0:
            # We need to copy and make sure to clear any nan values, because bokeh
            # does not send these over the wire for some reason
            arr = arr.copy()
            np.nan_to_num(arr.values, copy=False)

        # rebin any axes that have more than 800 pixels
        if self.auto_rebin and np.any(np.asarray(arr.shape) > self.rebin_size):
            reduction = {d: (s // self.rebin_size) + 1 for d, s in arr.S.dshape.items()}
            warnings.warn('Rebinning with {}'.format(reduction))

            arr = rebin(arr, reduction=reduction)

            # TODO pass in a reference to the original copy of the array and make sure that
            # preparation tasks move over transparently

        self.arr = arr
        handler = FunctionHandler(self.tool_handler)
        app = Application(handler)
        show(app, notebook_url=notebook_url, notebook_handle=notebook_handle)

        return self.app_context