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


def find_trough(mesh):
    z_coords = mesh.points[:, 2]
    min_z = np.min(z_coords)

    return min_z


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
    z = extend_backward_like(reversed_z, x, groove_top)
    return np.column_stack((x, y, z))


def extend_backward_like(array, template, constant=0):
    target_length = len(template)
    current_length = len(array)
    difference = target_length - current_length

    if difference <= 0:
        return array[:target_length]
    else:
        return np.pad(array, (difference, 0), mode="constant", constant_values=constant)


rpm = 45
rps = rpm / 60
sampling_rate = 5500
outer_radius = 150.8
inner_radius = 3.64
groove_spacing = 0.8
thickness = 1.9
groove_top = thickness - 0.04
groove_step = 0.02
audio_raw = read_depth_sequence("output/4bit_5500hz.txt")
groove_z = standardize_audio_depth(audio_raw)
audio = AudioSegment.from_file("output/4bit_5500hz.wav")
duration = len(audio) / 1000.0
total_samples = len(groove_z)
total_rounds = rps * duration
samples_per_round = int(total_samples / total_rounds)

# Generate both spirals with a vertical offset
spiral1 = generate_spiral(
    outer_radius, inner_radius, groove_spacing, samples_per_round, z=thickness
)
spiral2 = generate_groove(
    outer_radius,
    (inner_radius + groove_spacing / 2),
    groove_spacing,
    samples_per_round,
    groove_z=groove_z,
    groove_top=thickness,
)

# Truncate to the same length
min_length = min(len(spiral1), len(spiral2))
spiral1 = spiral1[:min_length]
spiral2 = spiral2[:min_length]

# Combine points from both spirals
points = np.vstack((spiral1, spiral2))

faces = []
for i in range(min_length - 1):
    faces.extend([4, i, i + min_length, i + 1 + min_length, i + 1])

for i in range(min_length - 1 - samples_per_round):
    faces.extend(
        [
            4,
            i + min_length,
            samples_per_round + i,
            i + min_length + 1,
            samples_per_round + i + 1,
        ]
    )

top_surface = pv.PolyData(points, faces=np.array(faces))
min_z = find_trough(top_surface)
max_z = find_crest(top_surface)

extruded_surface = top_surface.extrude((0, 0, -(max_z - min_z)), capping=True)
min_z = find_trough(extruded_surface)

bottom_surface = pv.Disc(
    center=(0, 0, 0), inner=0, outer=outer_radius, r_res=200, c_res=200
)
extruded_bottom = bottom_surface.extrude((0, 0, min_z), capping=True)
merged = extruded_surface.merge(extruded_bottom)

merged = merged.clean()

merged.save("output/manual_merged_solid_disk.stl")
extruded_surface.save("surface.stl")
pl = pv.Plotter()
pl.add_mesh(merged, show_edges=False, color="lightblue")
pl.show()
