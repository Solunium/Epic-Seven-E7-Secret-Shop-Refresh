# Epic Seven Secret Shop Refresh with GUI
## Showcase
![](https://github.com/sya1999/Epic-Seven-Secret-Shop-Refresh/blob/main/assets/E7.gif)
## Getting Started
### MOUSE vs ADB
There are two different ways to run auto shop refresh, either through controlling host mouse or send in debug command to emulator

<br>

**Mouse**

Pros:

- Compatible with all emulator

- Fastest way to refresh shop 

Cons:

- Can't use mouse while the application is running

- Emulator needs to stay on screen

- Google Play Beta user might need to change desktop display setting to 1920 x 1080

<br>

**ADB**

Pros:

- Mouse is free to do whatever

- you can minimize the emulator window 

Cons:

- Requires emulator to have ADB 

- Runs 2 times slower than mouse

- need to set ingame resolution to be 1080 x 1920

[Click Here to jump to ADB section](https://github.com/Solunium/Epic-Seven-E7-Secret-Shop-Refresh/blob/main/README.md#quick-start-android-debug-bridge)

<br>
<br>

### Quick Start (Mouse):
**Step 1.** Download the [latest release](https://github.com/sya1999/Epic-Seven-Secret-Shop-Refresh/releases) make sure to download (**E7 Secret Shop Refresh.zip**)

**Step 2.** Extract the zip file to any directory

**Step 3.** Launch Epic Seven on your emulator, make sure to close dispatch mission and news

**Step 4.** Launch **E7SecretShopRefresh** in the folder that you just extracted

**Step 5.** Select your emulator from the drop down box	
  - If you can't find it, you need to type in the window name of your emulator and press enter
  - you can see the name of you emulator by hovering over the taskbar icon of your emulator

**Step 6.** (Optional) you can change the setting, refer to [Setting section](https://github.com/sya1999/Epic-Seven-Secret-Shop-Refresh/tree/main?tab=readme-ov-file#settings)

**Step 6.5:** **EXTRA STEP FOR GOOGLE PLAY BETA USER**

If you are using **GOOGLE PLAY BETA** with DUAL MONITOR, untick auto placement setting and move emulator to secondary monitor

If you are using **GOOGLE PLAY BETA**, make sure **Desktop display resolution setting is 1920 x 1080**, so that it resize properly  

**Step 7.** Press the "start refresh" button

**PRESS ESC KEY TO STOP THE PROGRAM**

**Always make sure that the program recognize the covenant/mystic bookmark before letting it run unsupervised**
	
You can check your refreshing history in the folder called **ShopRefreshHistory**

<br>
<br>

### Quick Start (Android Debug Bridge):
**Step 1.** Download the [latest release](https://github.com/sya1999/Epic-Seven-Secret-Shop-Refresh/releases) make sure to download (**E7 Secret Shop Refresh.zip**)

**Step 2.** Extract the zip file to any directory

**Step 3.** Launch Epic Seven on your emulator, make sure to close dispatch mission and news

**step 4.** Turn on **ADB** (Android Debug bridge) on your emulator

**step 5.** Change ingame resolution to **1080 x 1920**

**step 6.** Launch **E7ADBShopRefresh** in the folder that you just extracted

**step 7.** Follow the instruction show in the command line, and press enter to start

**PRESS ESC KEY TO STOP THE PROGRAM**

**Always make sure that the program recognize the covenant/mystic bookmark before letting it run unsupervised**

**One way to test the program is to manual refresh till covenant/mystic bookmark show up, then run the program to see if it brought the item**

### Compile it yourself:
**Step 1.** Install python

**Step 2.** Git clone this repository to your directory

**Step 3.** (Optional) Setup and activate a virtual environment with venv or conda

**Step 4.** Install the dependencies
```
pip install -r requirements.txt
```
**Step 5.** Open and run E7SecretShopRefresh.py or main.ipynb, go to the main function or app config class to make edit

**Step 6.** (Optional) Use pyinstaller to create an executable
```
pyinstaller -F --hide-console hide-early -i assets/icon.ico E7SecretShopRefresh.py
```
```
pyinstaller -F -i adb-assets/icon.ico E7ADBShopRefresh.py
```
## Settings
It can be helpful to select the friendship bookmark to check if the program is detecting items correctly	

Increase mouse speed, if the mouse is moving faster than ui animation

Increase screenshot speed, if you have a longer loading time after each purchase/refresh action

You can stay with the default speed setting in most cases 
(I don't recommend lowering the mouse and screen speed if you don't know what you are doing)

By not setting a skystone budget, the program will run till ESC is pressed

You can toggle on and off hint which is a live counter of the items purchased

by turning off auto placement, you can move the emulator to another monitor (After turning this off, make sure the entire emulator window stays on-screen)
