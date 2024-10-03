import numpy as np
from stl import mesh

# Constants
theta_iter = 10000  # Number of theta steps per cycle
diameter = 12  # Diameter of record in inches
inner_hole = 0.286  # Diameter of center hole in inches
inner_rad = 2.35  # Radius of innermost groove in inches
outer_rad = 5.75  # Radius of outermost groove in inches
groove_spacing = 20  # Pixel spacing of grooves
bevel = 2  # Pixel width of groove bevel

# Record parameters
record_height = 0.08  # Height of record in inches
record_bottom = 0  # Height of bottom of record

# Test parameters
amplitude = np.array([2, 4, 8])  # Amplitude of the sine wave
frequency = np.array([1000, 500, 0])  # Cycles per rotation
depth = np.array([0.5, 1, 0])  # Groove depth in inches
groove_width = np.array([1, 2, 3])  # Groove width in pixels

# Scaling factors
microns_per_inch = 25400
dpi = 254
microns_per_layer = 80

# Convert units
# Convert units
groove_spacing /= dpi
bevel /= dpi
amplitude = amplitude * microns_per_layer / microns_per_inch
depth = depth * microns_per_layer / microns_per_inch
groove_width = groove_width.astype(float) / dpi
# Function to create a ring of vertices


def create_ring(radius, z, segments=theta_iter):
    theta = np.linspace(0, 2 * np.pi, segments)
    x = (diameter / 2 + radius * np.cos(theta))
    y = (diameter / 2 + radius * np.sin(theta))
    return np.column_stack((x, y, np.full_like(x, z)))


# Create base shape of the record
record_perimeter_upper = create_ring(diameter / 2, record_height)
record_perimeter_lower = create_ring(diameter / 2, record_bottom)
record_hole_upper = create_ring(inner_hole / 2, record_height)
record_hole_lower = create_ring(inner_hole / 2, record_bottom)

# List to store all triangles for STL mesh
triangles = []


def add_quad_strip(vertices1, vertices2):
    for i in range(len(vertices1) - 1):
        triangles.append([vertices1[i], vertices1[i + 1], vertices2[i + 1]])
        triangles.append([vertices1[i], vertices2[i + 1], vertices2[i]])


# Connect the record perimeter and hole
add_quad_strip(record_hole_upper, record_hole_lower)
add_quad_strip(record_hole_lower, record_perimeter_lower)
add_quad_strip(record_perimeter_lower, record_perimeter_upper)

last_edge = record_perimeter_upper  # Last edge to connect with grooves

# Draw grooves
radius = outer_rad  # Start with the outermost radius
groove_num = 0

for freq_idx in range(2):
    for amp_idx in range(3):
        for depth_idx in range(2):
            for width_idx in range(3):
                for _ in range(2):
                    groove_outer_upper = create_ring(
                        radius + bevel, record_height)
                    groove_outer_lower = create_ring(radius, record_height - depth[depth_idx] - amplitude[amp_idx] + amplitude[amp_idx] * np.sin(
                        np.linspace(0, 2 * np.pi, theta_iter) * frequency[freq_idx]))
                    groove_inner_lower = create_ring(radius - groove_width[width_idx], record_height - depth[depth_idx] -
                                                     amplitude[amp_idx] + amplitude[amp_idx] * np.sin(np.linspace(0, 2 * np.pi, theta_iter) * frequency[freq_idx]))
                    groove_inner_upper = create_ring(
                        radius - groove_width[width_idx] - bevel, record_height)

                    add_quad_strip(last_edge, groove_outer_upper)
                    add_quad_strip(groove_outer_upper, groove_outer_lower)
                    add_quad_strip(groove_outer_lower, groove_inner_lower)
                    add_quad_strip(groove_inner_lower, groove_inner_upper)

                    last_edge = groove_inner_upper
                    radius -= groove_spacing + groove_width[width_idx]
                    groove_num += 1
                    print(f"{groove_num} of 72 grooves drawn")

                radius -= 2 * groove_spacing  # Extra spacing
            radius -= 2 * groove_spacing  # Extra spacing
        radius -= 2 * groove_spacing  # Extra spacing
    radius -= 2 * groove_spacing  # Extra spacing

# Close the remaining space between the last groove and the center hole
add_quad_strip(last_edge, record_hole_upper)

# Convert list of triangles to numpy array
triangles = np.array(triangles)

# Create mesh
record_mesh = mesh.Mesh(np.zeros(triangles.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(triangles):
    for j in range(3):
        record_mesh.vectors[i][j] = f[j]

# Save as STL
record_mesh.save('test.stl')
