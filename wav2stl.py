from pydub import AudioSegment
import numpy as np
import sys

np.set_printoptions(threshold=sys.maxsize)
# Load the audio file
audio = AudioSegment.from_file("test1.mp3")
samples = np.array(audio.get_array_of_samples())


# try to reconstruct to 8 bit
samples_8bit = (samples / 2**8).astype(np.int8)
audio_8bit = AudioSegment(samples_8bit.tobytes(),
                          frame_rate=audio.frame_rate,
                          sample_width=1,
                          channels=1
                          )
audio_8bit.export("8bit.wav", format="wav")


# try to reconstruct to 4 bit
samples_4bit = ((samples / 2**12).astype(np.int8) * 2**4).astype(np.int8)
audio_4bit = AudioSegment(samples_4bit.tobytes(),
                          frame_rate=audio.frame_rate,
                          sample_width=1,
                          channels=1
                          )
audio_4bit.export("4bit.wav", format="wav")


# Some tests
print(audio_8bit[:1000].get_array_of_samples())
np.savetxt('test.out', samples_4bit, fmt="%d")
print(audio.sample_width)
print(audio.frame_rate)
print(audio.channels)
