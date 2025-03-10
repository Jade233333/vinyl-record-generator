import numpy as np
import pyvista as pv
from pydub import AudioSegment


# read depth data from txt file
def read_depth_sequence(file_path):
    with open(file_path, "r") as file:
        sequence = [int(line.strip()) for line in file]
    return np.array(sequence)


# convert sequence to z coordination
def standardize_audio_depth(original):
    max_value = np.max(original)
    negative = original - max_value
    specialized = negative * groove_step
    down_shift = specialized + groove_top
    return down_shift


# find minimum hight in a mesh
def find_trough(mesh):
    z_coords = mesh.points[:, 2]
    min_z = np.min(z_coords)

    return min_z


# find maximum hight in a mesh
def find_crest(mesh):
    z_coords = mesh.points[:, 2]
    max_z = np.min(z_coords)

    return max_z


def generate_spiral(outer_radius, inner_radius, increment, samples_per_round, z):
    total_rounds = (outer_radius - inner_radius) / increment
    theta_max = total_rounds * 2 * np.pi
    num_points = int(total_rounds * samples_per_round)
    theta = np.linspace(0, theta_max, num_points)
    r = inner_radius + increment / (2 * np.pi) * theta
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = np.full_like(x, z)
    return np.column_stack((x, y, z))


def generate_groove(
    outer_radius, inner_radius, increment, samples_per_round, groove_top, groove_z
):
    total_rounds = (outer_radius - inner_radius) / increment
    theta_max = total_rounds * 2 * np.pi
    num_points = int(total_rounds * samples_per_round)
    theta = np.linspace(0, theta_max, num_points)
    r = inner_radius + increment / (2 * np.pi) * theta
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    reversed_z = groove_z[::-1]
    z = extend_like(
        reversed_z, x, compensation_length=samples_per_round * 3, constant=groove_top
    )

    return np.column_stack((x, y, z))


def extend_like(array, template, compensation_length, constant):
    """
    inspired by numpy.full_like
    extend an existing array to the length of template arrary in both direction
    """
    target_length = len(template)
    current_length = len(array)

    # Add the compensation block after the existing data
    compensation_block = np.full(compensation_length, constant)
    array_with_compensation = np.concatenate((array, compensation_block))

    # Recalculate length after adding the compensation block
    current_length = len(array_with_compensation)
    difference = target_length - current_length

    if difference <= 0:
        # Trim the array if it's longer than the target
        return array_with_compensation[:target_length]
    else:
        # Pad the difference before the array
        padding = np.full(difference, constant)
        return np.concatenate((padding, array_with_compensation))


def align_array(array1, array2):
    min_length = min(len(array1), len(array2))
    array1 = array1[:min_length]
    array2 = array2[:min_length]
    return array1, array2, min_length


# variables
rpm = 45
rps = rpm / 60
sampling_rate = 5500
outer_radius = 100
inner_radius = 3.65
groove_spacing = 0.8
thickness = 2
groove_step = 0.05
groove_top = thickness - 2 * groove_step
audio_raw = read_depth_sequence("output/4bit_5500hz.txt")
groove_z = standardize_audio_depth(audio_raw)
audio = AudioSegment.from_file("output/4bit_5500hz.wav")
duration = len(audio) / 1000.0
total_samples = len(groove_z)
total_rounds = rps * duration
samples_per_round = int(total_samples / total_rounds)


# use two spirals to constract a surface
edge_spiral = generate_spiral(
    outer_radius, inner_radius, groove_spacing, samples_per_round, z=thickness
)
groove_spiral = generate_groove(
    outer_radius,
    inner_radius + groove_spacing / 2,
    groove_spacing,
    samples_per_round,
    groove_z=groove_z,
    groove_top=thickness,
)

# truncate two spirals to the same length
edge_spiral, groove_spiral, min_length = align_array(edge_spiral, groove_spiral)
# create an arrary to store coords of vertices
vertices = np.vstack((edge_spiral, groove_spiral))

# constract faces from edge_spiral to bot the groove_spiral inside and outside
# extrude
faces_outer = []
faces_inner = []
for i in range(min_length - 1):
    faces_outer.extend([4, i, i + min_length, i + 1 + min_length, i + 1])
for i in range(min_length - 1 - samples_per_round):
    faces_inner.extend(
        [
            4,
            i + min_length,
            samples_per_round + i,
            samples_per_round + i + 1,
            i + min_length + 1,
        ]
    )
faces = faces_inner + faces_outer
top_surface = pv.PolyData(vertices, faces=np.array(faces))
extruded_surface = top_surface.extrude(
    (0, 0, -0.5 - (find_crest(top_surface) - find_trough(top_surface))), capping=True
)

# create bottom from a flat Disc
#  extrude
bottom_surface = pv.Disc(
    center=(0, 0, 0), inner=inner_radius, outer=outer_radius, r_res=200, c_res=200
)
extruded_bottom = bottom_surface.extrude(
    (0, 0, find_trough(top_surface) - 0.1), capping=True
)

# merge top and bottom surface, done
merged = extruded_bottom.merge(extruded_surface)
merged = merged.clean()
merged.save("output/record.stl")
