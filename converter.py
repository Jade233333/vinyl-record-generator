import numpy as np
from stl import mesh

# Parameters
filename = "debaser.txt"
sampling_rate = 44100  # (44.1 kHz audio)
rpm = 33.3  # rev per min
sec_per_min = 60  # seconds per minute
rate_divisor = 4  # downsampling factor
diameter_inch = 11.8  # diameter of record in inches
inner_hole_inch = 0.286  # diameter of center hole in inches
inner_rad_inch = 2.35  # innermost groove radius in inches
outer_rad_inch = 5.75  # outermost groove radius in inches
record_height_inch = 0.04  # height of record in inches
amplitude_micron = 24  # amplitude of signal (in 16 micron steps)
bevel = 0.5  # bevel edge of groove
groove_width_inch = 3 / 600  # width of the groove (converted to inches)
depth_micron = 6  # depth in 16 micron steps
microns_per_inch = 25400  # scaling factor for microns
dpi = 600
microns_per_layer = 16  # microns per vertical print layer

# Convert units to inches
amplitude_inch = amplitude_micron * microns_per_layer / microns_per_inch
depth_inch = depth_micron * microns_per_layer / microns_per_inch

# Load and process audio data


def process_audio_data(filename, amplitude_inch):
    with open(filename, 'r') as f:
        raw_data = f.read().strip().split(',')

    audio_data = np.array([float(x) for x in raw_data], dtype=np.float32)

    # Normalize audio data
    maxval = np.max(np.abs(audio_data))
    if maxval > 0:
        audio_data *= amplitude_inch / maxval

    # Debug: check first 10 audio samples
    print(f"Loaded audio data: {audio_data[:10]}")
    return audio_data

# Setup the geometry of the record


def setup_record_shape(diameter_inch, inner_hole_inch, record_height_inch, theta_iter):
    theta_values = np.arange(0, 2 * np.pi, 2 * np.pi / theta_iter)

    record_perimeter_upper = np.array([
        [(diameter_inch / 2) * (1 + np.cos(theta)), (diameter_inch / 2)
         * (1 + np.sin(theta)), record_height_inch]
        for theta in theta_values
    ])
    record_perimeter_lower = np.array([
        [(diameter_inch / 2) * (1 + np.cos(theta)),
         (diameter_inch / 2) * (1 + np.sin(theta)), 0]
        for theta in theta_values
    ])

    record_hole_upper = np.array([
        [(inner_hole_inch / 2) * (1 + np.cos(theta)),
         (inner_hole_inch / 2) * (1 + np.sin(theta)), record_height_inch]
        for theta in theta_values
    ])
    record_hole_lower = np.array([
        [(inner_hole_inch / 2) * (1 + np.cos(theta)),
         (inner_hole_inch / 2) * (1 + np.sin(theta)), 0]
        for theta in theta_values
    ])

    return record_perimeter_upper, record_perimeter_lower, record_hole_upper, record_hole_lower

# Generate grooves based on audio data


def draw_grooves(audio_data, record_perimeter_upper, record_perimeter_lower, theta_iter, inner_rad_inch, outer_rad_inch, groove_width_inch, amplitude_inch, record_height_inch):
    radius = outer_rad_inch
    rad_incr = (groove_width_inch + groove_width_inch) / theta_iter

    # STL mesh
    vertices = []
    total_samples = len(audio_data)
    sample_num = 0

    for theta in np.arange(0, 2 * np.pi, 2 * np.pi / theta_iter):
        if sample_num >= total_samples:
            break

        groove_height = record_height_inch - depth_inch - \
            amplitude_inch + audio_data[sample_num]
        sample_num += 1

        x_outer = (radius + amplitude_inch * bevel) * np.cos(theta)
        y_outer = (radius + amplitude_inch * bevel) * np.sin(theta)
        x_inner = (radius - groove_width_inch -
                   amplitude_inch * bevel) * np.cos(theta)
        y_inner = (radius - groove_width_inch -
                   amplitude_inch * bevel) * np.sin(theta)

        # Add vertices for the current step
        vertices.append([x_outer, y_outer, record_height_inch])
        vertices.append([x_inner, y_inner, groove_height])

        print(f"Added vertices: ({x_outer}, {y_outer}, {
              record_height_inch}), ({x_inner}, {y_inner}, {groove_height})")

        radius -= rad_incr

    print(f"Total vertices: {len(vertices)}")
    return vertices

# Main function


def create_stl_file(filename):
    audio_data = process_audio_data(filename, amplitude_inch)
    theta_iter = (sampling_rate * sec_per_min) / (rate_divisor * rpm)

    record_perimeter_upper, record_perimeter_lower, record_hole_upper, record_hole_lower = setup_record_shape(
        diameter_inch, inner_hole_inch, record_height_inch, theta_iter
    )

    vertices = draw_grooves(audio_data, record_perimeter_upper, record_perimeter_lower, theta_iter,
                            inner_rad_inch, outer_rad_inch, groove_width_inch, amplitude_inch, record_height_inch)

    # Create the mesh
    num_faces = len(vertices) // 3
    record_mesh = mesh.Mesh(np.zeros(num_faces, dtype=mesh.Mesh.dtype))

    # Assign vertices to the mesh
    for i in range(num_faces):
        record_mesh.vectors[i] = vertices[i*3:i*3+3]

    # Save the STL
    record_mesh.save(filename + ".stl")
    print(f"STL file saved with {num_faces} faces.")


# Example usage:
create_stl_file("debaser")
