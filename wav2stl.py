from pydub import AudioSegment
import numpy as np
import sys

np.set_printoptions(threshold=sys.maxsize)

filename = "test3.mp3"
audio = AudioSegment.from_file(filename)
samples = np.array(audio.get_array_of_samples())


def to8bit(samples):
    # try to reconstruct to 8 bit
    samples_8bit = (samples / 2**8).astype(np.int8)
    audio_8bit = AudioSegment(samples_8bit.tobytes(),
                              frame_rate=audio.frame_rate,
                              sample_width=1,
                              channels=audio.channels
                              )
    audio_8bit.export(f"{filename.split(".")[0]}_8bit.wav", format="wav")


def to4bit(samples):
    # try to reconstruct to 4 bit
    samples_4bit = ((samples / 2**12).astype(np.int8) * 2**4).astype(np.int8)
    audio_4bit = AudioSegment(samples_4bit.tobytes(),
                              frame_rate=audio.frame_rate,
                              sample_width=1,
                              channels=audio.channels
                              )
    audio_4bit.export(f"{filename.split(".")[0]}_4bit.wav", format="wav")


# Some tests
# print(audio_8bit[:1000].get_array_of_samples())
# np.savetxt('test.out', samples_4bit, fmt="%d")
print(audio.sample_width)
print(audio.frame_rate)
print(audio.channels)
to4bit(samples)
to8bit(samples)
