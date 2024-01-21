"""This file contain program for generating buffer polygon for gps track in KML file."""

import os
import re
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import pyclipper
import pyproj
import seaborn as sns

track_file_path = 'kml_rutrail/Voinovo-Zapolicy.kml'
empty_file_path = 'assets/Empty.kml'
buffer = 300


def meters_to_mercator_units(buffer: float, coordinates_latlon: List[Tuple]) -> float:
    """
    Convert distance in meters to Mercator units.

    Args:
    buffer (float): The distance in meters
    coordinates_latlon (List[Tuple[float, float]]): List of lat-lon coordinates

    Returns:
    float: The distance in Mercator units
    """
    middle_coord_index = len(coordinates_latlon) // 2
    lat, lon = coordinates_latlon[middle_coord_index]
    proj = pyproj.Proj(proj='merc', datum='WGS84')
    scale_factor = round(proj.get_factors(lat, lon).meridional_scale, 3)
    distance_mercator_units = buffer * scale_factor
    print(
        f'Scale factor: {scale_factor} defined at lat: {lat}, lon: {lon} \
(by {middle_coord_index}th coordinate)'
    )
    print(
        f'Buffer of {buffer} meters is approximately {distance_mercator_units} units in Mercator'
    )
    print('*' * 10)
    return distance_mercator_units


def read_kml_file(file_path: str) -> List[Tuple]:
    """
    Reads a KML file and extracts coordinate data.

    Args:
    - file_path: str, the path to the KML file.

    Returns:
    - List[Tuple[float, float]]: a list of coordinate pairs.
    """
    with open(file_path, 'r') as file:
        kml_data = file.read()
        coordinates_data = re.search(
            r'<coordinates>(.*?)</coordinates>', kml_data, re.DOTALL
        )
        if coordinates_data:
            coordinates = [
                tuple(map(float, coord.split(',')))
                for coord in coordinates_data.group(1).strip().split('\n')
            ]
            print('*' * 10)
            print('Total coordinate pairs:', len(coordinates))
            print('Sample of coordinates:', coordinates[:1])
            print('*' * 10)
            return coordinates
    return []


def create_buffer_track(coordinates: List[Tuple], buffer: float) -> List[Tuple]:
    """
    Create a buffer track based on the given coordinates and buffer size.

    Args:
    - coordinates: List of tuples representing (x, y) coordinates.
    - buffer: Size of the buffer.

    Returns:
    - List of tuples representing the buffered track coordinates.
    """
    coordinates = [(coord[0], coord[1]) for coord in coordinates]
    coordinates_scaled = pyclipper.scale_to_clipper(coordinates)  # type: ignore
    pco = pyclipper.PyclipperOffset()  # type: ignore
    pco.AddPath(
        path=coordinates_scaled,
        join_type=pyclipper.JT_MITER,  # type: ignore
        end_type=pyclipper.ET_OPENSQUARE,  # type: ignore
    )
    solution = pco.Execute(pyclipper.scale_to_clipper(buffer))  # type: ignore
    assert len(solution) == 1, 'WARNING: more than one solution found'
    solution = solution[0]
    print('Total solution pairs:', len(solution))
    print('Sample of solution:', solution[:1])
    print('*' * 10)
    return solution


def plot_track(
    solution: List[Tuple],
    coordinates: List[Tuple],
    track_file_path: str,
) -> None:
    """
    Plot the track by overlaying the original coordinates and the solution coordinates.

    Args:
    - solution: List of tuples representing the solution coordinates in (latitude,
    longitude) format.
    - coordinates: List of tuples representing the original coordinates in (latitude,
    longitude) format.
    - track_file_path: File path to save the plot.
    """
    lat_orig, lon_orig = zip(*coordinates)
    lat_sol, lon_sol = zip(*solution)
    set_orig = pd.DataFrame(
        {'lat': lat_orig, 'lon': lon_orig, 'data_class': 'Original'}
    )
    set_sol = pd.DataFrame({'lat': lat_sol, 'lon': lon_sol, 'data_class': 'Solution'})
    data = pd.concat([set_orig, set_sol])
    sns.set(rc={'figure.figsize': (50, 50)})
    sns.scatterplot(x='lat', y='lon', data=data, hue='data_class', style='data_class')
    plot_name = os.path.basename(track_file_path)[:-4] + '_buffered.pdf'
    print('Saving plot to:', plot_name)
    plt.savefig(plot_name, dpi=300)
    print('Plot saved to:', plot_name)
    print('*' * 10)


def track_to_string(track: List[Tuple]) -> str:
    """
    Convert a list of (x, y) points to a string representation.
    Args:
    - track: List of tuples representing (x, y) points
    Returns:
    - String representation of the track
    """
    return '\n'.join([f'{point[0]},{point[1]},0' for point in track])


def insert_string_after_coordinates(empty_file_path, insert_string, track_file_path):
    with open(empty_file_path, 'r') as file:
        kml_data = file.read()
        name_tag = '</name>'
        name_index = kml_data.find(name_tag)
        start_tag = '<coordinates>'
        coord_index = kml_data.find(start_tag) + len(start_tag)
        new_file_path = os.path.basename(track_file_path)[:-4] + '_buffered.kml'
        if coord_index != -1 and name_index != -1:
            new_kml_data = (
                kml_data[:name_index]
                + track_file_path
                + kml_data[name_index:coord_index]
                + '\n'
                + insert_string
                + kml_data[coord_index:]
            )
            with open(new_file_path, 'w') as new_file:
                new_file.write(new_kml_data)


def latlon_to(coordinates: List[Tuple], inverse: bool = False) -> List[Tuple]:
    """
    Convert latitude and longitude coordinates to mercator projection and back.

    Args:
    - coordinates: List of tuples containing latitude and longitude coordinates.
    - inverse: Whether to perform inverse projection.

    Returns:
    - List of tuples containing converted x and y coordinates in mercator projection.
    """
    coord_converted: List[Tuple[float, float]] = []
    proj = pyproj.Proj(proj='merc', datum='WGS84')

    for pair in coordinates:
        x, y = proj(pair[0], pair[1], inverse=inverse)
        coord_converted.append((round(x, 6), round(y, 6)))

    print(
        'Convert coordinates, inverse:',
        inverse,
        'Total converted coordinates:',
        len(coord_converted),
    )
    print('Sample of converted coordinates:', coord_converted[:1])
    print('*' * 10)
    return coord_converted


def main(track_file_path: str, buffer: float, empty_file_path: str) -> None:
    """
    Main function to process track file, create buffer, plot track, and insert solution into KML file.

    Args:
        track_file_path (str): The file path of the track to be processed.
        buffer (float): The buffer distance in meters.
        empty_file_path (str): The file path for the empty file to insert the solution.
    """

    # Read the KML file to get the coordinates in latitude and longitude
    coordinates_latlon = read_kml_file(track_file_path)

    # Convert the buffer from meters to Mercator units
    buffer_merc = meters_to_mercator_units(buffer, coordinates_latlon)

    # Convert the coordinates from latitude and longitude to Mercator coordinates
    coordinates_merc = latlon_to(coordinates_latlon)

    # Create a buffer track using the Mercator coordinates and buffer in Mercator units
    solution_merc_ints = create_buffer_track(coordinates_merc, buffer_merc)

    # Rescale the integer Mercator solution into floating-point Mercator coordinates
    solution_merc = pyclipper.scale_from_clipper(solution_merc_ints)  # type: ignore

    # Convert the solution from Mercator coordinates back to latitude and longitude
    solution_latlon = latlon_to(solution_merc, inverse=True)

    # Plot the track
    plot_track(solution_latlon, coordinates_latlon, track_file_path)

    # Convert the solution in latitude and longitude to a string for insert in KML file
    solution_latlon_string = track_to_string(solution_latlon)

    # Insert the solution string after the coordinates in the track file and save it
    insert_string_after_coordinates(
        empty_file_path=empty_file_path,
        insert_string=solution_latlon_string,
        track_file_path=track_file_path,
    )


if __name__ == '__main__':
    main(track_file_path, buffer, empty_file_path)
