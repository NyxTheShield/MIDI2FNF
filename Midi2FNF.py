from mido import MidiFile, MetaMessage
import sys
import json
import random
from easygui import *
import os

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
                if message.type == "control_change" or \
                   message.type == "program_change":
                    pass

                elif message.type == "note_on" or message.type == "note_off":
                    if message.note not in notes:
                        notes[message.note] = 0
                    if message.type == "note_on" and message.velocity != 0:
                        notes[message.note] += 1
                        if(notes[message.note] == 1):
                            tracksMerged += \
                                [(totaltime, message.note, message.velocity)]

                    else:
                        notes[message.note] -= 1
                        if(notes[message.note] == 0):
                            tracksMerged += \
                                [(totaltime, message.note, message.velocity)]
                    
                
                globalTime+= message.time
                if (message.type == "note_on"):
                    currTime = globalTime*tick_duration*1000
                    noteToUse = 0
                    if (currTrack == 1):
                        if (message.note < 60 or message.note> 63):
                            noteToUse = random.choice([0,1,2,3])
                        else:
                            noteToUse = message.note-60
                    if (currTrack == 2):
                        if (message.note < 72 or message.note> 75):
                            noteToUse = random.choice([4,5,6,7])
                        else:
                            noteToUse = message.note-72+4     
                    aux = [currTime,noteToUse,0]
                    #print(aux)
                    nyxTracks[currTrack] += [aux]

        #print("totaltime: " + str(totaltime)+"s")

    frames = []
    currTime = 240/bpm
    while currTime < totaltime:
        #print("FRAME!!" + str(currTime))
        aux = []
        for note in list(nyxTracks[1]):
            if note[0]< currTime*1000:
                print("track1")
                print(note)
                aux+=[note]
                nyxTracks[1].remove(note)
        frames+=[aux]

        aux = []
        for note in list(nyxTracks[2]):
            if note[0]< currTime*1000:
                print("track2")
                print(note)
                aux+=[note]
                nyxTracks[2].remove(note)
        frames+=[aux]
        
        currTime += 240/bpm


    dicc = dict()
    dicc["song"] = {}
    dicc["song"]["player1"] = "bf"
    dicc["song"]["player2"] = "dad"
    dicc["song"]["notes"] = []
    dicc["song"]["isHey"] = False
    dicc["song"]["cutsceneType"] = "none"
    dicc["song"]["song"]=songName
    dicc["song"]["isSpooky"]=False
    dicc["song"]["validScore"]=True
    dicc["song"]["speed"]=2
    dicc["song"]["isMoody"]=False
    dicc["song"]["sectionLengths"]=[]
    dicc["song"]["uiType"]="normal"
    dicc["song"]["stage"]="stage"
    dicc["song"]["sections"]=0
    dicc["song"]["needsVoices"]=True
    dicc["song"]["bpm"]=bpm
    dicc["song"]["gf"]="gf"

    for i, notes in enumerate(frames):
        #print("asdf")
        #print(notes)
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
        
