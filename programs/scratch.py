import numpy as np


# read depth data from txt file
def read_depth_sequence(file_path):
    with open(file_path, "r") as file:
        sequence = [int(line.strip()) for line in file]
    return np.array(sequence)


# convert sequence to z coordination
def modify_depth(original):
    max_value = np.max(original)
    negative = original - max_value
    specialized = negative * groove_step
    down_shift = specialized + groove_top
    return down_shift


# variables in mm
outside_demension = 150.8
max_radius = 146.05
min_radius = 60.3
thickness = 1.9
center_hole_radius = 3.63
rpm = 45
time_sec = 90

audio_raw = read_depth_sequence("output/final_4bit.out")
groove_width = 0.075
groove_min_depth = 0.045
groove_spacing = 0.75
groove_step = 0.015

# calculation
groove_top = thickness - groove_min_depth
rps = rpm / 60
num_grooves = time_sec * rps
starting_radius = max_radius
ending_radius = max_radius - (groove_spacing * num_grooves)
num_samples = np.size(audio_raw)


# z
grooves_z = modify_depth(audio_raw)

# xy in polar form
# groovez
radii = np.linspace(starting_radius, ending_radius, num_samples)


# test
