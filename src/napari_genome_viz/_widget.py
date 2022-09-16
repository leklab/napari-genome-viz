import matplotlib.pyplot as plt
import napari
import numpy as np
from magicgui import magic_factory
from napari.utils import progress
from scipy.interpolate import interp1d
from scipy.spatial import distance_matrix


@magic_factory(call_button="Draw Interpolated Lines")
def plot_interp_lines(
    select: "napari.layers.Points",
) -> "napari.types.LayerDataTuple":
    """Returns interpolated lines layer given a points layer

    Returns
    -------
    napari.types.LayerDataTuple
        tuple of (data, meta, 'labels') for consumption by napari
    """
    with progress(total=0):
        trace_coords = select.data
        # Linear length along the line:
        distance = np.cumsum(
            np.sqrt(np.sum(np.diff(trace_coords, axis=0) ** 2, axis=1))
        )
        distance = np.insert(distance, 0, 0) / distance[-1]

        # Interpolation
        line_division = 7
        alpha = np.linspace(0, 1, line_division * len(trace_coords))

        interpolator = interp1d(distance, trace_coords, kind="cubic", axis=0)
        interpolated_points = interpolator(alpha)
        line_coords = [
            interpolated_points[i : i + 2]
            for i in range(0, len(interpolated_points), 1)
        ][:-1]

        # set region numbers which will map to colour spectrum
        colormap_values_lines = np.arange(1, len(line_coords) + 1) / (
            len(line_coords) + 1
        )

        line_properties = {"region_number": colormap_values_lines}
        line_kwargs = dict(
            shape_type="line",
            edge_width=0.02,
            properties=line_properties,
            edge_color="region_number",
            face_colormap="viridis",
            name=select.name + " interpolated lines",
        )

    line_layer = (line_coords, line_kwargs, "shapes")
    # link_layers(select, line_layer)
    return line_layer


@magic_factory(call_button="Draw Straight Lines")
def plot_straight_lines(
    select: "napari.layers.Points",
) -> "napari.types.LayerDataTuple":
    """Returns straight lines layer given a points layer

    Returns
    -------
    napari.types.LayerDataTuple
        tuple of (data, meta, 'labels') for consumption by napari
    """
    with progress(total=0):
        trace_coords = select.data
        # define path coordinates
        line_coords = [
            trace_coords[i : i + 2] for i in range(0, len(trace_coords), 1)
        ][:-1]

        # set region numbers which will map to colour spectrum
        line_properties = {
            "region_number": np.arange(1, len(trace_coords))
            / len(trace_coords)
        }

        line_kwargs = dict(
            shape_type="line",
            edge_width=0.02,
            properties=line_properties,
            edge_color="region_number",
            face_colormap="viridis",
            name=select.name + " straight lines",
        )

    line_layer = (line_coords, line_kwargs, "shapes")

    return line_layer


@magic_factory(call_button="Return Distance Matrix")
def plot_dist_matrix(
    select: "napari.layers.Points",
) -> "napari.types.ImageData":
    """Returns distance matrix given points layer

    Returns
    -------
    napari.types.LayerDataTuple
        tuple of (data, meta, 'labels') for consumption by napari
    """
    with progress(total=0):
        trace_coords = select.data
        # distance between tads:
        distance_mat = distance_matrix(trace_coords, trace_coords)
        import matplotlib.cm as cmap

        plt.imshow(distance_mat, cmap=cmap.hot)
        plt.colorbar()
        plt.title(select.name + " heatmap")
        return plt.show()
