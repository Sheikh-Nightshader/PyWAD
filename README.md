PyWAD a Doom WAD Builder and Extractor


usage/commands

python3 pywad.py extract mywad.wad mywad 
python3 pywad.py build mywad newwad.wad
python3 pywad.py build mywad1 mywad2 mywad1-2.wad

*Extracts wad files into a folder.
*Builds a new wad file from folder.
*Merges multiple wad folders into a megawad.

Commands explained:

Single map wads
python3 pywad.py extract (wadfile) (wadfolder)
python3 pywad.py build (wadfolder) (wadfile)

Multiple map wads
python3 pywad.py build mywadfolder1 mywadfolder2 mywad1-2.wad


This works well for android users using python in Termux making Doom modding easier.
