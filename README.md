This is the beginning of the DnD project -

Currently it takes the spells.txt which is extracted from the player guide and the all_spells txt which is level and character class based and extracts this and adds to a chromadb
db called - chromadb and a collection called spell_rag_v2

The monsters are also parsed from the monster manual pdf and that is added to the same db but collection monsters
Some extra parsing will need to be done here as it adds non monster text as monsters etc.

The file rag_dialoge_test.py -
is an example of how the dialogue model could be used. Currently it takes an example comment and adds a "fake" EXTENDED PROMPT and send it to an ollama model which can be found here 
https://huggingface.co/Chun121/Qwen3-4B-RPG-Roleplay-V2?not-for-all-audiences=true

once ollama is installed it can be started with 
ollama run hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M

which will download and start the model

The idea is currently to generate some characters - how exactly unclear and to show where the character is - either randomly or from  some adventure and when feedback is obtained from the character to entity recognition the input - lookup for equipment, spells, monsters or whatever and extend the input with rag information obtained from the lookup to create an extended prompt - maybe as well some extra stuff ( no idea) and send that to the dialogue gm generator model...

repeat. 

I have no idea at the moment how we go forwards or if it is needed...
