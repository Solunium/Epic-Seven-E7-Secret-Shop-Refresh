# Epic Seven Secret Shop Refresh with GUI
## Showcase
gif here
## Getting Started
### Quick Start:
**Step 1.** Download the [latest release](https://github.com/sya1999/Epic-Seven-Secret-Shop-Refresh/releases) make sure to download (**E7 Secret Shop Refresh.zip**)

**Step 2.** Extract the zip file to any directory

**Step 3.** Launch Epic Seven on your emulator

**Step 4.** Launch **E7SecretShopRefresh** in the folder that you just extracted

**Step 5.** Select your emulator from the drop down box	
  - If you can't find it, you need to type in the window name of your emulator and press enter
  - you can see the name of you emulator by hovering over the taskbar icon of your emulator

**Step 6.** (Optional) you can change the setting, refer to [Setting section](https://github.com/sya1999/Epic-Seven-Secret-Shop-Refresh/tree/main#settings)

**Step 7.** Press the "start refresh" button
**- PRESS ESC KEY TO STOP THE PROGRAM**
	
You can check your refreshing history in the folder called **ShopRefreshes**

### Compile it yourself:
**Step 1.** Install python

**Step 2.** Git clone this repository to your directory

**Step 3.** (Optional) Setup and activate a virtual environment with venv or conda

**Step 4.** Install the dependencies
```
pip install -r requirements.txt
```
**Step 5.** Open E7SecretShopRefresh.py or main.ipynb, go to the main function or app config class to make edit

**Step 6.** (Optional) use pyinstaller to create an executable

## Settings:
It can be helpful to select the friendship bookmark to check if the program is detecting items correctly	

Increase mouse speed, if the mouse is moving faster than ui animation

Increase screenshot speed, if you have a longer loading time after each purchase/refresh action

You can stay with the default speed setting in most cases 
(I don't recommend lowering the mouse and screen speed if you don't know what you are doing)

By not setting a skystone budget, the program will run till ESC is pressed
