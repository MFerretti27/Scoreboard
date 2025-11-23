# General Information
- Python Script to Display your Favorite Major League Sports Teams in Scoreboard Style <br />
- Using FreeSimpleGUI for GUI interface (Free version of PySimpleGUI)
    - [FreeSimpleGUI Documentation](https://docs.pysimplegui.com/en/latest/)<br />
- List of API's used:
    - ESPN API
    - [MLB-StatsAPI](https://github.com/toddrob99/MLB-StatsAPI)
    - [nba_api](https://github.com/swar/nba_api)
    - [nhl-api-py](https://github.com/coreyjs/nhl-api-py)


# Screen Shots
Main menu Screen, used to add team, set display order, and change functionality of scoreboard, and updating code:<br />
<img width="175" alt="image" src="https://github.com/user-attachments/assets/abb4c1f8-fc19-424f-a004-c1e574debe70" />
<img width="175" alt="image" src="https://github.com/user-attachments/assets/e77fe8b8-caf0-4d1a-86de-6f2760a049b7" />
<img width="175" alt="image" src="https://github.com/user-attachments/assets/942fe12b-e1a5-462c-aaec-c7f815821205" />
<img width="175" alt="image" src="https://github.com/user-attachments/assets/0315fde6-bfb0-4af8-82a7-504c2ef353b8" />


Screens when no teams are currently playing but have games scheduled: <br />
<img width="175" alt="Screenshot 2025-06-19 at 5 05 03 PM" src="https://github.com/user-attachments/assets/752c588a-986f-462b-b354-4b4265d32dbe" />
<img width="175" alt="Screenshot 2025-05-23 at 7 34 50 PM" src="https://github.com/user-attachments/assets/3e22b6d5-d841-485e-bc24-50bf449109ca" />
<img width="175" alt="NHL Not Playing" src="https://github.com/user-attachments/assets/3547da83-0236-495d-ae7d-4b494e1c860a" />
<img width="175" alt="Screenshot 2025-10-01 at 12 18 53 AM" src="https://github.com/user-attachments/assets/0548349b-7130-4587-8612-94843cb76989" />


Screens when teams are currently playing:<br />
<img width="175" alt="Screenshot 2025-07-02 at 6 59 21 PM" src="https://github.com/user-attachments/assets/8499ffd5-83f5-4f6c-873d-b66a66535c60" />
<img width="175" alt="Screenshot 2025-05-23 at 8 25 22 PM" src="https://github.com/user-attachments/assets/2231d76b-d3ad-4962-896f-30167ba365d5" />
<img width="175" alt="Screenshot 2025-11-23 at 2 05 16 PM" src="https://github.com/user-attachments/assets/a60cf163-a549-4b26-82a2-e6ba7cff9751" />


Screen when games are over:<br />
<img width="175" alt="Screenshot 2025-05-21 at 1 46 33 AM" src="https://github.com/user-attachments/assets/1e87ce4c-3169-449c-b937-4e4ca21a63ef" />
<img width="175" alt="Screenshot 2025-06-20 at 12 23 38 AM" src="https://github.com/user-attachments/assets/39377230-fc2a-4db8-9d2f-023490d649fd" />
<img width="175" alt="Screenshot 2025-10-13 at 10 58 59 PM" src="https://github.com/user-attachments/assets/8b3c5720-20e1-4246-8198-5f5d4fe5b36e" />
<img width="175" alt="Screenshot 2025-10-20 at 10 45 35 PM" src="https://github.com/user-attachments/assets/699de253-b7b9-429e-86d0-aa788003bc9f" />


If game is in a playoffs/champianship game a image will apear showing its not the regular seaseon.<br />
Also if a team in the Bonus their score will go orange, in a powerplay it will go blue, or in the redzone it will go read.<br />
For football a the team who has possession of the ball will be underlined.<br />
<img width="175" alt="Screenshot 2025-06-09 at 10 18 15 PM" src="https://github.com/user-attachments/assets/a9e6693d-10ec-4f2c-943c-5fe9dca71752" />
<img width="175" alt="Screenshot 2025-06-22 at 10 44 39 PM" src="https://github.com/user-attachments/assets/9fc4de32-c387-4636-913e-88234e92ab23" />
<img width="175" alt="Screenshot 2025-10-20 at 7 35 43 PM" src="https://github.com/user-attachments/assets/41ed422f-a2d0-4fc4-bc7f-4e8e98a64df0" />



## Controls
Pressing keys on the keyboard while script is running will trigger different actions.

Escape - Return to main menu.<br />
Caps Lock - Stay on the current displayed team (only if multiple teams are playing).<br />
Shift - Resume rotating between multiple teams.<br />
Right Arrow - Turn on live data delay, this will put a delay on live data shown. The amount of delay is set in settings.<br />
Left Arrow - Turn off live data delay, this will show live game info as soon as its available.<br />
Up Arrow - Enter "No Spoiler Mode," hiding scores, records, and game details.<br />
Down Arrow - Exit "No Spoiler Mode," showing scores, records, and game details.<br />



## How to Run
Using Python run the main.py file e.g. ```python main.py``` <br />
- This file will create a virtual environment and install the all library dependencies needed for the scoreboard script to work (Other generic libraries will be installed with python)<br />
- When starting the main menu will be displayed, this is where you can add teams you want to follow, check for updates, change the display order of teams, and change overall settings.<br />
- Press the Start button or "Return/Enter" on the keyboard on main menu screen to start displaying teams selected.<br />
- Press Escape on the keyboard to return to main menu or press escape while at main menu to exit.<br />


## How Data is Collected
- The script uses multiple API's for each sport to increase stability and information avaliable 
-	Primary source: ESPN API.
-	Secondary Source: MLBStats-API (baseball), nba_api (basketball), nhlapi (hockey).
-	It always tries to grab data from ESPN API first and will grab from both API's when a team is currently playing a game
    -	If only primary source fails:
        -   Tries a secondary API based on the sport. All data but Spread/OverUnder will still be displayed so its not very noticable.
        -   A small message will appear in bottom right saying ESPN API failed (Only will be displayed for specfic team that it failed for).
    -   If only secondary sources fail:
        -   Displays basic info from ESPN.
        -   Some details (last pitch thrown, bonus status, shots on goal, play by play, etc) might be missing but most data will still be displayed.
        -   A small message will appear in bottom right saying one of MLB/NBA/NFL/NHL API failed (Only will be displayed for team that it failed for).
    -	If all data fetching fails:
        -	Shows a clock until connection/data is restored.<br /><br />

-	Logos are downloaded when running for the first time.
    -	If you need to re-download logos or resize images such as if a team has updated their logo, you can re-download logos and resize by selecting "Download/Resize Images when Starting" in settings.



## Main Screen
-	The main screen allows you to:
    -	Update scoreboard.
        - Pressing Update bottom will check Github if there is an update, if there is click it again to update.
    -	Restore to previous version.
        - If update went wrong or critical issues arise in newest version you can restore to a previous software version you were on before.
        - Every time you update scoreboard through update button it will save a local copy of older version in the same directory.
    -   Connect to new wifi (if you are on Linux)
    -	Add teams from MLB, NBA, NHL, and NFL to follow and display.
    -	Set the order of teams are displayed in.
    -	Change what is displayed (See Scoreboard screen section below to see what information can be displayed or not displayed on the scoreboard screen).
    -	Change functionality of scoreboard in settings section.
        - You can set a delay for live data so that if watching on TV the scoreboard doesn’t update before TV has.
        - How often each team is displayed on screen for.
            - This can be done individually for when currently playing and when no team is playing.
        - How often the scoreboard should update new information.
            - This is only when no team is playing. If a team is playing it will update every few seconds to ensure the most information is captured and displayed. (Set delay if this is too fast and ahead of TV).
        - How long team information should be displayed once game is over (until new information on upcoming game overwrites it).



## Scoreboard Screen
-   Home team will always display on the right.
-	Scoreboard will prioritize live games currently playing meaning if a game is finished/scheduled for later it won't display until there are no live games for slected teams (Can be changed in settings).
-	Scoreboard will always display team logos, score, game time/game status and teams names.
-	Generic elements below for all teams can be displayed or not displayed based of settings:
    -	Team season record.
    -	Betting Odds MoneyLine/OverUnder/Spread before the game has started.
    -	Venue of where game is being played before the game has started (stadium name).
    -	Date of when game finished.
    -	Series information for sports play a series of games (MLB, NBA, NHL).
    -	A broadcast network logo that game is on, only if its national broadcast not local one.
    -   A image showing that the current game is a playoff/champainship game.
-	Sports specific elements can be displayed or not displayed based off settings:
    -	MLB
          -	Last pitch thrown.
          -	Batter Count.
          -	Image of bases showing what base is occupied.
          -	Hits and errors of each team.
          -	What inning the game is in.
          -	How many outs there are.
          -	Description of last play.
    -	NBA
          -	How many Timeouts each team has.
          -	If a team is in the bonus (If a team is in the bonus their score will go orange).
          -	Game Clock and quarter the game is in.
          -	Shooting stats of each team (3pt/FG made and attempted).
          -	Play by Play of the game.
    -	NHL
          -	The number of shots on goal each team has.
          -	If a team is on a power play (If a team is on a power play their score will go blue).
          -	Game Clock and period the game is in.
          -	Play by Play of the game.
    -	NFL
          -	How many Timeouts each team has.
          -	If a team is in the RedZone (If a team is in the RedZone their score will go red).
          -	What team has possession of the ball (What ever team has possession their score will be underlined).
          -	What down and yardage a team is at on the field.
          -	Game Clock and quarter the game is in.


     
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
- All other requirements are in requirements.txt file and will be installed when you run the main.py file in virtual environment.



## Hardware Recommended
- Raspberry PI (3b+ and up, the better the CPU the less lag displaying images)
    - [Link](https://www.amazon.com/Raspberry-Pi-Quad-core-Cortex-A76-Processor/dp/B0CTQ3BQLS/ref=sxin_16_pa_sp_search_thematic_sspa?content-id=amzn1.sym.76d54fcc-2362-404d-ab9b-b0653e2b2239%3Aamzn1.sym.76d54fcc-2362-404d-ab9b-b0653e2b2239&crid=2W4WOFMA7GQFC&cv_ct_cx=raspberry%2Bpi%2B5&dib=eyJ2IjoiMSJ9.9Y9spcqJNnOBeHLQWNTS41xuiL-91jGxokGdWfYaXkN26OVp-gUsmv2kqlxliXXA.-RF009atOtVOBvjkGi-tAig15vDCYjL13yHoA8iGsX0&dib_tag=se&keywords=raspberry%2Bpi%2B5&pd_rd_i=B0CTQ3BQLS&pd_rd_r=a22d1f2f-599f-4cb8-8e5d-9832619347b6&pd_rd_w=go2DS&pd_rd_wg=aZn7Y&pf_rd_p=76d54fcc-2362-404d-ab9b-b0653e2b2239&pf_rd_r=FEB2SVV839B11Z6QKJBH&qid=1731383117&s=electronics&sbo=RZvfv%2F%2FHxDF%2BO5021pAnSA%3D%3D&sprefix=ras%2Celectronics%2C190&sr=1-1-6024b2a3-78e4-4fed-8fed-e1613be3bcce-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9zZWFyY2hfdGhlbWF0aWM&th=1)<br />
- Monitor (22, 24, inch have been tested, use these for 100% known working without making any changes to code)
    - 22 inch flat monitor [Link](https://www.amazon.com/dp/B0D17P8N28?ref=ppx_yo2ov_dt_b_fed_asin_title)<br />
    - 24 inch Asus monitor [Link](https://www.amazon.com/ASUS-VA24DQ-Adaptive-Sync-DisplayPort-Frameless/dp/B08C5MGFXQ/ref=sr_1_3?crid=3S3T4WEGS9F80&dib=eyJ2IjoiMSJ9.rmF77kGZWbFRIylLifYcthss5lyAUm4EJ3MCJ40pqPqk6E_p4qgSiCnLo3AtyHk0jlxasr3d1r7SRelS4QjWUlJ8WoVcpdJ8JIkxzzURDpKruZxWRjl2bgEddP3chNo-kYixRihIxsh7RNkkfIIuqltU9GVN0nA6SqcF4MWjIJIWxBeebZn1awc6QkvL0lgoY7ORZlWmoiBAFy58rvyO2zj6JnsciaG1HeKXFcKam3c.L37ENfD17MKaFgnxtCRUxVbtX79lT4SiDcT7y2hxc2w&dib_tag=se&keywords=asus+monitor&qid=1748050481&sprefix=asus+monitor%2Caps%2C202&sr=8-3&ufe=app_do%3Aamzn1.fos.9fe8cbfa-bf43-43d1-a707-3f4e65a4b666)
    - 15 inch monitor [Link](https://www.amazon.com/Portable-Ultra-Slim-External-Kickstand-Extender/dp/B0D8JXY8V3/ref=sr_1_1_sspa?crid=IXV836AAVTQY&dib=eyJ2IjoiMSJ9.JFwG8BAM9jkKSm3OAh4xtDYnh0VGDF3iuVvD2ln-HAvVOuW69xYNAH5kzbNq8sVzDK1D9IY5ceWZ-C0EX6IEkSRt8KxpAunjMeQ1XkfiD_zJF_Op2FScahvVyb7t43xlh5HS9T_ujfUZL-NmmMDqGHYFOEsPuZlkTO3SXRK3W1-kjzRWKU3O9FPoVypirbHmYjc_UcHbGqa0_bxOFUF_a1SV5TlbSs0jRIMzGs7JeL0.jqQ152DrfcMx0DyA7sv6mx2l9on_qiKtzkIPrQmWwRQ&dib_tag=se&keywords=ailrinni%2Bportable%2Bmonitor%2B-%2B15.6%2Binch%2Bfull%2Bhd%2B1080p%2Bips&qid=1748048739&sprefix=%2Caps%2C188&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1)<br />

- Remote (Helpful when setting everything up on pi, navigating main menu, and controlling scoreboard - see controls section)
  - [Link](https://www.amazon.com/dp/B06XHF7DNQ?ref=ppx_yo2ov_dt_b_fed_asin_title)
    
  
This code has been tested in the following operating systems, Debian (Raspberry Pi), Darwin (Mac) and Windows.<br />
Text and images should auto size based on the monitor size you are using.<br />


## Future Plans
- [ ] Support for college sports
- [ ] Improve main screen layout switching (Less flicker when navigating)
- [ ] Clean up code
