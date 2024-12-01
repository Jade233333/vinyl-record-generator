# import necessary libraries
import numpy as np  # for data manipulation
from stl import mesh  # for stl file generation
# from testing preview


# constants in mm
outside_demension = 150.8
starting_radius = 146.05
ending_radius = 60.3
thickness = 1.9
center_hole_radius = 3.63
groove_width = 0.056
groove_depth = 0.048
groove_distance = 1.12

# read depth data from txt file


def read_depth_sequence(file_path):
    with open(file_path, "r") as file:
        sequence = [int(line.strip()) for line in file]
    return np.array(sequence)


# modify depth sequence to distance below the top surface
def modify_depth(original, top):
    min_value = np.min(original)
    modified = original - min_value + top
    return modified


# z
grooves_z = modify_depth(read_depth_sequence("final_4bit.out"))


# xy in polar form
# groove
num_grooves = int((starting_radius - ending_radius) / groove_distance)
radii = np.linspace(starting_radius, ending_radius, num_grooves*10000)


# test
