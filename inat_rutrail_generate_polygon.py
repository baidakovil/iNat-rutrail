"""This file contain program for generating buffer polygon for gps track in KML file."""

import math
import os
import re
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import pyclipper
import pyproj

storing_folder = './rutrail/'
start_folder = 12
end_folder = 121

buffer = 850
buffer_clean = 150
empty_file_path = 'assets/Empty.kml'

dict_remove_solutions = {73: [2, 3, 4]}


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


import re
from typing import List, Tuple


def read_kml_file(file_paths: List[str]) -> List[List[Tuple[float, float]]]:
    """
    Reads a KML file and extracts coordinate data.

    Args:
    - file_paths: list of paths to the KML files.

    Returns:
    - a list of lists with coordinate pairs.
    """
    coord_list = []

    for file_path in file_paths:
        with open(file_path, 'r') as file:
            file_data = file.read()

            if file_path.endswith('.kml'):
                coordinates_data = re.findall(
                    r'<coordinates>(.*?)</coordinates>', file_data, re.DOTALL
                )
                for data in coordinates_data:
                    coordinates = [
                        tuple(map(float, coord.split(',')))
                        for coord in data.strip().split('\n')
                    ]
                    coord_list.append(coordinates)

            elif file_path.endswith('.gpx'):
                coordinates_data = re.findall(
                    r'<trkseg>(.*?)</trkseg>', file_data, re.DOTALL
                )
                for data in coordinates_data:
                    coordinates = re.findall(r'<trkpt lat="(.*?)" lon="(.*?)"', data)
                    coordinates = [(float(lat), float(lon)) for lon, lat in coordinates]
                    coord_list.append(coordinates)
    return coord_list


def create_buffer_track(
    coord_list: List[List[Tuple]], buffer: float, buffer_clean: float
) -> List[List[Tuple]]:
    """
    Create a buffer track based on the given coordinates and buffer size.

    Args:
    - coord_list: List of lists of tuples representing (x, y) coordinates.
    - buffer: Size of the buffer.

    Returns:
    - List of tuples representing the buffered track coordinates.

    Raises: AssertionError if there are more than one solution found.
    """
    coord_list_scaled = [pyclipper.scale_to_clipper(coord) for coord in coord_list]  # type: ignore
    pco = pyclipper.PyclipperOffset()  # type: ignore
    pco.AddPaths(
        paths=coord_list_scaled,
        join_type=pyclipper.JT_MITER,  # type: ignore
        end_type=pyclipper.ET_OPENSQUARE,  # type: ignore
    )
    solution = pco.Execute(pyclipper.scale_to_clipper(buffer))  # type: ignore
    if len(solution) > 1:
        print('WARNING: more than one solution found')

    solution_cleaned = pyclipper.CleanPolygons(  # type: ignore
        polys=pyclipper.scale_from_clipper(solution),  # type: ignore
        distance=buffer_clean,
    )

    print('Solution pairs NOT CLEANED:', str(sum([len(i) for i in solution])))
    print('Solution pairs YES CLEANED:', str(sum([len(i) for i in solution_cleaned])))
    print('Sample of solution:', solution[0][:1])
    print('*' * 10)
    return solution_cleaned


def plot_track(
    sol_list: List[List[Tuple]],
    coord_list: List[List[Tuple]],
    track_file_paths: List[str],
    buffer,
) -> None:
    """
    Plot the track by overlaying the original coordinates and the solution coordinates.

    Args:
    - solutions: List of lists of tuples representing the solution coordinates in
    (latitude, longitude) format.
    - coord_list: List of lists of tuples representing the original coordinates in
    (latitude, longitude) format.
    - track_file_paths: File paths of the original tracks.
    """
    output_folder = os.path.dirname(track_file_paths[0])
    track_no = track_file_paths[0].split('/')[-2]
    remove_solutions = dict_remove_solutions.get(int(track_no), [])
    set_coord = pd.DataFrame()
    inner_tracks_count = 0
    for i, coord in enumerate(coord_list):
        lat_orig, lon_orig = zip(*coord)
        try:
            data_class = (
                f'Original track (file): {os.path.basename(track_file_paths[i])}'
            )
        except IndexError:
            inner_tracks_count += 1
            data_class = f'Original track (inner): {inner_tracks_count}'
        set_coord_temp = pd.DataFrame(
            {
                'lat': lat_orig,
                'lon': lon_orig,
                'data_class': data_class,
                'remove_solutions': 0,
            }
        )
        set_coord = pd.concat([set_coord, set_coord_temp])

    set_sol = pd.DataFrame()
    for i, sol in enumerate(sol_list):
        if len(sol) == 0:
            continue
        lat_sol, lon_sol = zip(*sol)
        set_sol_temp = pd.DataFrame(
            {
                'lat': lat_sol,
                'lon': lon_sol,
                'data_class': f'Solution #{i+1}',
                'remove_solutions': 1 if i + 1 in remove_solutions else 0,
            }
        )
        set_sol = pd.concat([set_sol, set_sol_temp])

    data = pd.concat([set_coord, set_sol])
    fig, ax = plt.subplots(figsize=(50, 50))
    for _, group in data.groupby('data_class'):
        linestyle = 'dotted' if (group['remove_solutions'] == 1).any() else 'solid'
        ax.plot(
            group['lat'],
            group['lon'],
            marker='o',
            label=group['data_class'].unique()[0],
            linestyle=linestyle,
        )
    ax.legend()
    plot_name = (
        os.path.dirname(track_file_paths[0]).split('/')[-1]
        + '_'
        + str(buffer)
        + '_2x_buff.pdf'
    )
    print('Saving plot to:', plot_name)
    plt.savefig(os.path.join(output_folder, plot_name), dpi=300, bbox_inches='tight')
    # mplleaflet.show(fig=ax.figure)
    print('Plot saved to:', plot_name)
    print('*' * 10)


def tracks_to_string(
    tracks: List[List[Tuple]],
    track_file_paths: List[str],
) -> str:
    """
    Convert a list of (x, y) points to a string representation.
    Args:
    - tracks: List of lists of tuples representing (x, y) points
    Returns:
    - String representation of the track
    """
    track_no = track_file_paths[0].split('/')[-2]
    remove_solutions = dict_remove_solutions.get(int(track_no), [])
    solutions = []
    for i, track in enumerate(tracks):
        if len(track) == 0:
            continue
        if i + 1 not in remove_solutions:
            solutions.append(
                '\n'.join([f'              {point[0]},{point[1]},0' for point in track])
            )

    return '\n'.join(solutions)


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
    output_folder = os.path.dirname(track_file_paths[0])
    file_names_full = ", ".join(
        [os.path.basename(track_file_path) for track_file_path in track_file_paths]
    )
    new_file_path = os.path.join(
        output_folder,
        os.path.dirname(track_file_paths[0]).split('/')[-1]
        + '_'
        + str(buffer)
        + '_buff.kml',
    )
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
            + '\n'
            + insert_string
            + '\n            '
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


def distance(a, b, c):
    """Calculate the perpendicular distance from point c to the line segment ab."""
    ax, ay = a
    bx, by = b
    cx, cy = c

    dx = bx - ax
    dy = by - ay

    if dx == dy == 0:  # The points are the same.
        return math.hypot(cx - ax, cy - ay)

    t = ((cx - ax) * dx + (cy - ay) * dy) / (dx * dx + dy * dy)

    if t < 0:  # Point c is outside the line segment, closer to point a.
        dx = cx - ax
        dy = cy - ay
    elif t > 1:  # Point c is outside the line segment, closer to point b.
        dx = cx - bx
        dy = cy - by
    else:  # Point c is inside the line segment.
        near_x = ax + t * dx
        near_y = ay + t * dy
        dx = cx - near_x
        dy = cy - near_y

    return math.hypot(dx, dy)


def simplify_track(track, delta):
    """Simplify a track using the Ramer-Douglas-Peucker algorithm."""
    if len(track) < 3:
        return track

    # Find the point in the track that is furthest from the line segment formed by the first and last points.
    max_dist = 0.0
    max_index = 0
    for i in range(1, len(track) - 1):
        dist = distance(track[0], track[-1], track[i])
        if dist > max_dist:
            max_dist = dist
            max_index = i

    # If the maximum distance is greater than delta, split the track into two at this point and simplify each half.
    if max_dist > delta:
        return simplify_track(track[: max_index + 1], delta)[:-1] + simplify_track(
            track[max_index:], delta
        )

    # Otherwise, all points between the first and last are discarded.
    else:
        return [track[0], track[-1]]


def simplify_tracks(tracks, delta):
    """Simplify a list of tracks."""
    return [simplify_track(track, delta) for track in tracks]


def process_track(
    track_file_paths: List[str], buffer: int, buffer_clean: int, empty_file_path: str
) -> None:
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
    buffer_clean_merc = meters_to_mercator_units(buffer_clean, coord_list_latlon[0])

    # Convert the coordinates from latitude and longitude to Mercator coordinates
    coord_list_merc = latlon_to(coord_list_latlon)

    # coord_list_merc_sim = coord_list_merc
    # coord_list_latlon_sim = coord_list_latlon
    coord_list_merc_sim = simplify_tracks(coord_list_merc, buffer_clean_merc * 2)
    coord_list_latlon_sim = latlon_to(coord_list_merc_sim, inverse=True)

    print(f'Buffer: {buffer}, buffer_clean: {buffer_clean}')
    # Create a buffer track using the Mercator coordinates and buffer in Mercator units
    solutions_merc_sim = create_buffer_track(
        coord_list_merc_sim, buffer_merc, buffer_clean
    )

    # Convert the solution from Mercator coordinates back to latitude and longitude
    solutions_latlon_sim = latlon_to(solutions_merc_sim, inverse=True)

    coord_list_latlon_sim.extend(coord_list_latlon)
    # Plot the track
    plot_track(
        sol_list=solutions_latlon_sim,
        coord_list=coord_list_latlon_sim,
        track_file_paths=track_file_paths,
        buffer=buffer,
    )

    # Convert the solution in latitude and longitude to a string for insert in KML file
    solution_latlon_string = tracks_to_string(solutions_latlon_sim, track_file_paths)

    # Insert the solution string after the coordinates in the track file and save it
    save_kml(
        empty_file_path=empty_file_path,
        insert_string=solution_latlon_string,
        track_file_paths=track_file_paths,
        buffer=buffer,
        buffer_clean=buffer_clean,
    )


def main():
    for i in range(start_folder, end_folder + 1):
        folder = os.path.join(storing_folder, str(i))
        if not os.path.exists(folder):
            continue
        track_file_paths = [
            os.path.join(folder, file)
            for file in os.listdir(folder)
            if (file.endswith('.kml') or file.endswith('.gpx'))
            and (not file.endswith('_buff.kml'))
        ]
        process_track(track_file_paths, buffer, buffer_clean, empty_file_path)


if __name__ == '__main__':
    main()
