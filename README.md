# General Infomation
- Python Script to Display your Favorite Major League Sports Teams in Scoreboard Style <br />
- Using FreeSimpleGUI for GUI interface (Free version of PySimpleGUI)
    - [FreeSimpleGUI Documentation](https://docs.pysimplegui.com/en/latest/)<br />
- Uses EPSN API to grab sports data in JSON format (free, no API key required but more subject to change than other API's) <br />

## Change Teams Displayed
- To change the teams that the scoreboard displays change the array ```teams```, the order of this list is also the order teams are displayed <br />
- Supported sports leagues are NFL (football), MLB (baseball), NHL (hockey), and NBA (basketball). Others leagues such as soccer are possible and should work but are untestested <br /><br />
**<ins>The team names you want to follow must match this order -> [team name, sport league, sport name]</ins>** <br />
```
teams = [
    ["Detroit Lions", "nfl", "football"],
    ["Detroit Tigers", "mlb", "baseball"],
    ["Pittsburgh Steelers", "nfl", "football"],
    ["Detroit Red Wings", "nhl", "hockey"],
    ["Detroit Pistons", "nba", "basketball"]
]
```
## How to Run
Using Python run the main.py file e.g. ```python main.py```
- This file will create a virutal enviroment and install the all dependancies needed for the scoreboard script to work, all non-generic dependancies are listed below (Others generic ones should already be on your machine)
  - adafruit-circuitpython-ticks <br />
  - FreeSimpleGUI <br />
  - pillow <br />
  - PySimpleGUI <br />
  - requests <br />
<br />

- On the first time running the scoreboard.py file will create a sports_logos folder and will fetch all logos for the leagues of the teams you want to be displayed. **<ins>If you change teams you want to be displayed or change the order of the teams displayed then you will have to delete the sports_logo folder and on the next run it will re-download all the logos</ins>** <br /><br />
- If the script fails to get data from ESPN API, or None of your specified teams have any data, or if internet connection goes out the script will disaply a clock. It will display a clock until internet connection is restored (script will handle reconnecting to internet) or if one of your specified teams have data again <br />

## Requirments
- Python needs to be installed and in your PATH <br />
- pip (usually installed with python) needs to be installed <br />
- All other requirements are in requirements.txt file and will be installed when you run the main.py file <br />

## Hardware Recommended
- Raspberry PI
    - [Link](https://www.amazon.com/Raspberry-Pi-Quad-core-Cortex-A76-Processor/dp/B0CTQ3BQLS/ref=sxin_16_pa_sp_search_thematic_sspa?content-id=amzn1.sym.76d54fcc-2362-404d-ab9b-b0653e2b2239%3Aamzn1.sym.76d54fcc-2362-404d-ab9b-b0653e2b2239&crid=2W4WOFMA7GQFC&cv_ct_cx=raspberry%2Bpi%2B5&dib=eyJ2IjoiMSJ9.9Y9spcqJNnOBeHLQWNTS41xuiL-91jGxokGdWfYaXkN26OVp-gUsmv2kqlxliXXA.-RF009atOtVOBvjkGi-tAig15vDCYjL13yHoA8iGsX0&dib_tag=se&keywords=raspberry%2Bpi%2B5&pd_rd_i=B0CTQ3BQLS&pd_rd_r=a22d1f2f-599f-4cb8-8e5d-9832619347b6&pd_rd_w=go2DS&pd_rd_wg=aZn7Y&pf_rd_p=76d54fcc-2362-404d-ab9b-b0653e2b2239&pf_rd_r=FEB2SVV839B11Z6QKJBH&qid=1731383117&s=electronics&sbo=RZvfv%2F%2FHxDF%2BO5021pAnSA%3D%3D&sprefix=ras%2Celectronics%2C190&sr=1-1-6024b2a3-78e4-4fed-8fed-e1613be3bcce-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9zZWFyY2hfdGhlbWF0aWM&th=1)<br />
- 22 inch monitor/screen
    - [Link](https://www.amazon.com/dp/B0D17P8N28?ref=ppx_yo2ov_dt_b_fed_asin_title)  (This is what I use as its the best looking one I found, but is a little expensive)<br />
  
This should has been tested in the following operating systems, Debian (Raspberry Pi) and Darwin (Mac) <br />

You can use any screen with any size but it will require you to change the constants.py file to get the correct spacing and text sizes, this is because each screen will have different pixel sizes<br />

## Future Plans
- [ ] Support for college football 
- [ ] Include more displayed data for MLB
- [ ] Clean up code
