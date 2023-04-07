# splitAudioBySilence.py
Split audio into wave files based on silence detection.

## Examples of audio spliting
Split an audio file
```bash
# Supports .wav, .flac, .mp3
splitAudioBySilence.py -s source_file.wav
```

...or several audio files
```bash
# Source file name list seperated by space
splitAudioBySilence.py -s source_file1.wav source_file2.wav source_file3.wav
```

Split a WAV file with silence threshold assigned.
```bash
# Assign silence threshold as -40db
splitAudioBySilence.py -t -40 -s source_file.wav
```

Split a WAV file with silence threshold and minimal silence length assigned
```bash
# Assign silence threshold as -40db and minimal silence length as 80ms
splitAudioBySilence.py -t -40 -l 80 -s source_file.wav
```
## Exapmle of renaming splitted files with mapping table
Renaming files splitted from a audio file.
```bash
splitAudioBySilence.py -s source_file.wav -m mapping_table.txt
```

Renaming files splitted from several audio files.
```bash
splitAudioBySilence.py -s source_file1.wav source_file2.wav source_file3.wav -m mapping_table.txt
```
## Priority of parameter source for minimal-silence-length, silence-threshold and noclear-old-files.
audio_file.info > splitAudioBySilence.conf > command line options
