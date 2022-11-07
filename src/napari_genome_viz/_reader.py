import os
import re
import urllib.request
import ssl

import numpy as np
import pandas as pd


def napari_get_reader(path):
    """Returns reader if path contains data in
    4DN standard FISH-Omics Format - Chromatin Tracing (FOF-CT)
    Specifically DNA-Spot/Trace Data core table (info on format
    https://fish-omics-format.readthedocs.io/en/latest/core.html#core)
    otherwise None.

    :param path: path to be opened by reader
    :type path: str
    :return: reader function or None
    """

    if path.startswith('http'):
        f = urllib.request.urlopen(path)
    else:
        file = os.path.abspath(path)
        f = open(file, "rb")

    # if header does not indicate FOF-CT data format, return None
    #with open(file, "rb") as f:
    firstline = f.readline().rstrip().decode("utf-8")

    if firstline.find("FOF-CT") == -1:
        return None

    # if header does not indicate file contains correct columns, return None
    #with open(file, encoding="ISO-8859-1") as f:
    header = ""
    for line in f:
        line = line.decode("ISO-8859-1")
        if line.startswith("#"):
            header += line
        else:
            break  # stop when there are no more #

    if header.find("Trace_ID, X, Y, Z") == -1:
        return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def reader_function(path):
    """Take a path and return a list of LayerData tuples.

    Parameters
    ----------
    path : str or list of str
        Path to file.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array,
        metadata is a dict of keyword arguments for the corresponding
        viewer.add_* method in napari, and layer_type is a
        lower-case string naming the type of layer.

        Reader takes DNA-Spot/Trace Data core table, splits it into
        Traces and plots them with a mapped colour spectrum corresponding
        to the point's position along the trace.
    """

    if path.startswith('http'):
        f = urllib.request.urlopen(path)
    else:
        path = os.path.abspath(path)
        f = open(path, "rb")

    # read in file
    df = pd.read_csv(path, comment="#", header=None, encoding="ISO-8859-1")

    # get column names
    # if header does not indicate file contains correct columns, return None
    #with open(path, encoding="ISO-8859-1") as f:
    header = ""
    for line in f:
        line = line.decode("ISO-8859-1")
        if line.startswith("#"):
            header += line
        else:
            break  # stop when there are no more #

    column_names = re.findall(r"(?<=columns=\()(.*)(?=\))", header)
    df.columns = column_names[0].split(", ")

    # get trace coords and ids
    trace_coords = df[["X", "Y", "Z"]].values
    trace_ids = df[["Trace_ID"]]

    # number of traces in data
    trace_counts = trace_ids.value_counts()[
        trace_ids["Trace_ID"].unique()
    ].tolist()

    # split point coordinates into arrays by trace lengths
    trace_coords_split = [
        x
        for x in np.split(trace_coords, np.cumsum(trace_counts)[:-1], axis=0)
        if x.size > 0
    ]

    layers = []

    traces = list(range(0, len(trace_ids["Trace_ID"].unique())))

    for trace in traces:
        trace_coords_trace = trace_coords_split[trace]
        # get colormap coordinates for each trace
        x = trace_counts[trace]
        colormap_values = np.arange(1, x + 1) / x
        # colormap_values = [i for i in chain.from_iterable(colormap_values)]
        # set region numbers which will map to colour spectrum
        point_properties = {"region_number": colormap_values}
        probe_kwargs = dict(
            properties=point_properties,
            face_color="region_number",
            size=0.3,
            edge_width=0,
            shading="spherical",
            name="trace " + str(trace_ids["Trace_ID"].unique()[trace]),
        )
        layers.extend([(trace_coords_trace, probe_kwargs, "points")])
    return layers
