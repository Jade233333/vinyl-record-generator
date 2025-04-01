import numpy as np
import pyvista as pv
from pydub import AudioSegment


class AudioHandler:
    def __init__(self, txt_path, wav_path):
        self.txt_path = txt_path
        self.wav_path = wav_path
        self.displacement_raw = self.read_depth_sequence()
        self.audio = AudioSegment.from_file(self.wav_path)
        self.duration = len(self.audio) / 1000.0

    def read_depth_sequence(self):
        with open(self.txt_path, "r") as file:
            sequence = [int(line.strip()) for line in file]
        return np.array(sequence)


class MeshGenerator:
    def __init__(
        self,
        outer_radius,
        inner_radius,
        groove_spacing,
        samples_per_round,
        thickness,
        groove_buffer_coefficient,
        wave_displacement,
        groove_step,
    ):
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.groove_spacing = groove_spacing
        self.wave_displacement = wave_displacement
        self.groove_inner_radius = self.inner_radius + self.groove_spacing / 2
        self.samples_per_round = samples_per_round
        self.thickness = thickness
        self.groove_step = groove_step
        self.groove_buffer_coefficient = groove_buffer_coefficient
        self.groove_top = (
            self.thickness - self.groove_buffer_coefficient * self.groove_step
        )
        self.groove_z = self.displacement_to_groovez()
        self.groove_spiral = self.generate_groove()
        self.edge_spiral = self.generate_spiral()

    def displacement_to_groovez(self):
        original = self.wave_displacement
        max_value = np.max(original)
        down_shift = original - max_value
        steplize = down_shift * self.groove_step
        groove_z = steplize + self.groove_top
        return groove_z

    def generate_spiral(self):
        total_rounds = (self.outer_radius - self.inner_radius) / self.groove_spacing
        theta_max = total_rounds * 2 * np.pi
        num_points = int(total_rounds * self.samples_per_round)
        theta = np.linspace(0, -theta_max, num_points)
        r = self.inner_radius + self.groove_spacing / (2 * np.pi) * (-theta)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        z = np.full_like(x, self.thickness)
        return np.column_stack((x, y, z))

    def generate_groove(self):
        total_rounds = (
            self.outer_radius - self.groove_inner_radius
        ) / self.groove_spacing
        theta_max = total_rounds * 2 * np.pi
        num_points = int(total_rounds * self.samples_per_round)
        theta = np.linspace(0, -theta_max, num_points)
        r = self.groove_inner_radius + self.groove_spacing / (2 * np.pi) * (-theta)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        reversed_z = self.groove_z[::-1]
        z = self.extend_like(
            array=reversed_z,
            template=x,
            compensation_length=self.samples_per_round * 3,
            forward_constant=self.groove_top,
            backward_constant=self.thickness,
        )
        return np.column_stack((x, y, z))

    @staticmethod
    def extend_like(
        array, template, compensation_length, forward_constant, backward_constant
    ):
        target_length = len(template)
        # Add compensation block after the existing data
        compensation_block = np.full(compensation_length, forward_constant)
        array_with_compensation = np.concatenate((array, compensation_block))
        current_length = len(array_with_compensation)
        difference = target_length - current_length
        if difference <= 0:
            return array_with_compensation[:target_length]
        else:
            padding = np.full(difference, backward_constant)
            return np.concatenate((padding, array_with_compensation))

    @staticmethod
    def align_array(array1, array2):
        min_length = min(len(array1), len(array2))
        return array1[:min_length], array2[:min_length], min_length

    def create_faces(self, min_length):
        faces_outer = []
        faces_inner = []
        # Build faces for outer surface
        for i in range(min_length - 1):
            faces_outer.extend([4, i, i + min_length, i + 1 + min_length, i + 1])
        # Build faces for inner surface, with a compensation for the samples_per_round offset
        for i in range(min_length - 1 - self.samples_per_round):
            faces_inner.extend(
                [
                    4,
                    i + min_length,
                    self.samples_per_round + i,
                    self.samples_per_round + i + 1,
                    i + min_length + 1,
                ]
            )
        return faces_inner + faces_outer

    @staticmethod
    def find_trough(mesh):
        z_coords = mesh.points[:, 2]
        return np.min(z_coords)

    @staticmethod
    def find_crest(mesh):
        z_coords = mesh.points[:, 2]
        return np.max(z_coords)

    def generate_mesh(self):
        # Align the spiral arrays
        edge_spiral_aligned, groove_spiral_aligned, min_length = self.align_array(
            self.edge_spiral, self.groove_spiral
        )
        vertices = np.vstack((edge_spiral_aligned, groove_spiral_aligned))
        faces = self.create_faces(min_length)
        # Create top surface and extrude it
        top_surface = pv.PolyData(vertices, faces=np.array(faces))
        crest = self.find_crest(top_surface)
        trough = self.find_trough(top_surface)
        surface_extrude_distance = crest - trough + 0.1
        extruded_surface = top_surface.extrude(
            (0, 0, -surface_extrude_distance), capping=True
        )

        # Create bottom surface from a disc and extrude it
        inner_radius = np.min(np.linalg.norm(vertices[:, :2], axis=1))
        outer_radius = np.max(np.linalg.norm(vertices[:, :2], axis=1))
        bottom_surface = pv.Disc(
            center=(0, 0, 0),
            inner=inner_radius,
            outer=outer_radius,
            r_res=200,
            c_res=200,
        )
        bottom_extrude_distance = trough + 0.1
        extruded_bottom = bottom_surface.extrude(
            (0, 0, bottom_extrude_distance), capping=True
        )

        # Merge and clean the two surfaces
        merged = extruded_bottom.merge(extruded_surface)
        merged = merged.clean()
        return merged


if __name__ == "__main__":
    rpm = 45
    rps = rpm / 60
    groove_step = 0.05
    thickness = 2
    outer_radius = 100
    inner_radius = 3.65
    groove_spacing = 0.8

    audio_data = AudioHandler(
        txt_path="output/4bit_550hz.txt",
        wav_path="output/4bit_550hz.wav",
    )

    total_samples = len(audio_data.displacement_raw)
    total_rounds = rps * audio_data.duration
    samples_per_round = int(total_samples / total_rounds)
    wave_displacement = audio_data.displacement_raw

    mesh_gen = MeshGenerator(
        outer_radius=outer_radius,
        inner_radius=inner_radius,
        groove_spacing=groove_spacing,
        samples_per_round=samples_per_round,
        thickness=thickness,
        groove_buffer_coefficient=3,
        wave_displacement=wave_displacement,
        groove_step=groove_step,
    )
    final_mesh = mesh_gen.generate_mesh()
    final_mesh.save("output/record.stl")
    print("Mesh saved to output/record.stl")
