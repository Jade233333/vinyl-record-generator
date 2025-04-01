# Vinyl Record Generator

The project generates a 3D model of a vinyl record from audio file.

## Usage

### Lean

Clone the project, install requirements and run `programs/generator.py`.

### Verbose

Clone the project, create virtual environment and install dependencies.
> [!NOTE]
> examples below for unix-based system

```shell
git clone https://github.com/Jade233333/vinyl_record_generator.git
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Prepare the audio file. It is recommended to move it under `sources/` folder.

```shell
mv your_audio.mp3 sources/
```

Adjust CONSTANTS inside `/programs/generator.py` to match your need.
Naming of those constants are straightforward, you can figure it out yourself.
For most of them you can stay with the default but do not forget to change `AUDIO_PATH`.

```shell
python programs/generator.py

