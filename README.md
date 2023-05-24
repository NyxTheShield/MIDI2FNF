# MIDI2FNFKai
Interconvert midi files between Friday Night Funkin' songcharts

## Usage

Drag & Drop MIDI file or the JSON file of Friday Night Funkin' songchart.

MIDI -> JSON
JSON -> MIDI

C#7 : keyswitch for "mustHitSection".
C5-D#5 : LDUR ch.1
C6-D#6 : LDUR ch.1
multi keys support: D#5-B5, D#6-B6. to setup in config.json's "key_count"

By the way, the "mustHitSection" inversion process is done internally, so on the DAW, you should make notes exactly as you see notes in game.
It's more intuitive and the editor in FNF has that specification.

I converted FNF2MIDI2FNF2MIDI twice, but it's the same content, so it should work.








