# TerminalStockSim-1.1.5
Made By Mr.SusBus aka GrandmaVoodo and AI

Stock trader sim for your terminal, with a twist...

The game is all in one file "Stock_Sim.py"

linux Install Guide: Recommended!
1) (Optional) Install system packages you may need
   - Use this CMD "sudo apt update && sudo apt install -y python3 python3-venv python3-pip python3-tk build-essential"
2) Create a managed virtual environment (recommended location: project folder)
   - got to your folder where the game is installed "cd /path/to/your/game"
   - Run this CMD "python3 -m venv .venv"
   - Run this CMD "source .venv/bin/activate"
4) In your VE install all Python dependencies
   - Run this CMD "python -m pip install --upgrade pip && pip install numpy matplotlib cryptography"
5) Run the game.
   - Run this CMD "python Stock_Sim.py"




Old Install - Quick.
Install Guide for Lunix:
1. Make a folder Call it what ever put Stock_Sim.py in that folder.
2. open terminal and run this command:
   - sudo apt update && sudo apt install -y python3 python3-pip && pip install matplotlib numpy cryptography
   - pip install --upgrade matplotlib numpy cryptography
3. Next open the folder you made with the Stock_Sim.py in the terminal.
4. run the game with "python3 Stock_Sim.py"
The save file will be saved in the folder that the Stock_Sim.py is in.ton

Install for windows:
   - install python here: https://www.python.org/downloads/
   - run this cmd in your terminal:
      - python -m pip install cryptography numpy matplotlib colorama
     
Windows file convert: beta STILL NEED TESTING
1. make new folder put bolt convet.py and Stock_Sim.py inside
2. run "python3 convert.py"
3. it will make a new windows verison that will work on windows.
4. you may need to remove these lines at 3030: Change it to this
-"            if msvcrt.kbhit():"
-"                key = msvcrt.getch()"
 -"               if key in (b'\r', b'\n'):"
  -"                  break"

