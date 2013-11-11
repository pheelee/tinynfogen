tinynfogen
==========


usage: TinyNFOGen.py [-h] --src ROOTFOLDER [--dst DESTFOLDER] [-f] [-o]
                     [-updateXBMC] [-v] [-n GLOBALNFONAME] [-l LANGUAGE]

Generate NFO Files

optional arguments:
  -h, --help        show this help message and exit
  --src ROOTFOLDER  The root folder where the movies are
  --dst DESTFOLDER  The folder where the movies should be put to after
                    processing
  -f                Forces Folder and File renaming for all items
  -o                Forces overwriting of existing movies in destination
  -updateXBMC       Forces update of XBMC Library (regardless of config
                    setting)
  -v                Script Output is more verbose
  -n GLOBALNFONAME  Specify a global name for the nfo file
  -l LANGUAGE       Language of Movie Infos in ISO 639-1 code
                    Default:German(de)
