# General Information
- Python Script to Display your Favorite Major League Sports Teams in Scoreboard Style <br />
- Using FreeSimpleGUI for GUI interface (Free version of PySimpleGUI)
    - [FreeSimpleGUI Documentation](https://docs.pysimplegui.com/en/latest/)<br />
- Uses EPSN API to grab sports data in JSON format (free, no API key required but more subject to change than other API's)
    - [List of ESPN API Endpoints](https://gist.github.com/akeaswaran/b48b02f1c94f873c6655e7129910fc3b) <br />

# Screen Shots
When not playing screens will switch between your specified teams every 30 seconds, new data will be fetched from ESPN every 3 minutes <br />
<img width="200" alt="NHL Not Playing" src="https://github.com/user-attachments/assets/3547da83-0236-495d-ae7d-4b494e1c860a" />
<img width="200" alt="NFL Not Playing" src="https://github.com/user-attachments/assets/0a164789-db49-475a-8928-a6b8be7eb3c8" />
<br />
When a team or multiple teams are currently playing the script with prioritize these games and only display them. If multiple games are currently playing at the same time the screen will switch between each team currently playing every 30 seconds and fetch new data from ESPN every 30 seconds.<br />
<img width="200" alt="MLB Playing" src="https://github.com/user-attachments/assets/7bf61e47-0e7a-4783-bfcb-59c563b3dc30" />
<br />

## How to Change Teams Displayed
- To change the teams that the scoreboard displays change the array ```teams``` in constants.py file, the order of this list is also the order teams are displayed <br />
- Supported sports leagues are NFL (Football), MLB (Baseball), NHL (Hockey), NBA (Basketball) EPL (Soccer), and MLS (Soccer).<br /><br />
**<ins>The team names you want to follow must match this order -> [Full team name, sport league, sport name]</ins>** <br /><br />
Example: <br />
```
teams = [
    ["Detroit Lions", "nfl", "football"],
    ["Detroit Tigers", "mlb", "baseball"],
    ["Chicago Fire FC", "usa.1", "soccer"],
    ["Detroit Red Wings", "nhl", "hockey"],
    ["Detroit Pistons", "nba", "basketball"]
]
```
## How to Run
Using Python run the main.py file e.g. ```python main.py``` <br />
- This file will create a virtual environment and install the all library dependencies needed for the scoreboard script to work (Other generic libraries should already be on your machine, full list of all libraries listed in Requirements section)<br /><br />
- On the first time running the scoreboard.py file will create a sports_logos folder and will fetch all logos for the leagues of the teams you want to be displayed which is based of the teams array in constants.py file. **<ins>If you add new sports team with a new league not used before then you will have to delete the sports_logo folder and on the next run it will re-download all the logos for every league in teams array</ins>** <br /><br />
- If the script fails to get data from ESPN API, or none of your specified teams have any data, or if internet connection goes out the script will display a clock. The clock will include the date and the message telling why the clock is being displayed. For example, message could say "No teams have any data" in which none of the specified teams have upcoming games and haven’t had a game in the last 3 days or it could also say "No internet connection" or if any error occurs like being unable to connection to ESPN the message will have the error message. The clock will also randomly select logos of your teams and display them updating every minute. It will display a clock until one of your specified teams have data again or internet connection is restored (script will try getting data and reconnecting to internet every 3 minutes) <br /> <br />
- To quit running pressed escape on the keyboard<br />

## Requirments
- Python needs to be installed and in your PATH (install [HERE](https://www.python.org/downloads/))<br />
- pip (usually installed with python) needs to be installed <br />
- All other environment are in requirements.txt file and will be installed when you run the main.py file, full list below<br />

Unique Libraries Script needs to be installed to work (these will be installed in virtual enviroment when running main.py):<br />
  - adafruit-circuitpython-ticks -- Used to keep track of when to fetch data and switch displaying teams <br />
  - FreeSimpleGUI -- Used to install Python GUI library  <br />
  - pillow -- Used to resize logo images without losing quality <br />
  - requests -- Used for being able to grab data from ESPN API <br />
  - flake8 -- Used for code quality rules for repo <br />
<br />


Other libraries Used:
  - datetime -- Used to display information longer by knowing when game ended and date it ended on (set to always disaply a game information for 3 days after its done unless overwritten by new fresh data)
  - subprocess -- Used for attempting to recover internet connection
  - platform -- Used for attempting to recover internet connection by knowing what commands to run based on OS computer is running
  - sys -- Used to determine if you are in virtual environment (ensures script is being run correctly)
  - os -- Used to see if file paths exists
  - time -- Used for sleep functionality
  - venv -- Used for creating virtual environment to install script dependencies and run script
  - gc -- Garbage collection to ensure memory isn’t being eaten up

## Hardware Recommended
- Raspberry PI (3b+ and up, the better the CPU the less lag displaying images)
    - [Link](https://www.amazon.com/Raspberry-Pi-Quad-core-Cortex-A76-Processor/dp/B0CTQ3BQLS/ref=sxin_16_pa_sp_search_thematic_sspa?content-id=amzn1.sym.76d54fcc-2362-404d-ab9b-b0653e2b2239%3Aamzn1.sym.76d54fcc-2362-404d-ab9b-b0653e2b2239&crid=2W4WOFMA7GQFC&cv_ct_cx=raspberry%2Bpi%2B5&dib=eyJ2IjoiMSJ9.9Y9spcqJNnOBeHLQWNTS41xuiL-91jGxokGdWfYaXkN26OVp-gUsmv2kqlxliXXA.-RF009atOtVOBvjkGi-tAig15vDCYjL13yHoA8iGsX0&dib_tag=se&keywords=raspberry%2Bpi%2B5&pd_rd_i=B0CTQ3BQLS&pd_rd_r=a22d1f2f-599f-4cb8-8e5d-9832619347b6&pd_rd_w=go2DS&pd_rd_wg=aZn7Y&pf_rd_p=76d54fcc-2362-404d-ab9b-b0653e2b2239&pf_rd_r=FEB2SVV839B11Z6QKJBH&qid=1731383117&s=electronics&sbo=RZvfv%2F%2FHxDF%2BO5021pAnSA%3D%3D&sprefix=ras%2Celectronics%2C190&sr=1-1-6024b2a3-78e4-4fed-8fed-e1613be3bcce-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9zZWFyY2hfdGhlbWF0aWM&th=1)<br />
- 22 inch monitor/screen
    - [Link](https://www.amazon.com/dp/B0D17P8N28?ref=ppx_yo2ov_dt_b_fed_asin_title)  (This is what I use as its the best looking one I found, but is a little expensive)<br />
  
This code has been tested in the following operating systems, Debian (Raspberry Pi) and Darwin (Mac) <br />

You can use any screen with any size but it will require you to change the constants.py file to get the correct spacing and text sizes, this is because each screen will have different pixel sizes<br />

## Future Plans
- [ ] Support for college football 
- [ ] Add automatic sizing based on screen size
- [ ] Clean up code
