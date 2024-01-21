"""This file contain program for generating buffer polygon for gps track in KML file."""

import os
import re
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import pyclipper
import pyproj
import seaborn as sns

track_file_paths = [
    # 'kml_rutrail/Voinovo-Zapolicy.kml',
    'kml_rutrail/Voinovo-Zapolicy.gpx',
    'kml_rutrail/Zima.kml',
]
# track_file_paths = ['kml_rutrail/Nerskaya.kml']
empty_file_path = 'assets/Empty.kml'
buffer = 300
buffer_clean = 50


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


def read_kml_file(file_paths: List[str]) -> List[List[Tuple]]:
    """
    Reads a KML file and extracts coordinate data.

    Args:
    - file_paths: list of paths to the KML files.

    Returns:
    - a list of lists with coordinate pairs.
    """
    coord_list = []
    coordinates = []
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            file_data = file.read()

            if file_path[-4:] == '.kml':
                coordinates_data = re.search(
                    r'<coordinates>(.*?)</coordinates>', file_data, re.DOTALL
                )
                if coordinates_data:
                    coordinates = [
                        tuple(map(float, coord.split(',')))
                        for coord in coordinates_data.group(1).strip().split('\n')
                    ]

            elif file_path[-4:] == '.gpx':
                coordinates_data = re.findall(
                    r'<trkpt lat="(.*?)" lon="(.*?)"', file_data
                )
                coordinates = [
                    (float(lat), float(lon)) for lon, lat in coordinates_data
                ]
            if coordinates:
                print('*' * 10)
                print(f'File: {file_path}')
                print(f'Total coordinate pairs: {len(coordinates)}')
                print(f'Sample of coordinates:', coordinates[:1])
                print('*' * 10)
                coord_list += [coordinates]
    return coord_list


def read_gpx_file(file_paths: List[str]) -> List[List[Tuple]]:
    """
    Reads a GPX file and extracts coordinate data.

    Args:
    - file_paths: list of paths to the GPX files.

    Returns:
    - a list of lists with coordinate pairs.
    """
    coord_list = []

    return coord_list


def create_buffer_track(
    coord_list: List[List[Tuple]], buffer: float, buffer_clean: float
) -> List[Tuple]:
    """
    Create a buffer track based on the given coordinates and buffer size.

    Args:
    - coord_list: List of lists of tuples representing (x, y) coordinates.
    - buffer: Size of the buffer.

    Returns:
    - List of tuples representing the buffered track coordinates.

    Raises: AssertionError if there are more than one solution found.
    """
    # coordinates = [
    #     (coord[0], coord[1]) for coord in coordinates for coordinates in coord_list
    # ]
    coord_list_scaled = [pyclipper.scale_to_clipper(coord) for coord in coord_list]  # type: ignore
    pco = pyclipper.PyclipperOffset()  # type: ignore
    pco.AddPaths(
        paths=coord_list_scaled,
        join_type=pyclipper.JT_MITER,  # type: ignore
        end_type=pyclipper.ET_OPENSQUARE,  # type: ignore
    )
    solution = pco.Execute(pyclipper.scale_to_clipper(buffer))  # type: ignore
    assert len(solution) == 1, 'WARNING: more than one solution found'
    solution = solution[0]

    solution_cleaned = pyclipper.CleanPolygon(  # type: ignore
        poly=pyclipper.scale_from_clipper(solution),  # type: ignore
        distance=buffer_clean,
    )

    print('Total solution pairs NOT CLEANED:', len(solution))
    print('Total solution pairs YES CLEANED:', len(solution_cleaned))
    print('Sample of solution:', solution[:1])
    print('*' * 10)
    return solution_cleaned


def plot_track(
    solution: List[Tuple],
    coord_list: List[List[Tuple]],
    track_file_paths: List[str],
) -> None:
    """
    Plot the track by overlaying the original coordinates and the solution coordinates.

    Args:
    - solution: List of tuples representing the solution coordinates in (latitude,
    longitude) format.
    - coord_list: List of lists of tuples representing the original coordinates in (latitude,
    longitude) format.
    - track_file_paths: File paths of the original tracks.
    """
    set_orig = pd.DataFrame()
    for i, coord in enumerate(coord_list):
        lat_orig, lon_orig = zip(*coord)
        set_orig_new = pd.DataFrame(
            {
                'lat': lat_orig,
                'lon': lon_orig,
                'data_class': f'Original: {os.path.basename(track_file_paths[i])}',
            }
        )
        set_orig = pd.concat([set_orig, set_orig_new])

    lat_sol, lon_sol = zip(*solution)
    set_sol = pd.DataFrame({'lat': lat_sol, 'lon': lon_sol, 'data_class': 'Solution'})
    data = pd.concat([set_orig, set_sol])
    sns.set(rc={'figure.figsize': (50, 50)})
    sns.scatterplot(x='lat', y='lon', data=data, hue='data_class', style='data_class')
    file_names = [
        os.path.basename(track_file_path)[:-4] for track_file_path in track_file_paths
    ]
    plot_name = '_'.join(file_names)[:64] + '_buffered.pdf'
    print('Saving plot to:', plot_name)
    plt.savefig(plot_name, dpi=300)
    print('Plot saved to:', plot_name)
    print('*' * 10)


def tracks_to_string(tracks: List[List[Tuple]]) -> str:
    """
    Convert a list of (x, y) points to a string representation.
    Args:
    - tracks: List of lists of tuples representing (x, y) points
    Returns:
    - String representation of the track
    """
    return '\n'.join(
        ['\n'.join([f'{point[0]},{point[1]},0' for point in track]) for track in tracks]
    )


def save_kml(
    empty_file_path: str,
    insert_string: str,
    track_file_paths: List[str],
    buffer: int,
    buffer_clean: int,
) -> None:
    """
    Saves a KML file.

    Args:
    - empty_file_path: str, the path to the empty KML file to be used as a template
    - insert_string: str, the string to be inserted into the KML file
    - track_file_path: str, the path to the track file
    - buffer: int, the buffer distance
    - buffer_clean: int, the buffer clean distance
    """
    file_names = [
        os.path.basename(track_file_path)[:-4] for track_file_path in track_file_paths
    ]
    file_names_full = ", ".join(
        [os.path.basename(track_file_path) for track_file_path in track_file_paths]
    )
    new_file_path = '_'.join(file_names)[:64] + '_buffered.kml'
    placemark_name = f'Autogenerated from file(s) {file_names_full}\n'
    placemark_description = (
        f'Buffer base distance: {buffer}*2={buffer*2} m\n\
Buffer clean distance: {buffer_clean} m\n\
Narrowest possible buffer: {buffer*2}-2*{buffer_clean}={buffer*2-2*buffer_clean} m\n\
Widest possible buffer: {buffer*2}+2*{buffer_clean}={buffer*2+2*buffer_clean} m\n\
Total points: '
        + str(len(insert_string.split("\n")))
        + '\n'
    )
    with open(empty_file_path, 'r') as file:
        kml_data = file.read()

        name_tag = '</name>'
        start_tag = '</coordinates>'
        description_tag = '</description>'

        description_index = kml_data.find(description_tag)
        name_index = kml_data.find(name_tag)
        coord_index = kml_data.find(start_tag)

        new_kml_data = (
            kml_data[:name_index]
            + placemark_name
            + kml_data[name_index:description_index]
            + placemark_description
            + kml_data[description_index:coord_index]
            + insert_string
            + kml_data[coord_index:]
        )

        with open(new_file_path, 'w') as new_file:
            new_file.write(new_kml_data)


def latlon_to(
    coord_list_orig: List[List[Tuple]], inverse: bool = False
) -> List[List[Tuple]]:
    """
    Convert latitude and longitude coordinates to mercator projection and back.

    Args:
    - coord_list_orig: List of lists oftuples with latitude and longitude coordinates.
    - inverse: Whether to perform inverse projection.

    Returns:
    - List of lists of tuples with converted x and y coordinates.
    """
    coord_list: List[List[Tuple]] = []
    proj = pyproj.Proj(proj='merc', datum='WGS84')

    for coord in coord_list_orig:
        coord_converted: List[Tuple] = []
        for pair in coord:
            x, y = proj(pair[0], pair[1], inverse=inverse)
            coord_converted.append((round(x, 6), round(y, 6)))
        coord_list.append(coord_converted)

    coord_count = str(sum([len(i) for i in coord_list]))
    print(
        'Convert coordinates, inverse:',
        inverse,
        'Total converted coordinates:',
        coord_count,
    )
    print('Sample of converted coordinates:', coord_list[0][:1])
    print('*' * 10)
    return coord_list


def main(track_file_paths: List[str], buffer: int, empty_file_path: str) -> None:
    """
    Main function to process track file, create buffer, plot track, and insert solution
    into KML file.

    Args:
        track_file_path (str): The file path of the track to be processed.
        buffer (float): The buffer distance in meters.
        empty_file_path (str): The file path for the empty file to insert the solution.
    """

    # Read the KML file to get the coordinates in latitude and longitude
    coord_list_latlon = read_kml_file(track_file_paths)

    # Convert the buffer from meters to Mercator units
    buffer_merc = meters_to_mercator_units(buffer, coord_list_latlon[0])

    # Convert the coordinates from latitude and longitude to Mercator coordinates
    coord_list_merc = latlon_to(coord_list_latlon)

    print(f'Buffer: {buffer}, buffer_clean: {buffer_clean}')
    # Create a buffer track using the Mercator coordinates and buffer in Mercator units
    solution_merc = create_buffer_track(coord_list_merc, buffer_merc, buffer_clean)

    # Convert the solution from Mercator coordinates back to latitude and longitude
    solution_latlon = latlon_to([solution_merc], inverse=True)

    # Plot the track
    plot_track(solution_latlon[0], coord_list_latlon, track_file_paths)

    # Convert the solution in latitude and longitude to a string for insert in KML file
    solution_latlon_string = tracks_to_string(solution_latlon)

    # Insert the solution string after the coordinates in the track file and save it
    save_kml(
        empty_file_path=empty_file_path,
        insert_string=solution_latlon_string,
        track_file_paths=track_file_paths,
        buffer=buffer,
        buffer_clean=buffer_clean,
    )


if __name__ == '__main__':
    main(track_file_paths, buffer, empty_file_path)
