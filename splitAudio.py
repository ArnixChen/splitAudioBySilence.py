#!/usr/bin/python

# From https://stackoverflow.com/questions/29547218/
# remove-silence-at-the-beginning-and-at-the-end-of-wave-files-with-pydub
from pydub import AudioSegment


def detect_audio_begin(sound, offset, silence_threshold=-60.0):
    '''
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    '''
    sound_length = len(sound)
    chunk_size = 10  # ms
    
    audio_begin = offset  # ms
#    print("audio_begin:", end="")
    while sound[audio_begin:audio_begin+chunk_size].dBFS < silence_threshold:
        audio_begin += chunk_size
        if audio_begin >= sound_length:
            return -1
#        print(" %d" % audio_begin)
        #print(".", end="")

    #audio_begin -= chunk_size
#    print(" %d" % audio_begin, end="")

    return audio_begin

def detect_audio_end(sound, offset, silence_threshold=-60.0):
    sound_length = len(sound)
    chunk_size = 10    # ms
    audio_end = offset  # ms
#    print("audio_end:", end="")
    while sound[audio_end:audio_end+chunk_size].dBFS > silence_threshold:
        audio_end += chunk_size
        if audio_end >= sound_length:
            return -1
#        print(".", end="")

    audio_end += chunk_size
#    print(" %d" % audio_end)
    
    return audio_end
    
def split_audio(srcFile):
    import os
    import re
    
    fullPathFileName = srcFile
    print("splitAudio.py "+fullPathFileName)
    fileName = os.path.basename(fullPathFileName)
    dstFileName = fileName + "_out.wav"
    dirName = os.path.dirname(fullPathFileName)

    if len(dirName)==0 :
      dirName = '.'
      dstDirName = "."
    else:
      dstDirName = "out"

    print("\tdirName = "+dirName)
    print("\tdstDirName = "+dstDirName)
    
    sound = AudioSegment.from_file(dirName + "/" + fileName, format="wav")

    print("\tlength = %d ms" % len(sound))
    
    loudness = sound.dBFS
    print("\tloudness = %3.3f db" % loudness);
    if (loudness<-80):
      print("\tAbnormally Exit: Maybe it is a silence file!")
      sound.export(dstDirName + "/" + dstFileName, format="mp3")
      sys.exit()
    
    offset = 0
    end_of_file = False;
    audio_index = 0;
    sound_length = len(sound)
    while not(end_of_file):
      begin = detect_audio_begin(sound, offset)
      if (begin == -1):
        end_of_file = True
        break
        
      end = detect_audio_end(sound, begin)
      #print(f"{begin} -- {end}")
      if (begin == -1 or end == -1):
        end_of_file = True
        print("Touch end of file!")
        break

      while True:
        nextBegin = detect_audio_begin(sound, end)
        if (nextBegin == -1):
            end_of_file = True
            break
        nextEnd = detect_audio_end(sound, nextBegin)
        #print(f"  {nextBegin} -- {nextEnd}")
        if (nextBegin - end) < 400:
          end = nextEnd
          #print("  merged")
        else:
          break

      if (sound[begin:end].dBFS < -60):
        offset = end
        continue

      audio_index += 1
      if (audio_index == 200):
          print("")
      audio = sound[begin:end]
      
      #dstFileName = f"{audio_index:04d}." + str(begin) + ".wav"
      dstFileName = f"{audio_index:04d}.wav"
      print("audio[%d]: %d -- %d  %s" % (audio_index, begin, end, dstFileName))
      audio.export(dstDirName + "/" + dstFileName, format="wav")
      offset = end+1
      
def file_remapping(mapping_list_file):
    import os
    import re
    import glob
    
    audioFileList = glob.glob("./*.wav")
    audioFileList.sort()
    
    wordListFP = open("./" + mapping_list_file, "r")
    wordList = wordListFP.readlines()
    wordListFP.close()
    
    for i in range(0, len(wordList), 1):
        #print("[",i, "]: ", wordList[i], sep="")
        wordList[i] = wordList[i].rstrip()
        #number = int(re.sub("([^ ]*)\t([0-9]{4})", "\\2", wordList[i]))
        word = re.sub("([^ ]*)\t([0-9]{4})", "\\1", wordList[i])
        wordList[i] = "%04d."%(i+1) + word
        os.rename(audioFileList[i], wordList[i] + ".wav")
        print("[",i+1, "]: ", end="")
        print(audioFileList[i] + " => " + wordList[i] + ".wav")


if __name__ == '__main__':
    import sys

    if (len(sys.argv) != 3):
        print("splitAudio.py -- Split audio into segments with mapping list");
        print("syntax: splitAudio.py <mapping list> <audio file.WAV>\n")
    else:
        mapping_list_file = sys.argv[1]
        source_audio = sys.argv[2]
        #split_audio("/home/arnix/works/Language_Test/Python/splitAudio/0a800-1000.WAV")
        split_audio(source_audio)
        file_remapping(mapping_list_file)

