import numpy as np
import pyvista as pv


############################################################
##################  Functions  #############################
############################################################
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


def polar_to_quantized_cartesian(radii, angles, xy_precision):
    x = radii * np.cos(angles)
    y = radii * np.sin(angles)
    return np.round(x / xy_precision) * xy_precision, np.round(
        y / xy_precision
    ) * xy_precision


def vertices_coords_synthesis(radii, angles, xy_precision, z):
    x, y = polar_to_quantized_cartesian(radii, angles, xy_precision)
    vertices = np.vstack((x, y, z)).T
    return vertices


############################################################
##################   Data and Variables  ###################
############################################################
# vinyl record variables in mm
outer_dimension = 150.8
max_radius = 146.04
min_radius = 60.3
thickness = 1.9
center_hole_radius = 3.64
rpm = 45
time_sec = 90
rps = rpm / 60

# printer variables
xy_accuracy = 0.02
z_accuracy = 0.02


############################################################
##################   Points   ##############################
############################################################
# groove variables
audio_raw = read_depth_sequence("output/4bit_5500hz.txt")
groove_spacing = 0.8
groove_min_depth = 0.04
groove_width = 0.8
bottom_offset_factor = 0.2  # e.g. 20% of half the groove width
groove_step = z_accuracy

groove_top = thickness - groove_min_depth
groove_rounds = time_sec * rps
starting_radius = max_radius
ending_radius = max_radius - (groove_spacing * groove_rounds)
sample_count = np.size(audio_raw)
angle_per_sample = groove_rounds * 2 * np.pi / sample_count

groove_shift_value_top = groove_width / 2
groove_shift_value_bottom = bottom_offset_factor * groove_width / 2

# vertices
groove_z_bottom = standardize_audio_depth(audio_raw)
groove_z_top = np.full_like(groove_z_bottom, thickness)
groove_radii = np.linspace(starting_radius, ending_radius, sample_count)
groove_angles = angle_per_sample * np.arange(sample_count)

groove_radii_inner_top = groove_radii - groove_shift_value_top
groove_radii_outer_top = groove_radii + groove_shift_value_top
groove_radii_inner_bottom = groove_radii - groove_shift_value_bottom
groove_radii_outer_bottom = groove_radii + groove_shift_value_bottom

groove_inner_top = vertices_coords_synthesis(
    groove_radii_inner_top, groove_angles, xy_accuracy, groove_z_top
)
groove_outer_top = vertices_coords_synthesis(
    groove_radii_outer_top, groove_angles, xy_accuracy, groove_z_top
)
groove_inner_bottom = vertices_coords_synthesis(
    groove_radii_inner_bottom, groove_angles, xy_accuracy, groove_z_bottom
)
groove_outer_bottom = vertices_coords_synthesis(
    groove_radii_outer_bottom, groove_angles, xy_accuracy, groove_z_bottom
)

# Define the number of cross-sections (samples along the groove)
N = groove_inner_top.shape[0]

# Build the list of cross-section vertices in a consistent order.
# Here we assume a closed loop per cross-section in the order:
# [inner_top, inner_bottom, outer_bottom, outer_top]
cross_sections = []
for i in range(N):
    cs = [
        groove_inner_top[i],
        groove_inner_bottom[i],
        groove_outer_bottom[i],
        groove_outer_top[i],
    ]
    cross_sections.append(cs)

# Flatten the list of cross-sections into one big vertex array.
vertices = np.array(cross_sections).reshape(-1, 3)

# For each adjacent pair of cross-sections, create quad faces.
# The quad connecting two adjacent cross-sections along edge j is defined by:
# [i*4 + j, (i+1)*4 + j, (i+1)*4 + ((j+1)%4), i*4 + ((j+1)%4)]
faces = []
num_vertices_per_section = 4

for i in range(N - 1):
    for j in range(num_vertices_per_section):
        j_next = (j + 1) % num_vertices_per_section
        v0 = i * num_vertices_per_section + j
        v1 = (i + 1) * num_vertices_per_section + j
        v2 = (i + 1) * num_vertices_per_section + j_next
        v3 = i * num_vertices_per_section + j_next
        # Each quad face is defined as [4, v0, v1, v2, v3]
        faces.append([4, v0, v1, v2, v3])

# Convert the list of faces to a flat numpy array (VTK expects a flat list)
flat_faces = np.hstack(faces)

# Create the PyVista PolyData mesh.
groove_mesh = pv.PolyData(vertices, flat_faces).triangulate()
groove_mesh.save("output/groove.stl")

# Visualize to check if everything is connected as expected.
# groove_mesh.plot(show_edges=True)
# pl = pv.Plotter()
# _ = pl.add_mesh(groove_mesh)
# pl.camera.zoom(2.0)
# pl.show()

# Create a SOLID cylinder (no hole)
solid_cylinder = pv.Cylinder(
    center=(0, 0, thickness / 2),  # Center at mid-height
    direction=(0, 0, 1),  # Align along Z-axis
    radius=outer_dimension,
    height=thickness,
    resolution=150,
).triangulate()

# Create a smaller cylinder for the center hole
hole_cylinder = pv.Cylinder(
    center=(0, 0, thickness / 2),
    direction=(0, 0, 1),
    radius=center_hole_radius,
    height=thickness + 2,  # Extra height to ensure clean subtraction
    resolution=150,
).triangulate()

# Subtract the hole from the main cylinder
vinyl_base = solid_cylinder.boolean_difference(hole_cylinder)
vinyl = vinyl_base.boolean_difference(groove_mesh)

# Save and visualize
vinyl.save("output/vinyl.stl")
vinyl.plot(show_edges=True, cpos="xz")
