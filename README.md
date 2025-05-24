# General Information
- Python Script to Display your Favorite Major League Sports Teams in Scoreboard Style <br />
- Using FreeSimpleGUI for GUI interface (Free version of PySimpleGUI)
    - [FreeSimpleGUI Documentation](https://docs.pysimplegui.com/en/latest/)<br />
- List of API's used:
    - EPSN API
    - [MLB-StatsAPI](https://github.com/toddrob99/MLB-StatsAPI)
    - [nba_api](https://github.com/swar/nba_api)
    - [nhl-api-py](https://github.com/coreyjs/nhl-api-py)

# Screen Shots
Main menu Screen, used for add team, set display order, and change functionality of scoreboard, and updating code.
<img width="200" alt="Screenshot 2025-05-23 at 9 38 34 PM" src="https://github.com/user-attachments/assets/313e5fda-874a-4881-a75f-0e89b1f6cd25" />
<img width="200" alt="Screenshot 2025-05-23 at 9 38 58 PM" src="https://github.com/user-attachments/assets/875b2eae-882a-46ee-a761-61c07fc6f752" />
<img width="200" alt="Screenshot 2025-05-23 at 9 39 07 PM" src="https://github.com/user-attachments/assets/ace14a8b-e4df-4ca2-a3c0-13b2d4a5a0c0" />


Screens when no teams are currently playing but have games scheduled: <br />
<img width="200" alt="NHL Not Playing" src="https://github.com/user-attachments/assets/3547da83-0236-495d-ae7d-4b494e1c860a" />
<img width="200" alt="NFL Not Playing" src="https://github.com/user-attachments/assets/0a164789-db49-475a-8928-a6b8be7eb3c8" />
<img width="200" alt="Screenshot 2025-05-23 at 7 34 50 PM" src="https://github.com/user-attachments/assets/3e22b6d5-d841-485e-bc24-50bf449109ca" />

Screens when teams are currently playing:<br />
<img width="200" alt="MLB Playing" src="https://github.com/user-attachments/assets/7bf61e47-0e7a-4783-bfcb-59c563b3dc30" />
<img width="200" alt="Screenshot 2025-05-23 at 8 25 22 PM" src="https://github.com/user-attachments/assets/2231d76b-d3ad-4962-896f-30167ba365d5" />

Screen when games are over:<br />
<img width="200" alt="Screenshot 2025-05-21 at 1 46 33 AM" src="https://github.com/user-attachments/assets/1e87ce4c-3169-449c-b937-4e4ca21a63ef" />
<br />

## Controls
Pressing keys on the keyboard while script is runnign will trigger diffrent actions.

Escape - Return to main menu.<br />
Caps Lock - Stay on the current displayed team (only if multiple teams are playing).<br />
Shift - Resume rotating between multiple teams.<br />
Right Arrow - Turn on live data delay, this will put a delay on live data shown. The amount of delay is set in settings.<br />
Left Arrow - Turn off live data delay, this will show live game info as soon as its available.<br />
Up Arrow - Enter "No Spoiler Mode," hiding scores, records, and game details.<br />
Down Arrow - Exit "No Spoiler Mode," showing scores, records, and game details.<br />

## How to Run
Using Python run the main.py file e.g. ```python main.py``` <br />
- This file will create a virtual environment and install the all library dependencies needed for the scoreboard script to work (Other generic libraries should already be on your machine, full list of all libraries listed in Requirements section)<br /><br />
- When starting the main menu will be displayed, this is where you can add teams you want to follow, check for updates of code, change display or of teams, and change overall settings. The settings allow you to change what elements on the socreboard are displayed, what font text is in, how long to display each team for, adding a delay in displaying live data to not be too fast.


## How Data is Collected
-	Primary source: ESPN API.
-	Secondary Source: MLBStats-API (baseball), nba_api (basketball), nhlapi (hockey).
-	If only primary source fails:
    -   Tries backup APIs based on the sport.
-   If only secondary sources fail:
    -   Displays basic info from ESPN.
    -   Some details (last pitch thrown, bonus status, shots on goal, etc) might be missing but most data will still be displayed.
-	If all data fetching fails:
    -	Shows a clock until connection/data is restored.
    -	Logos are gotten when first running for the first time.
    -	If you need to re-download logos such as if a team has updated their logo, you can re-download logos by selecting ""Always Get Logos when Starting" in settings.

## Main Screen
-	The main screen allows you to:
    -	Update scoreboard.
        - Pressing Update bottom will see if there is an update, if there is click it again to update.
    -	Restore to previous version.
        - If update went wrong or critical issues arise in newest version you can restore to a pervious software version you were on before.
    -	Add teams from MLB, NBA, NHL, and NFL to be follow and display.
    -	Set the order of teams to be displayed.
    -	Change what is displayed (should be self-explanatory on settings screen).
    -	Change functionality of scoreboard.
        - You can set a delay for live data so that if watching on TV the scoreboard doesn’t update before TV has.
        - How often each team is displayed on screen for.
        - This can be done individually for when currently playing and when no team is playing
        - How often the scoreboard should update new information.
        - This is only when no team is playing. If a team is playing it will update every few seconds to ensure the most information is captured and displayed. (Set delay if this is too fast and ahead of TV)

## Clock Screen
-	Displays a clock:
    -	If data fetching fails.
    -	If internet connection is lost.
    -	If none of selected teams have data to display.
-	Automatically returns displaying team info:
    -	Once data fetching is successful.
    -	Internet connection is restored.
    -	One of selected teams has data to display.
-	A message on clock screen will appear telling why clock is displaying.

## Requirements
- Python needs to be installed and in your PATH (install [HERE](https://www.python.org/downloads/))<br />
- pip (usually installed with python) needs to be installed <br />
- All other requirments are in requirements.txt file and will be installed when you run the main.py file in virtual environment.
- Full list of all librarys used below:<br />

Unique Libraries Script needs to be installed to work (these will be installed in virtual environment when running main.py):<br />
  - adafruit-circuitpython-ticks -- Used to keep track of when to fetch data and switch displaying teams <br />
  - FreeSimpleGUI -- Used to install Python GUI library  <br />
  - pillow -- Used to resize logo images without losing quality <br />
  - requests -- Used for being able to grab data from ESPN API <br />
  - ruff -- Used for code quality rules for repo <br />
  - MLB-StatsAPI -- Used to get more MLB data and used as a backup if EPSN fetching fails for MLB
  - nba_api -- Used to get more MLB data and used as a backup if EPSN fetching fails for MLB
  - nhl-api-py -- Used to get more MLB data and used as a backup if EPSN fetching fails for MLB
  - rapidfuzz -- Used to find best matches within lists
<br />


Other libraries Used (should already be on system without having to be installed):
  - datetime -- Used to get when game is scheduled/ended
  - subprocess -- Used for attempting to recover internet connection
  - platform -- Used for attempting to recover internet connection by knowing what commands to run based on OS computer is running
  - sys -- Used to determine if you are in virtual environment (ensures script is being run correctly)
  - os -- Used to see if file paths exists
  - time -- Used for sleep functionality
  - venv -- Used for creating virtual environment to install script dependencies and run script
  - gc -- Garbage collection to ensure memory isn’t being eaten up
  - random -- Used for getting random indexs of list to display random logos of your teams
  - shutil -- Used for safely deleting folder for downloading team logos multiple times
  - copy -- Used for copying full dictionaries and their contents for storing infomation to display later
  - traceback -- Used to print full traceback on error for debugging help
  - ast -- Used to assign elements in list a number for setting order
  - io -- Used to display terminal information on gui, this shows whats going on while waiting for logos to be downloaded

## Hardware Recommended
- Raspberry PI (3b+ and up, the better the CPU the less lag displaying images)
    - [Link](https://www.amazon.com/Raspberry-Pi-Quad-core-Cortex-A76-Processor/dp/B0CTQ3BQLS/ref=sxin_16_pa_sp_search_thematic_sspa?content-id=amzn1.sym.76d54fcc-2362-404d-ab9b-b0653e2b2239%3Aamzn1.sym.76d54fcc-2362-404d-ab9b-b0653e2b2239&crid=2W4WOFMA7GQFC&cv_ct_cx=raspberry%2Bpi%2B5&dib=eyJ2IjoiMSJ9.9Y9spcqJNnOBeHLQWNTS41xuiL-91jGxokGdWfYaXkN26OVp-gUsmv2kqlxliXXA.-RF009atOtVOBvjkGi-tAig15vDCYjL13yHoA8iGsX0&dib_tag=se&keywords=raspberry%2Bpi%2B5&pd_rd_i=B0CTQ3BQLS&pd_rd_r=a22d1f2f-599f-4cb8-8e5d-9832619347b6&pd_rd_w=go2DS&pd_rd_wg=aZn7Y&pf_rd_p=76d54fcc-2362-404d-ab9b-b0653e2b2239&pf_rd_r=FEB2SVV839B11Z6QKJBH&qid=1731383117&s=electronics&sbo=RZvfv%2F%2FHxDF%2BO5021pAnSA%3D%3D&sprefix=ras%2Celectronics%2C190&sr=1-1-6024b2a3-78e4-4fed-8fed-e1613be3bcce-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9zZWFyY2hfdGhlbWF0aWM&th=1)<br />
- Monitor (22, 24, inch have been tested, use these for 100% known working without making any changes to code)
    - 22 inch flat monitor [Link](https://www.amazon.com/dp/B0D17P8N28?ref=ppx_yo2ov_dt_b_fed_asin_title)<br />
    - 24 inch asus monitor [Link](https://www.amazon.com/ASUS-VA24DQ-Adaptive-Sync-DisplayPort-Frameless/dp/B08C5MGFXQ/ref=sr_1_3?crid=3S3T4WEGS9F80&dib=eyJ2IjoiMSJ9.rmF77kGZWbFRIylLifYcthss5lyAUm4EJ3MCJ40pqPqk6E_p4qgSiCnLo3AtyHk0jlxasr3d1r7SRelS4QjWUlJ8WoVcpdJ8JIkxzzURDpKruZxWRjl2bgEddP3chNo-kYixRihIxsh7RNkkfIIuqltU9GVN0nA6SqcF4MWjIJIWxBeebZn1awc6QkvL0lgoY7ORZlWmoiBAFy58rvyO2zj6JnsciaG1HeKXFcKam3c.L37ENfD17MKaFgnxtCRUxVbtX79lT4SiDcT7y2hxc2w&dib_tag=se&keywords=asus+monitor&qid=1748050481&sprefix=asus+monitor%2Caps%2C202&sr=8-3&ufe=app_do%3Aamzn1.fos.9fe8cbfa-bf43-43d1-a707-3f4e65a4b666)
    - 15 inch monitor [Link](https://www.amazon.com/Portable-Ultra-Slim-External-Kickstand-Extender/dp/B0D8JXY8V3/ref=sr_1_1_sspa?crid=IXV836AAVTQY&dib=eyJ2IjoiMSJ9.JFwG8BAM9jkKSm3OAh4xtDYnh0VGDF3iuVvD2ln-HAvVOuW69xYNAH5kzbNq8sVzDK1D9IY5ceWZ-C0EX6IEkSRt8KxpAunjMeQ1XkfiD_zJF_Op2FScahvVyb7t43xlh5HS9T_ujfUZL-NmmMDqGHYFOEsPuZlkTO3SXRK3W1-kjzRWKU3O9FPoVypirbHmYjc_UcHbGqa0_bxOFUF_a1SV5TlbSs0jRIMzGs7JeL0.jqQ152DrfcMx0DyA7sv6mx2l9on_qiKtzkIPrQmWwRQ&dib_tag=se&keywords=ailrinni%2Bportable%2Bmonitor%2B-%2B15.6%2Binch%2Bfull%2Bhd%2B1080p%2Bips&qid=1748048739&sprefix=%2Caps%2C188&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1)<br />

- Remote (Helpful when setting everything up on pi, navigating main menu, and controlling scoreboard - see controls section)
  - [Link](https://www.amazon.com/dp/B06XHF7DNQ?ref=ppx_yo2ov_dt_b_fed_asin_title)
    
  
This code has been tested in the following operating systems, Debian (Raspberry Pi), Darwin (Mac) and Windows.<br />
Text and images should auto size based on the monitor size you are using.<br />

## Future Plans
- [ ] Support for college sports
- [ ] Impove main screen layout switching (Less flicker when navigating)
- [ ] Clean up code
