# import necessary libraries
import numpy as np  # for data manipulation
from stl import mesh  # for stl file generation
# from testing preview


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


# testing
depth_sequence = read_depth_sequence("final_4bit.out")
print(depth_sequence)
print(np.max(modify_depth(depth_sequence, 1)))
print(np.min(modify_depth(depth_sequence, 1)))
