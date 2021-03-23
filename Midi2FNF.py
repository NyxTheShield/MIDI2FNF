from mido import MidiFile, MetaMessage
import sys
import json
import random
from easygui import *
import os
import math
import sys

DEFAULT_TEMPO = 0.5

def ticks2s(ticks, tempo, ticks_per_beat):
    """
        Converts ticks to seconds
    """
    return ticks/ticks_per_beat * tempo


def note2freq(x):
    """
        Convert a MIDI note into a frequency (given in Hz)
    """
    a = 440
    return (a/32) * (2 ** ((x-9)/12))

def round_decimals_up(number:float, decimals:int=2):
    """
    Returns a value rounded up to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.ceil(number)

    factor = 10 ** decimals
    return math.ceil(number * factor) / factor

path = fileopenbox()
filename = os.path.basename(path)
filename = os.path.splitext(filename)[0]
songName = filename

bpm = float(enterbox("BPM of Midi", "Enter BPM", 120))

if __name__ == '__main__':

    nyxTracks = dict()
    for i in range(16):
        nyxTracks[i] = []
    # Import the MIDI file...
    mid = MidiFile(path)

    print("TYPE: " + str(mid.type))
    print("LENGTH: " + str(mid.length))
    print("TICKS PER BEAT: " + str(mid.ticks_per_beat))

    if mid.type == 3:
        print("Unsupported type.")
        exit()

    """
        First read all the notes in the MIDI file
    """
    tracksMerged = []
    notes = {}
    tick_duration = 60/(mid.ticks_per_beat*bpm)
    print("Tick Duration:")
    print(tick_duration)

    print("Tempo:" + str(DEFAULT_TEMPO))
    for i, track in enumerate(mid.tracks):
        currTrack = i
        tempo = DEFAULT_TEMPO
        totaltime = 0
        #print("Track: " + str(i))
        globalTime = 0
        for message in track:
            t = ticks2s(message.time, tempo, mid.ticks_per_beat)
            totaltime += t

            if isinstance(message, MetaMessage):  # Tempo change
                if message.type == "set_tempo":
                    tempo = message.tempo / 10**6
                elif message.type == "end_of_track":
                    pass
                else:
                    print("Unsupported metamessage: " + str(message))

            else:  # Note
                
                globalTime+= message.time
                if (message.type == "note_on"):
                    currTime = globalTime*tick_duration*1000
                    noteToUse = 0
                    if (message.channel == 0):
                        #print(message)
                        if (message.note < 60 or message.note> 63):
                            noteToUse = random.choice([0,1,2,3])
                        else: 
                            noteToUse = message.note-60
                    if (message.channel == 1):
                        #print(message)
                        if (message.note < 72 or message.note> 75):
                            noteToUse = random.choice([4,5,6,7])
                        else:
                            noteToUse = message.note-72+4     
                    aux = [currTime,noteToUse,0]
                    #print(aux)
                    nyxTracks[message.channel] += [aux]

        #print("totaltime: " + str(totaltime)+"s")

    frames = []
    currTime = 240/bpm
    tolerance = (240/bpm)/32;
    while currTime < totaltime:
        #print("FRAME!!" + str(currTime))
        aux = []
        for note in list(nyxTracks[0]):
            roundedNote = round_decimals_up(note[0],3)
            if roundedNote + tolerance < currTime*1000:
                #print("track0")
                #print(note)
                aux+=[ [roundedNote ,note[1],note[2]] ]
                nyxTracks[0].remove(note)
                
        for note in list(nyxTracks[1]):
            roundedNote = round_decimals_up(note[0],3)
            if roundedNote + tolerance < currTime*1000:
                #print("track0")
                #print(note)
                aux+=[ [roundedNote ,note[1],note[2]] ]
                nyxTracks[1].remove(note)

        
        frames+=[aux]

        print("Notes on this frame:")
        for x in aux:
            print(x)
        
        currTime += 240/bpm

    msg = "Enter the Chart Info"
    title = "Chart Info"
    fieldNames = ["Songname","Stage","Player1 Character","Player2 Character"]
    fieldValues = [songName, "stage", "bf", "dad"]  # we start with blanks for the values
    fieldValues = multenterbox(msg,title, fieldNames, fieldValues)

    # make sure that none of the fields was left blank
    while 1:
        if fieldValues == None: break
        errmsg = ""
        for i in range(len(fieldNames)):
          if fieldValues[i].strip() == "":
            errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
        if errmsg == "": break # no problems found
        fieldValues = multenterbox(errmsg, title, fieldNames, fieldValues)

    chartFormat = choicebox('Select the Chart Output Format', 'Format', ('Vanilla FNF', 'Kade Engine'))

    if (chartFormat == "Vanilla FNF"):
        dicc = dict()
        dicc["song"] = {}
        dicc["song"]["song"]= fieldValues[0]
        dicc["song"]["notes"] = []
        dicc["song"]["bpm"]=int(bpm)
        dicc["song"]["sections"]=0
        dicc["song"]["needsVoices"]=True
        dicc["song"]["player1"] = fieldValues[2]
        dicc["song"]["player2"] = fieldValues[3]
        dicc["song"]["sectionLengths"]=[]
        dicc["song"]["speed"]=2
        dicc["song"]["validScore"]=True
        
        #dicc["song"]["stage"]=fieldValues[1]
        dicc["bpm"]=int(bpm)
        dicc["sections"]=len(frames)

        for i, notes in enumerate(frames):
                auxDicc = dict()
                auxDicc["lengthInSteps"]=16
                auxDicc["bpm"]=int(bpm)
                auxDicc["changeBPM"]=False
                auxDicc["mustHitSection"]=True
                auxDicc["sectionNotes"]=notes
                auxDicc["typeOfSection"]=0
                dicc["song"]["notes"]+=[auxDicc]

        dicc["notes"]=dicc["song"]["notes"]
        
        json = json.dumps(dicc)

    else:
        dicc = dict()
        dicc["song"] = {}
        dicc["song"]["player1"] = fieldValues[2]
        dicc["song"]["player2"] = fieldValues[3]
        dicc["song"]["notes"] = []
        dicc["song"]["isHey"] = False
        dicc["song"]["cutsceneType"] = "none"
        dicc["song"]["song"]= fieldValues[0]
        dicc["song"]["isSpooky"]=False
        dicc["song"]["validScore"]=True
        dicc["song"]["speed"]=2
        dicc["song"]["isMoody"]=False
        dicc["song"]["sectionLengths"]=[]
        dicc["song"]["uiType"]="normal"
        dicc["song"]["stage"]=fieldValues[1]
        dicc["song"]["sections"]=0
        dicc["song"]["needsVoices"]=True
        dicc["song"]["bpm"]=bpm
        dicc["song"]["gf"]="gf"

        for i, notes in enumerate(frames):
                auxDicc = dict()
                auxDicc["typeOfSection"]=0
                auxDicc["lengthInSteps"]=16
                auxDicc["sectionNotes"]=notes
                auxDicc["altAnim"]=False
                auxDicc["mustHitSection"]=True
                auxDicc["bpm"]=bpm
                dicc["song"]["notes"]+=[auxDicc]
        json = json.dumps(dicc)

    out = filesavebox(default=filename+'.json')
    with open(out,"w") as file:
        file.write(json)


sys.exit()
