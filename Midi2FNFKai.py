import mido
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

# for Drag&Drop
path = ""
if len(sys.argv) > 1:
    path = sys.argv[1]

if path == "":
    path = fileopenbox()

bname = os.path.basename(path)
fileext = os.path.splitext(bname)[1]
filename = os.path.splitext(bname)[0]
songName = filename

print(fileext)

if __name__ == '__main__':
    if ".json" == fileext: # fnfjson 2 midi
        # JSONファイルの読み込みと辞書への変換
        with open(path, "r") as file:
            dat = json.load(file)["song"]
        notes = dat["notes"]
        bpm = notes[0]["bpm"]
        if "bpm" in dat:
            bpm = dat["bpm"]
        print("bpm:", bpm)
        msec_per_beat = 60 / bpm * 1000 
        msec_per_step = 60 / bpm * 1000 / 4
        key_count = 4
        if "keyCount" in dat: # multi
            key_count = dat["keyCount"]

        mid = MidiFile()
        track=[0,0]
        track[0] = mido.MidiTrack()
        track[1] = mido.MidiTrack()
        mid.tracks.append(track[0])
        mid.tracks.append(track[1])
        track[0].append( MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
        track[1].append( MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

        for section in notes:
            mustHit = False
            if "mustHitSection" in section:
                if section["mustHitSection"] == "true" or section["mustHitSection"] == True:
                    mustHit = True

            for sn in section["sectionNotes"]:
                note_time = sn[0]

                # check note channel 
                note_ch = 0
                if sn[1] >= key_count:
                    note_ch = 1
                if mustHit == True: # musthit : reverse channel
                    note_ch = 0 if note_ch == 1 else 1

                # channel to midi_note
                snt = sn[1]
                if snt >= key_count:
                    snt = snt - key_count
                note_note = snt + 60
                if note_ch == 1:
                    note_note = snt + 72
                
                # long note
                note_end = note_time + msec_per_step
                if sn[2] > 0:
                    note_end = note_time + sn[2]
                note_end -= 5

                track[note_ch].append(mido.Message('note_on', note=note_note, time=int(round(note_time*10000,0)))) # for rounding error *10000
                track[note_ch].append(mido.Message('note_off', note=note_note, time=int(round(note_end*10000,0))))

        # sort! midi's tick is "relative" time 
        for ch in range(len(track)):
            track[ch] = sorted(track[ch], key=lambda x: x.time)
            last_time = 0
            #print(track)
            for i in range(len(track[ch])):
                now_time = track[ch][i].time
                track[ch][i].time = now_time - last_time

                track[ch][i].time = int(round(mido.second2tick(track[ch][i].time/1000/10000, mid.ticks_per_beat, mido.bpm2tempo(bpm)),0))
                last_time = now_time

        print(track[0], bpm)
        mid.tracks=[mido.merge_tracks(tracks=track)]
        mid.save(songName+".mid")
        sys.exit()

    # midi 2 fnfjson
    bpm = float(enterbox("BPM of Midi", "Enter BPM", 120))

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
                        print(message, "-> ", noteToUse)
                        if (message.note >= 60 and message.note <= 71):
                            noteToUse = message.note-60
                        elif (message.note >= 72 and message.note <= 83):
                            noteToUse = message.note-72+4   
                        else: 
                            noteToUse = 0 #random.choice([0,1,2,3])
                            
                        print(message, "-> ", noteToUse)

                    aux = [currTime,noteToUse,0] #TODO: long notes
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

    #chartFormat = choicebox('Select the Chart Output Format', 'Format', ('Vanilla FNF', 'Kade Engine'))
    chartFormat = "Kade Engine"

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
