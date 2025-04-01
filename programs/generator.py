from typing import Optional, Literal
import numpy as np
import pyvista as pv
from pydub import AudioSegment
from mp32out import AudioData


class AudioHandler:
    def __init__(
        self,
        audio_path,
        target_bit_rate: Optional[Literal["4bit", "8bit"]],
        target_sampling_rate=None,
    ):
        self.audio_path = audio_path
        self.audio = AudioSegment.from_file(self.audio_path)
        self.duration = len(self.audio) / 1000.0
        self.target_bit_rate = target_bit_rate
        self.target_sampling_rate = target_sampling_rate
        self.audio_data = AudioData(audio_segment=self.audio)
        self._reduce_bit()
        self._resmaple()
        self.displacement_raw = self.audio_data.samples

    def _resmaple(self):
        if self.target_sampling_rate is not None:
            self.audio_data.resample(self.target_sampling_rate)

    def _reduce_bit(self):
        if self.target_bit_rate == "4bit":
            self.audio_data.to_raw_4bit()
        elif self.target_bit_rate == "8bit":
            self.audio_data.to_8bit()


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
        self.groove_z = self._displacement_to_groovez()

    def _displacement_to_groovez(self):
        original = self.wave_displacement
        max_value = np.max(original)
        down_shift = original - max_value
        steplize = down_shift * self.groove_step
        groove_z = steplize + self.groove_top
        return groove_z

    def _generate_spiral(self):
        total_rounds = (self.outer_radius - self.inner_radius) / self.groove_spacing
        theta_max = total_rounds * 2 * np.pi
        num_points = int(total_rounds * self.samples_per_round)
        theta = np.linspace(0, -theta_max, num_points)
        r = self.inner_radius + self.groove_spacing / (2 * np.pi) * (-theta)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        z = np.full_like(x, self.thickness)
        return np.column_stack((x, y, z))

    def _generate_groove(self):
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
        z = self._extend_like(
            array=reversed_z,
            template=x,
            compensation_length=self.samples_per_round * 3,
            forward_constant=self.groove_top,
            backward_constant=self.thickness,
        )
        return np.column_stack((x, y, z))

    @staticmethod
    def _extend_like(
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
    def _align_array(array1, array2):
        min_length = min(len(array1), len(array2))
        return array1[:min_length], array2[:min_length], min_length

    def _create_faces(self, min_length):
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
    def _find_trough(mesh):
        z_coords = mesh.points[:, 2]
        return np.min(z_coords)

    @staticmethod
    def _find_crest(mesh):
        z_coords = mesh.points[:, 2]
        return np.max(z_coords)

    def generate_mesh(self):
        groove_spiral = self._generate_groove()
        edge_spiral = self._generate_spiral()
        # Align the spiral arrays
        edge_spiral_aligned, groove_spiral_aligned, min_length = self._align_array(
            edge_spiral, groove_spiral
        )
        vertices = np.vstack((edge_spiral_aligned, groove_spiral_aligned))
        faces = self._create_faces(min_length)
        # Create top surface and extrude it
        top_surface = pv.PolyData(vertices, faces=np.array(faces))
        crest = self._find_crest(top_surface)
        trough = self._find_trough(top_surface)
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
    RPM = 78
    RPS = RPM / 60
    GROOVE_STEP = 0.05
    THICKNESS = 2
    OUTER_RADIUS = 100
    INNER_RADIUS = 3.65
    GROOVE_SPACING = 0.6
    AUDIO_PATH = "sources/final.mp3"
    TARGET_BIT_RATE = "4bit"
    TARGET_SAMPLING_RATE = 550
    GROOVE_BUFFER_COEFFICIENT = 3

    audio_data = AudioHandler(
        audio_path=AUDIO_PATH,
        target_bit_rate=TARGET_BIT_RATE,
        target_sampling_rate=TARGET_SAMPLING_RATE,
    )

    TOTAL_SAMPLES = len(audio_data.displacement_raw)
    TOTAL_ROUNDS = RPS * audio_data.duration
    SAMPLES_PER_ROUND = int(TOTAL_SAMPLES / TOTAL_ROUNDS)
    WAVE_DISPLACEMENT = audio_data.displacement_raw

    mesh_gen = MeshGenerator(
        outer_radius=OUTER_RADIUS,
        inner_radius=INNER_RADIUS,
        groove_spacing=GROOVE_SPACING,
        samples_per_round=SAMPLES_PER_ROUND,
        thickness=THICKNESS,
        groove_buffer_coefficient=GROOVE_BUFFER_COEFFICIENT,
        wave_displacement=WAVE_DISPLACEMENT,
        groove_step=GROOVE_STEP,
    )
    final_mesh = mesh_gen.generate_mesh()
    final_mesh.save("output/record.stl")
    print("Mesh saved to output/record.stl")
