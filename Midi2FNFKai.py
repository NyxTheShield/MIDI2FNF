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
CONFIG_FILE = "config.json"
DEFAULT_CONFIG ={
                "section_keyswitch": [{"note": 85, "set_attr": "mustHitSection", "1": True, "0": False }],
                "mustHitSectionNote": 85,
               "chartFormat": "Kade Engine", 
               "midi2fnf key_count": 4} 

def loadconfig():
    try:
        with open(CONFIG_FILE, "r") as f:
            dat = json.load(f)
    except:
        # default config file
        dat = DEFAULT_CONFIG
        with open(CONFIG_FILE, "w") as f:
            f.write(json.dumps(dat, indent=4))
    return dat
CONF = loadconfig()


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

# for Drag&Drop or FileDialog
path = ""
if len(sys.argv) > 1:
    path = sys.argv[1]

if path == "":
    path = fileopenbox()

bname = os.path.basename(path)
fileext = os.path.splitext(bname)[1]
filename = os.path.splitext(bname)[0]
songName = filename

print("processing: ", fileext)

if __name__ == '__main__':
     # fnf 2 midi---------------------------------------
    if ".json" == fileext:
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

        section_step =  240/bpm* 1000
        currTime = 0
        for section in notes:
            mustHit = False
            if "mustHitSection" in section:
                print("mustHitSection", section["mustHitSection"])
                if section["mustHitSection"] == "true" or section["mustHitSection"] == True:
                    mustHit = True
                    track[1].append(mido.Message('note_on', note=CONF["mustHitSectionNote"], time=int(round(currTime*10000,0)))) # for rounding error *10000
                    track[1].append(mido.Message('note_off', note=CONF["mustHitSectionNote"], time=int(round((currTime+section_step-10)*10000,0))))

            currTime += section_step

            for sn in section["sectionNotes"]:
                note_time = sn[0]

                # check note channel 
                note_ch = 0
                if sn[1] >= key_count:
                    note_ch = 1
                if mustHit == True: # musthit 
                    note_ch = 0 if note_ch == 1 else 1 # reverse

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


    # midi 2 fnf------------------------------------------------------------
    bpm = float(enterbox("BPM of Midi", "Enter BPM", 120))
    key_count = CONF["midi2fnf key_count"]

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
    msec_per_beat = 60 / bpm * 1000 
    msec_per_step = 60 / bpm * 1000 / 4
    
    noteState = {}
    def getNoteState(note):
        if str(note) in noteState:
            return noteState[str(note)]
        else:
            noteState[str(note)] = [0,0,0]
            print("error!")
            return noteState[str(note)]

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
                    if (message.channel == 0): #only use channel 0
                        print(message, "-> ", noteToUse)
                        if (message.note >= 60 and message.note <= 71):
                            noteToUse = message.note-60
                        elif (message.note >= 72 and message.note <= 83):
                            noteToUse = message.note-72 + key_count
                        else:
                            # special command
                            noteToUse = message.note 
                                
                    aux = [currTime,noteToUse,0] 
                    #print(aux)
                    nyxTracks[message.channel] += [aux]
                    noteState[str(message.note)] = len(nyxTracks[message.channel])-1
                
                elif (message.type == "note_off"):
                    # long notes detection

                    target_auxid = getNoteState(message.note)
                    lastaux = nyxTracks[message.channel][target_auxid]
                    currTime = globalTime*tick_duration*1000 - 5
                    lastaux[2] = currTime - lastaux[0]
                    if msec_per_step > lastaux[2]:
                        lastaux[2] = 0
                    nyxTracks[message.channel][target_auxid][2] = lastaux[2]
                    del noteState[str(message.note)]

                    print(message, "| long:", msec_per_step, lastaux[2])

        print("totaltime: " + str(totaltime)+"s")


    frames = []
    section_settings = []
    currTime = 240/bpm
    tolerance = (240/bpm)/32;
    while currTime < totaltime:
        #print("FRAME!!" + str(currTime))
        aux = []
        section_special_command = {}
        for i, v in enumerate(CONF["section_keyswitch"]):
            section_special_command[v["set_attr"]] =  v["0"]

        for j in range(2):
            for note in list(nyxTracks[j]):
                roundedNote = round_decimals_up(note[0],3)
                if roundedNote + tolerance < currTime*1000:
                    # check special command
                    special_f = False
                    for i, v in enumerate(CONF["section_keyswitch"]):
                        if note[1] == v["note"]:
                            print(f"FRAME:{str(currTime)} {v['set_attr']} : {v['1']}")
                            special_f = True
                            section_special_command[v["set_attr"]] =  v["1"]
                    if (special_f == False) and (note[1] > key_count*2):
                         print(f"{roundedNote} wrong note:{note[1]}")
                         special_f = True

                    # normal notes
                    if special_f == False:
                        aux+=[ [roundedNote,note[1],note[2]] ]
                    nyxTracks[j].remove(note)
                    
            #for note in list(nyxTracks[1]):
            #    roundedNote = round_decimals_up(note[0],3)
            #    if roundedNote + tolerance < currTime*1000:
            #        aux+=[ [roundedNote ,note[1],note[2]] ]
            #        nyxTracks[1].remove(note)

        frames+=[aux]
        section_settings.append(section_special_command)

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

    def convertMustHit(mustHit, in_notes):
        if mustHit:
            for i, v in enumerate(in_notes):
                if in_notes[i][1] >= key_count:
                    in_notes[i][1] =in_notes[i][1] - key_count
                else:
                    in_notes[i][1] = in_notes[i][1] + key_count
        return in_notes

    chartFormat = CONF["chartFormat"]

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
                auxDicc["sectionNotes"]= convertMustHit(section_settings[i]["mustHitSection"], notes)
                auxDicc["typeOfSection"]=0
                for k, v in section_settings[i].items():
                    auxDicc[k] = v
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
                auxDicc["sectionNotes"]= convertMustHit(section_settings[i]["mustHitSection"], notes)
                auxDicc["altAnim"]=False
                auxDicc["mustHitSection"]=True
                auxDicc["bpm"]=bpm
                for k, v in section_settings[i].items():
                    auxDicc[k] = v

                dicc["song"]["notes"]+=[auxDicc]
        json = json.dumps(dicc)

    out = filesavebox(default=filename+'.json')
    with open(out,"w") as file:
        file.write(json)

sys.exit()
