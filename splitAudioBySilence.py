#!/usr/bin/python

from pydub import AudioSegment
from pydub.silence import detect_nonsilent
#from pydub.playback import play
import soundfile as sf
import argparse
import sys
import os
import glob
import re

def get_basename_without_extension(file_path):
  '''
  Get file's basename without its extension.
  ex.
    result = get_basename_without_extension('/home/test/bin/test.py')
    print(result)
    Out[]: test
  '''
  return os.path.splitext(os.path.basename(file_path))[0]
  
def is_type(variable, atype):
  '''
  Check if a variable is type of atype
  '''
  if str(type(variable)) == f"<class '{atype}'>":
    return True
  else:
    return False

def get_info(filename, search_key=None):
  '''
  Get begin,end information of a splitted audio segment
  '''
  filename = os.path.basename(filename)
  if filename == get_basename_without_extension(__file__) + '.conf':
    info_filename = filename
  else:
    info_filename = filename + '.info'

  if not os.path.exists(info_filename):
#    print(f"    {info_filename} does not exist!")
    return None

  info_dict = {}
  with open(info_filename, 'r') as info_fileobj:
    for line in info_fileobj:
      line = line.rstrip()
#     print(f"{line}")
      if '=' not in line:
        continue

      key, value = line.split('=', 1)
      value = int(value) if (value.isdigit() or value[1:].isdigit()) else (True if value == 'True' else False)

      if search_key != None and key == search_key:
        return value
      else:
        info_dict[key] = value
  return info_dict

def save_config(filename, minimal_silence_length, silence_threshold, noclear_old_files=False):
  """
  Save command line options into configuration file.
  """
  with open(filename, 'w') as f:
    f.write(f"minimal_silence_length={minimal_silence_length}\n")
    f.write(f"silence_threshold={silence_threshold}\n")
    f.write(f"noclear_old_files={'True' if noclear_old_files else 'False'}\n")

def get_audio_data(audio_path):
  """
  Retrive audio data from file. It supports WAV, FLAC, MP3 format only.
  """
  try:
    audio_info = sf.info(audio_path)
  except FileNotFoundError:
    print(f"File {file_path} does not exists!")
    return None

  if audio_info.format == 'WAV':
    audio_format = 'wav'
  elif audio_info.format == 'FLAC':
    audio_format = 'flac'
  elif audio_info.format == 'MP3':
    audio_format = 'mp3'
  else:
    print(f"{audio_path} has unsupported format")
    return None

  return AudioSegment.from_file(audio_path, audio_format)

def clear_old_generated_files(src_basename):
  '''
  Remove wave files that are splitted from srcFile.
  '''
  print(f"  Remove old gernated wave files splitted from {src_basename}.wav")
  old_wave_list = glob.glob(f"{src_basename}.[0-9][0-9][0-9][0-9]*.wav")
  old_wave_list.sort()

  for item in old_wave_list:
    item_basename = get_basename_without_extension(item)

    if len(item_basename) > len(src_basename):
      src_length = len(src_basename)
      if item_basename[:src_length] == src_basename:
        if os.path.exists(item):
          os.remove(item)
          print(f"    Remove old {item_basename}.wav !", end='')
    print()

def split_audio(file_path, minimal_silence_length, silence_threshold, noclear_old_files=False):
  '''
  Split audio based on silence detection.
  '''
  try:
    audio_data = get_audio_data(file_path)
  except FileNotFoundError:
    print(f"File {file_path} does not exists!")
    exit(-1)
  print(f"Got audio_data of {file_path}")
  
  if not is_type(minimal_silence_length, 'int'):
    print(f"minimal_silence_length is not an integer")
    exit(-1)
    
  if not is_type(silence_threshold, 'int'):
    print(f"silence_threshold is not an integer")
    exit(-1)
    
  if not is_type(noclear_old_files, 'bool'):
    print(f"noclear_old_files is not an boolean")
    exit(-1)

  src_basename = get_basename_without_extension(file_path)

  if noclear_old_files == False:
    clear_old_generated_files(src_basename)

  parts = detect_nonsilent(audio_data, min_silence_len=minimal_silence_length, silence_thresh=silence_threshold)

  info_filename = src_basename  + '.wav.info'
  info_fileobj = open(info_filename, 'w')
  msg = f"minimal_silence_length={str(minimal_silence_length)}\n"
  info_fileobj.write(msg)
  msg = f"silence_threshold={str(silence_threshold)}\n"
  info_fileobj.write(msg)
  msg = f"noclear_old_files={'True' if noclear_old_files == True else 'False' }\n"
  info_fileobj.write(msg)

  is_joined_file = re.findall(r'\d{4}-\d{4}\.joined', src_basename)
  #print(f"is_joined_file={is_joined_file}")
  if is_joined_file != None and len(is_joined_file) == 1:
    result = re.findall(r'\d{4}', is_joined_file[0])
    #print(f"result={result}")
    begin_number = int(result[0])
    end_number = int(result[1])
    prefix = re.sub("\.\d{4}-\d{4}\.joined", "", src_basename)
    #print(f"prefix={prefix} src_basename={src_basename}")

  for i, part in enumerate(parts):
    begin, end = part

    if is_joined_file != None and len(is_joined_file) == 1:
      i = i + begin_number - 1
      formatted_number = str(i+1).zfill(4)
      out_filename = f"{prefix}.{formatted_number}.wav"
    else:
      formatted_number = str(i+1).zfill(4)
      out_filename = f"{src_basename}.{formatted_number}.wav"

    #print(f"{i} Non-silent segment from {begin} to {end}")
    print(f"Exporting {out_filename}:{begin}-{end}:{end-begin}")
    audio_data[begin: end].export(out_filename, format="wav")
    msg = f"{out_filename},{begin},{end},{end-begin}\n"
    info_fileobj.write(msg)
  info_fileobj.close()
  
def mapping_generated_files(source_list, mapping_table):
  '''
  Rename generated files with mapping_table.
  '''
  with open(mapping_table, 'r') as f:
    mapping_list = [line.strip() for line in f.readlines()]
  
  # Remove empty line
  for i, line in enumerate(mapping_list):
    if len(line) == 0:
      mapping_list.pop(i)
  
  i=0 # Index for renamed files
  for src_filename in source_list:
    src_basename = get_basename_without_extension(src_filename)
    if not os.path.exists(src_basename + ".wav"):
      continue
    generated_files = glob.glob(f"{src_basename}.[0-9][0-9][0-9][0-9].wav")
    if len(generated_files) == 0:
      print(f"No file generated from {src_basename}.wav was found !")
      return
    
    joined_files = glob.glob(f"{src_basename}.[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9].joined*.wav")
    if len(joined_files) != 0:
      generated_files.extend(joined_files)
    generated_files.sort()
    
    # Retrive new filenames from mapping_list and reverse it for list poping.
    subset = mapping_list[:len(generated_files)][::-1]
    del mapping_list[:len(generated_files)]
    print(f"subset={subset[::-1]}")
    
    for gen_file in generated_files:
      try:
        i = i + 1
        new_name = str(i).zfill(4) + '.' + subset.pop() + '.wav'
        print(f"Rename {gen_file} to {new_name} !")
        os.rename(gen_file, new_name)
      except IndexError:

        return

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Split audio into wave files based on silence detection')
  split_group = parser.add_argument_group('Split options', 'Options for audio spliting')
  split_group.add_argument('-s', '--source_list', nargs='+', required=False, help='the source audio files to split')
  split_group.add_argument('-t', '--threshold', type=int, default=-40, help='the volume threshold in dB below which audio is considered silent')
  split_group.add_argument('-l', '--length', type=int, default=80, help='the minimum length of silence in milliseconds to trigger a split')
  split_group.add_argument('-n', '--noclear', action='store_true', default=False, help='do not clear old generated files before spliting audios')
  mapping_group = parser.add_argument_group('Renaming options', 'Options for generated files renaming')
  mapping_group.add_argument('-m', '--mapping_table', type=str, required=False, help='A text file which contains the mapping name line by line for generated file renaming')  

  args = parser.parse_args()

  if len(sys.argv) == 1:
    parser.print_help()
    exit()

  #print(f"clear = {clear}")
  config_file = get_basename_without_extension(__file__) + '.conf'
  config = {}
  if os.path.exists(config_file):
    config['minimal_silence_length'] = get_info(config_file, 'minimal_silence_length')
    config['silence_threshold'] = get_info(config_file, 'silence_threshold')
    config['noclear_old_files'] = get_info(config_file, 'noclear_old_files')
    print(f"config={config}")
    
  if args.mapping_table != None:
    if not os.path.exists(args.mapping_table):
      print(f"Mapping table '{args.mapping_table}' does not exist!")
      exit(-1)
    mapping_generated_files(args.source_list, args.mapping_table)
    exit()

  for file_path in args.source_list:
    if not os.path.exists(file_path):
      print(f"File '{file_path}' does not exist!")
      exit(-1)
    else:
      if get_info(file_path, 'minimal_silence_length') != None:
        length = get_info(file_path, 'minimal_silence_length')
      else:
        if len(config) != 0:
          length = config['minimal_silence_length']
        else:
          length = args.length

      if get_info(file_path, 'silence_threshold') != None:
        threshold = get_info(file_path, 'silence_threshold')
      else:
        if len(config) != 0:
          threshold = config['silence_threshold']
        else:
          threshold = args.threshold

      if get_info(file_path, 'noclear_old_files') != None:
        noclear = get_info(file_path, 'noclear_old_files')
      else:
        if len(config) != 0:
          noclear = config['noclear_old_files']
        else:
          noclear = args.noclear

      if not os.path.exists(config_file):
        save_config(config_file, length, threshold, noclear)
        
      print(f"minimal_silence_length={length} silence_threshold={threshold} noclear={noclear}")
      split_audio(file_path, length, threshold, noclear)
    
