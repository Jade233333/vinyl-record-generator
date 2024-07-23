from pydub import AudioSegment
import numpy as np
import sys

np.set_printoptions(threshold=sys.maxsize)
# Load the audio file
audio = AudioSegment.from_file("test.wav")
samples = np.array(audio.get_array_of_samples())

print(audio[:10].get_array_of_samples())
np.savetxt('test.out', samples)
