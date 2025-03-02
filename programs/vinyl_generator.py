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
groove_step = z_accuracy * 2

groove_top = thickness - groove_min_depth
groove_rounds = time_sec * rps
starting_radius = max_radius
ending_radius = max_radius - (groove_spacing * groove_rounds)
sample_count = np.size(audio_raw)
angle_per_sample = groove_rounds * 2 * np.pi / sample_count


# vertices
groove_z_bottom = standardize_audio_depth(audio_raw)
max_depth = thickness - np.min(groove_z_bottom)
groove_radii = np.linspace(starting_radius, ending_radius, sample_count)
groove_angles = angle_per_sample * np.arange(sample_count)

###########################################################
##################   Modified Geometry Synthesis  ##########
############################################################


# 1. Create the solid base with center hole (optimized version)
def create_base_mesh():
    solid = pv.Cylinder(
        center=(0, 0, thickness / 2),
        direction=(0, 0, 1),
        radius=outer_dimension,
        height=thickness,
    ).triangulate()

    hole = pv.Cylinder(
        center=(0, 0, thickness / 2),
        direction=(0, 0, 1),
        radius=center_hole_radius,
        height=thickness + 2,
    ).triangulate()

    return solid.boolean_difference(hole).clean()


# 2. Generate groove geometry as surface displacement
def create_groove_surface():
    # Create spiral path using your existing parameters
    points = np.column_stack(
        (
            groove_radii * np.cos(groove_angles),
            groove_radii * np.sin(groove_angles),
            groove_z_bottom,  # Use your depth-modulated Z values
        )
    )

    fake_radius = max_depth / np.sqrt(2)
    print(fake_radius)
    # Create polyline from points
    poly = pv.PolyData()
    poly.points = points
    cells = np.full((len(points) - 1, 3), 2, dtype=np.int_)
    cells[:, 1] = np.arange(0, len(points) - 1, dtype=np.int_)
    cells[:, 2] = np.arange(1, len(points), dtype=np.int_)
    poly.lines = cells

    # Create tube with variable radius using your groove width parameters
    groove = poly.tube(radius=fake_radius, n_sides=4, capping=False).rotate_z(
        45, inplace=True
    )

    # Apply your quantization
    groove.points[:, :2] = np.round(groove.points[:, :2] / xy_accuracy) * xy_accuracy
    groove.points[:, 2] = np.round(groove.points[:, 2] / z_accuracy) * z_accuracy

    return groove.triangulate().clean()


# 3. Combine base and grooves
def combine_meshes(base, groove):
    # Use your existing vertex quantization for alignment
    groove.points[:, :2] = np.round(groove.points[:, :2] / xy_accuracy) * xy_accuracy
    groove.points[:, 2] = np.round(groove.points[:, 2] / z_accuracy) * z_accuracy

    # Merge instead of boolean operation
    combined = base.merge(groove, merge_points=True, tolerance=xy_accuracy)
    return combined.clean()


# Main execution
if __name__ == "__main__":
    # Create base mesh
    base_mesh = create_base_mesh()
    base_mesh.save("output/base.stl")

    # Create groove surface
    groove_mesh = create_groove_surface()
    groove_mesh.save("output/grooves.stl")
    # Combine using point quantization
    final_mesh = combine_meshes(base_mesh, groove_mesh)

    # Export results
    final_mesh.save("output/vinyl_with_grooves.stl")
    print(f"Final mesh: {final_mesh.n_points} points, {final_mesh.n_cells} cells")

    # Add this after your base mesh and groove mesh creation, but before combining

    # Plot base mesh
    p = pv.Plotter()
    p.add_mesh(base_mesh, color="tan", show_edges=True, opacity=0.8)
    p.add_text("Base Mesh", font_size=20)
    p.show(cpos="xy")

    # Plot groove mesh
    p = pv.Plotter()
    p.add_mesh(groove_mesh, color="red", show_edges=True, opacity=1.0)
    p.add_text("Groove Mesh", font_size=20)
    p.show(cpos="xy")

    # Plot cross-section view
    p = pv.Plotter()
    p.add_mesh(base_mesh, color="tan", show_edges=True, opacity=0.3)
    p.add_mesh(groove_mesh, color="red", show_edges=True, opacity=0.8)
    p.add_text("Combined View (Transparent Base)", font_size=20)
    p.show(cpos="xz")
