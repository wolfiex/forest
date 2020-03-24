import re
import os
import glob
import datetime as dt
import bokeh.models
import netCDF4
import numpy as np
from functools import lru_cache
from forest.exceptions import FileNotFound, IndexNotFound
from forest.old_state import old_state, unique
from forest.util import coarsify
from forest.util import to_datetime as _to_datetime
from forest import (
        geo,
        locate,
        view)


MIN_DATETIME64 = np.datetime64('0001-01-01T00:00:00.000000')


def _natargmax(arr):
    """ Find the arg max when an array contains NaT's"""
    no_nats = np.where(np.isnat(arr), MIN_DATETIME64, arr)
    return np.argmax(no_nats)


def infinite_cache(f):
    """Unbounded cache to reduce navigation I/O

    .. note:: This information would be better saved in a database
              or file to reduce round-trips to disk
    """
    cache = {}
    def wrapped(self, path, variable):
        if path not in cache:
            cache[path] = f(self, path, variable)
        return cache[path]
    return wrapped


class Dataset:
    def __init__(self, pattern=None, color_mapper=None, **kwargs):
        self.pattern = pattern
        self.color_mapper = color_mapper
        self.locator = Locator(self.pattern)

    def navigator(self):
        return Navigator(self.pattern)

    def map_view(self):
        loader = Loader(self.locator)
        return view.UMView(loader, self.color_mapper, use_hover_tool=False)


class Locator:
    """Locate EIDA50 satellite images"""
    def __init__(self, pattern):
        self.pattern = pattern

    def find(self, date):
        if isinstance(date, (dt.datetime, str)):
            date = np.datetime64(date, 's')
        paths = self.paths()
        ipath = self.find_file_index(paths, date)
        path = paths[ipath]
        time_axis = self.load_time_axis(path)
        index = self.find_index(
                time_axis,
                date,
                dt.timedelta(minutes=15))
        return path, index

    def paths(self):
        return sorted(glob.glob(os.path.expanduser(self.pattern)))

    @staticmethod
    @lru_cache()
    def load_time_axis(path):
        with netCDF4.Dataset(path) as dataset:
            var = dataset.variables["time"]
            values = netCDF4.num2date(
                    var[:], units=var.units)
        return np.array(values, dtype='datetime64[s]')

    def find_file_index(self, paths, user_date):
        dates = np.array([
            self.parse_date(path) for path in paths],
            dtype='datetime64[s]')
        mask = ~(dates <= user_date)
        if mask.all():
            msg = "No file for {}".format(user_date)
            raise FileNotFound(msg)
        before_dates = np.ma.array(
                dates, mask=mask, dtype='datetime64[s]')
        return _natargmax(before_dates.filled())

    @staticmethod
    def find_index(times, time, length):
        dtype = 'datetime64[s]'
        if isinstance(times, list):
            times = np.asarray(times, dtype=dtype)
        bounds = locate.bounds(times, length)
        inside = locate.in_bounds(bounds, time)
        valid_times = np.ma.array(times, mask=~inside)
        if valid_times.mask.all():
            msg = "{}: not found".format(time)
            raise IndexNotFound(msg)
        return _natargmax(valid_times.filled())

    @staticmethod
    def parse_date(path):
        # reg-ex to support file names like *20191211.nc
        groups = re.search(r"([0-9]{8})\.nc", path)
        if groups is None:
            # reg-ex to support file names like *20191211T0000Z.nc
            groups = re.search(r"([0-9]{8}T[0-9]{4}Z)\.nc", path)
            return dt.datetime.strptime(groups[1], "%Y%m%dT%H%MZ")
        else:
            return dt.datetime.strptime(groups[1], "%Y%m%d")


class Loader:
    def __init__(self, locator):
        self.locator = locator
        self.empty_image = {
            "x": [],
            "y": [],
            "dw": [],
            "dh": [],
            "image": []
        }
        self.cache = {}
        paths = self.locator.paths()
        if len(paths) > 0:
            with netCDF4.Dataset(paths[-1]) as dataset:
                self.cache["longitude"] = dataset.variables["longitude"][:]
                self.cache["latitude"] = dataset.variables["latitude"][:]

    @property
    def longitudes(self):
        return self.cache["longitude"]

    @property
    def latitudes(self):
        return self.cache["latitude"]

    def image(self, state):
        if state.valid_time is None:
            data = self.empty_image
        else:
            try:
                data = self._image(_to_datetime(state.valid_time))
            except (FileNotFound, IndexNotFound):
                data = self.empty_image
        return data

    def _image(self, valid_time):
        path, itime = self.locator.find(valid_time)
        return self.load_image(path, itime)

    def load_image(self, path, itime):
        lons = self.longitudes
        lats = self.latitudes
        with netCDF4.Dataset(path) as dataset:
            values = dataset.variables["data"][itime]
        fraction = 0.25
        lons, lats, values = coarsify(
                lons, lats, values, fraction)
        return geo.stretch_image(
                lons, lats, values)


class Navigator:
    def __init__(self, pattern):
        self.pattern = pattern

    def variables(self, pattern):
        return ["EIDA50"]

    def initial_times(self, pattern, variable):
        return [dt.datetime(1970, 1, 1)]

    def valid_times(self, pattern, variable, initial_time):
        arrays = []
        for path in sorted(glob.glob(pattern)):
            arrays.append(self._valid_times(path, variable))
        if len(arrays) == 0:
            return []
        return np.unique(np.concatenate(arrays))

    @infinite_cache
    def _valid_times(self, path, variable):
        with netCDF4.Dataset(path) as dataset:
            var = dataset.variables["time"]
            values = netCDF4.num2date(var[:], units=var.units)
        return np.array(values, dtype='datetime64[s]')

    def pressures(self, pattern, variable, initial_time):
        return []