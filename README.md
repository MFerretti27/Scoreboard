# General Infomation
- Python Script to Display your Favorite Teams in Scoreboard Style <br />
- Using FreeSimpleGUI for GUI interface (Free version of PySimpleGUI)
    - [FreeSimpleGUI Documentation](https://docs.pysimplegui.com/en/latest/)<br />
- Uses EPSN API to grab sports data in JSON format (free, no API key required but more subject to change than other API's) <br />

# Change Teams Displayed
- To change the teams that the scoreboard displays change the array names ```teams```, the order of this list is also the order teams are displayed <br />
- Supported sports leagues are NFL (football), MLB (baseball), NHL (hockey), and NBA (basketball). Others leagues such as soccer are possible and should work but are untestested <br /><br />
The team names you want to follow *must match* this order -> [team name, sport league, sport name] <br />
```
teams = [
    ["Detroit Lions", "nfl", "football"],
    ["Detroit Tigers", "mlb", "baseball"],
    ["Pittsburgh Steelers", "nfl", "football"],
    ["Detroit Red Wings", "nhl", "hockey"],
    ["Detroit Pistons", "nba", "basketball"]
]
```
# How to Run
Using Python run the main.py file e.g. ```python main.py```
- This file will create a virutal enviroment and install the all dependancies needed for the scoreboard script to work, all non-generic dependancies are listed below (Others generic ones should already be on your machine)
  - adafruit-circuitpython-requests <br />
  - adafruit-circuitpython-ticks <br />
  - FreeSimpleGUI <br />
  - pillow <br />
  - PySimpleGUI <br />
  - requests <br />
  - setuptools <br />
  - psutil <br />
<br />
- On the first time running the scoreboard.py file will create a sports_logos folder and will fetch all logos for the leagues of the teams you want to be displayed. If you change teams you want to be displayed or change the order of the teams displayed then you will have to delete the sports_logo folder and on the next run it will re-download all the logos <br />

## Requirments
- Python needs to be installed and in your PATH <br />
- pip (usually installed with python) needs to be installed <br />
- All other requirements are in requirements.txt file and will be installed when you run the main.py file <br />

## Hardware Recommended
- Raspberry PI <br />
- 22 inch monitor/screen <br />
  
This should work on any OS but I have only run and tested this on a Raspberry PI 3b, Raspberry PI 5 and Mac OS (So Linux based OS's) <br />
You should be able to use any screen size but it might require you to change the size of displayed elements such as text and image elements (I would reccomend at least a 22 inch screen)<br />

