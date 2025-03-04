from pydub import AudioSegment
import numpy as np


class AudioData:
    def __init__(
        self,
        audio_segment=None,
        samples=None,
        frame_rate=44100,
        sample_width=2,
        channels=1,
    ):
        """
        define audiodata by only audio, only samples or both
        audio is an audiosegment object which can be manipulated by its methods
        sample is a nparray which can be manipulated by algebraic calculation
        """
        if audio_segment and samples is not None:
            self.audio = audio_segment
            self.samples = samples
        elif audio_segment is not None:
            self.audio = audio_segment
            self.samples = np.array(audio_segment.get_array_of_samples())
        elif samples is not None:
            self.samples = samples
            self.audio = AudioSegment(
                samples.tobytes(),
                frame_rate=frame_rate,
                sample_width=sample_width,
                channels=channels,
            )
        else:
            raise ValueError("Either 'audio_segment' or 'samples' must be provided.")

    def save_audio(self, filename):
        self.audio.export(filename, format="wav")
        print(f"audio saved to {filename}")

    def save_samples(self, filename):
        np.savetxt(filename, self.samples, fmt="%d")
        print(f"samples saved to {filename}")

    def to_8bit(self):
        samples_8bit = (self.samples / 2**8).astype(np.int8)
        audio_8bit = AudioSegment(
            samples_8bit.tobytes(),
            frame_rate=self.audio.frame_rate,
            sample_width=1,
            channels=self.audio.channels,
        )
        return AudioData(audio_8bit, samples_8bit)

    def to_4bit(self):
        """
        4bit is not an acceptable audiosegment
        here I double each 4bit sample to make the audio file 8bit
        but actually keep the quality 4bit
        """
        samples_4bit = ((self.samples / 2**12).astype(np.int8) * 2**4).astype(np.int8)
        audio_4bit = AudioSegment(
            samples_4bit.tobytes(),
            frame_rate=self.audio.frame_rate,
            sample_width=1,
            channels=self.audio.channels,
        )
        return AudioData(audio_4bit, samples_4bit)

    def to_raw_4bit(self):
        """
        four bit, but lower volume(without doubling each sample)
        """
        samples_4bit = ((self.samples / 2**12).astype(np.int8)).astype(np.int8)
        audio_4bit = AudioSegment(
            samples_4bit.tobytes(),
            frame_rate=self.audio.frame_rate,
            sample_width=1,
            channels=self.audio.channels,
        )
        return AudioData(audio_4bit, samples_4bit)

    def resample(self, new_sampling_rate):
        resampled_audio = self.audio.set_frame_rate(new_sampling_rate)
        resample_samples = np.array(resampled_audio.get_array_of_samples())
        return AudioData(resampled_audio, resample_samples)


# Load from a file
audio = AudioSegment.from_file("sources/final.mp3")
audio_data = AudioData(audio_segment=audio)

# Save original audio and samples
audio_data.save_audio("output/original.wav")
audio_data.save_samples("output/original.txt")

# 4bit_5500hz
audio_4bit = audio_data.to_raw_4bit()
resampled_audio = audio_4bit.resample(550)
resampled_audio.save_audio("output/4bit_550hz.wav")
resampled_audio.save_samples("output/4bit_550hz.txt")
