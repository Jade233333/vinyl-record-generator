import pyvista as pv

# Dimensions (same as before)
outer_dimension = 150.8
center_hole_radius = 3.64
thickness = 1.9

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

# Verify solidness (should return True)
print("Is solid?", vinyl_base.is_all_triangles)

# Save and visualize
vinyl_base.save("output/vinyl_base_solid.stl")
vinyl_base.plot(show_edges=True, cpos="xz")

