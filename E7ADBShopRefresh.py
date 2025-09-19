import subprocess
import os
import sys
from io import BytesIO
import time
import csv

from PIL import Image
import threading
import cv2
import numpy as np
import keyboard
import random
import configparser

class E7Item:
    def __init__(self, image=None, price=0, count=0):
        self.image=image
        self.price=price
        self.count=count

    def __repr__(self):
        return f'ShopItem(image={self.image}, price={self.price}, count={self.count})'

class E7Inventory:
    def __init__(self):
        self.inventory = dict()

    def addItem(self, path:str, name='', price=0, count=0):
        image = cv2.imread(os.path.join('adb-assets', path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        newItem = E7Item(image, price, count)
        self.inventory[name] = newItem

    def getStatusString(self):
        status_string = ''
        for key, value in self.inventory.items():
            status_string += key[0:4] + ': ' + str(value.count) + ' '
        return status_string

    def getName(self):
        res = []
        for key in self.inventory.keys():
            res.append(key)
        return res
    
    def getCount(self):
        res = []
        for value in self.inventory.values():
            res.append(value.count)
        return res
    
    def getTotalCost(self):
        sum = 0
        for value in self.inventory.values():
            sum += value.price * value.count
        return sum

    def writeToCSV(self, duration, skystone_spent):
        duration = round(duration, 2)

        res_folder = 'ShopRefreshHistory'
        if not os.path.exists(res_folder):
            os.makedirs(res_folder)

        history_file = 'ADB_History.csv'

        path = os.path.join(res_folder, history_file)
        if not os.path.isfile(path):
            with open(path, 'w', newline='') as file:
                writer = csv.writer(file)
                column_name = ['Duration', 'Skystone spent', 'Gold spent']
                column_name.extend(self.getName())
                writer.writerow(column_name)
        with open(path, 'a', newline='') as file:
            writer = csv.writer(file)
            data = [duration, skystone_spent, self.getTotalCost()]
            data.extend(self.getCount())
            writer.writerow(data)

class E7ADBShopRefresh:
    def __init__(self, tap_sleep:float = 0.3, budget=None, ip_port=None, stop_refresh_key='esc', random_offset = False, debug=False):
        self.loop_active = False
        self.end_of_refresh = True
        self.tap_sleep = tap_sleep
        self.budget = budget
        self.ip_port = ip_port
        self.stop_refresh_key = stop_refresh_key

        #random offset
        self.random_offset = random_offset
        self.x_offset = 75 if random_offset else 0
        self.y_offset = 25 if random_offset else 0

        self.debug = debug
        self.device_args = [] if ip_port is None else ['-s', ip_port]
        self.refresh_count = 0
        self.keyboard_thread = threading.Thread(target=self.checkKeyPress)
        self.adb_path = os.path.join('adb-assets','platform-tools', 'adb')
        self.storage = E7Inventory()
        self.screenwidth = 1920
        self.screenheight = 1080
        self.updateScreenDimension()

        self.storage.addItem('cov.jpg', 'Covenant bookmark', 184000)
        self.storage.addItem('mys.jpg', 'Mystic medal', 280000)
        if self.debug:
            self.storage.addItem('fb.jpg', 'Friendship bookmark', 18000)

    def start(self):
        self.loop_active = True
        self.end_of_refresh = False
        self.keyboard_thread.start()
        self.refreshShop()

    #threads
    def checkKeyPress(self):
        while(self.loop_active and not self.end_of_refresh):
            self.loop_active = not keyboard.is_pressed(self.stop_refresh_key)
        self.loop_active = False
        print('Shop refresh terminated!')

    def refreshShop(self):
        self.clickShop()
        #time needed for item to drop in after refresh (0.5 second loading + drop 1 second)
        sliding_time = 1.5
        #stat track
        start_time = time.time()
        milestone = self.budget//10
        #swipe location
        x1 = 0.6250 * self.screenwidth
        y1 = 0.7481 * self.screenheight
        y2 = 0.3629 * self.screenheight
        #refresh loop
        while self.loop_active:

            time.sleep(sliding_time)
            brought = set()

            if not self.loop_active: break
            #look at shop (page 1)
            screenshot = self.takeScreenshot()
            #print(len(self.storage.inventory.items()))
            for key, value in self.storage.inventory.items():
                pos = self.findItemPosition(screenshot, value.image)
                if pos is not None:
                    self.clickBuy(pos)
                    value.count += 1
                    brought.add(key)

            if not self.loop_active: break
            
            #swipe
            #debug
            if self.debug:
                self.showOffsetArea(x1, y1, "Please check if red rectangle is in a scrollable area", "start scroll area")    

            xoff, yoff = self.generateOffset()
            adb_process = subprocess.run([self.adb_path] + self.device_args + ['shell', 'input', 'swipe', str(x1+xoff), str(y1+yoff), str(x1+xoff), str(y2+yoff)])
            #wait for action to complete
            time.sleep(1)

            if not self.loop_active: break
            #look at shop (page 2)
            screenshot = self.takeScreenshot()
            for key, value in self.storage.inventory.items():
                pos = self.findItemPosition(screenshot, value.image)
                if pos is not None and key not in brought:
                    self.clickBuy(pos)
                    value.count += 1

            #print every 10% progress
            if self.budget >= 30 and self.refresh_count*3 >= milestone and not self.debug:
                sys.stdout.write(' ' * 80 + '\r')
                sys.stdout.write(f'{int(milestone/self.budget*100)}% {self.storage.getStatusString()}\r')
                sys.stdout.flush()
                milestone += self.budget//10
            
            if not self.loop_active: break
            if self.budget:
                if self.refresh_count >= self.budget//3:
                    break

            self.clickRefresh()
            self.refresh_count += 1
        
        self.end_of_refresh = True
        self.loop_active = False
        if self.refresh_count*3 != self.budget: print('100%') 
        duration = time.time()-start_time
        self.storage.writeToCSV(duration=duration, skystone_spent=self.refresh_count*3)
        self.printResult()
    
    #helper function
    def printResult(self):
        print('\n---Result---')
        for key, value in self.storage.inventory.items():
            print(key, ':', value.count)
        print('Skystone spent:', self.refresh_count*3)

    def updateScreenDimension(self):
        adb_process = subprocess.run([self.adb_path] + self.device_args + ['exec-out', 'screencap','-p'], stdout=subprocess.PIPE)
        byte_image = BytesIO(adb_process.stdout)
        pil_image = Image.open(byte_image)
        pil_image = np.array(pil_image)
        y, x, _ = pil_image.shape
        self.screenwidth = x
        self.screenheight = y


    def takeScreenshot(self):
        adb_process = subprocess.run([self.adb_path] + self.device_args + ['exec-out', 'screencap','-p'], stdout=subprocess.PIPE)
        img_array = np.frombuffer(adb_process.stdout, dtype=np.uint8)
        screenshot = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
        # ims = cv2.resize(screenshot, (960, 540))
        # cv2.imshow('image window', ims)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        return screenshot
    
    def showOffsetArea(self, x, y, imshow_title = "Debug", text_desc = ''):

        #Grab a color image
        adb_process = subprocess.run([self.adb_path] + self.device_args + ['exec-out', 'screencap','-p'], stdout=subprocess.PIPE)
        img_array = np.frombuffer(adb_process.stdout, dtype=np.uint8)
        ims = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        cv2.rectangle(ims, (int(x-self.x_offset), int(y-self.y_offset)), (int(x+self.x_offset), int(y+self.y_offset)), (0, 0, 255), 2)
        
        # show text tip
        if text_desc:
            (text_width, text_height), baseline = cv2.getTextSize(text_desc, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
            text_x = int(x-self.x_offset + ((x+self.x_offset) - (x-self.x_offset) -  text_width)/2)
            text_y = int(y+self.y_offset + text_height + baseline)

            text_props = {
                'text': text_desc,
                'org': (text_x, text_y),
                'fontFace': cv2.FONT_HERSHEY_SIMPLEX,
                'fontScale': 1,
                'color': (0, 0, 255),
                'thickness': 2,
            }

            #border  
            text_border = {
                'text': text_desc,
                'org': (text_x, text_y),
                'fontFace': cv2.FONT_HERSHEY_SIMPLEX,
                'fontScale': 1,
                'color': (0, 0, 0),
                'thickness': 6,
            }
            ims = cv2.putText(ims, **text_border)
            ims = cv2.putText(ims, **text_props)
        
        ims = cv2.resize(ims, (960, 540))
        cv2.imshow(imshow_title + f' - press {self.stop_refresh_key} to stop debug', ims)
        print('check image - find it in taskbar')
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def generateOffset(self):
        if self.random_offset:
            generate_x_offset = random.randint(-self.x_offset, self.x_offset)
            generate_y_offset = random.randint(-self.y_offset, self.y_offset)
            return (generate_x_offset, generate_y_offset)
        return (0, 0)

    def findItemPosition(self, screen_image, item_image):
        result = cv2.matchTemplate(screen_image, item_image, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= 0.75)
        
        #find location of item
        if loc[0].size > 0:
            x = loc[1][0] + self.screenwidth * 0.4718
            y = loc[0][0] + self.screenheight * 0.1000
            pos = (x, y)
            return pos
        return None

    #macro
    def clickShop(self):
        #newshop
        x = self.screenwidth * 0.0411
        y = self.screenheight * 0.3835
        adb_process = subprocess.run([self.adb_path] + self.device_args + ['shell', 'input', 'tap', str(x), str(y)])
        time.sleep(0.5)

        #oldshop
        x = self.screenwidth * 0.4406
        y = self.screenheight * 0.2462
        adb_process = subprocess.run([self.adb_path] + self.device_args + ['shell', 'input', 'tap', str(x), str(y)])
        time.sleep(0.5)

        #newshop
        x = self.screenwidth * 0.0411
        y = self.screenheight * 0.3835
        adb_process = subprocess.run([self.adb_path] + self.device_args + ['shell', 'input', 'tap', str(x), str(y)])
        time.sleep(0.5)

    def clickBuy(self, pos):
        if pos is None:
            return False
        
        x, y = pos
        xoff, yoff = self.generateOffset() 

        #debug
        if self.debug: self.showOffsetArea(x, y, "Please check if red rectangle is within buy button's border", "click buy area")

        adb_process = subprocess.run([self.adb_path] + self.device_args + ['shell', 'input', 'tap', str(x+xoff), str(y+yoff)])
        time.sleep(self.tap_sleep)

        #confirm
        x = self.screenwidth * 0.5677
        y = self.screenheight * 0.7037
        xoff, yoff = self.generateOffset() 

        #debug
        if self.debug: self.showOffsetArea(x, y, "Please check if red rectangle is within buy button's border", "click buy area")

        adb_process = subprocess.run([self.adb_path] + self.device_args + ['shell', 'input', 'tap', str(x+xoff), str(y+yoff)])
        time.sleep(self.tap_sleep)
        #loading sleep
        time.sleep(1)
    
    def clickRefresh(self):
        x = self.screenwidth * 0.1698
        y = self.screenheight * 0.9138
        xoff, yoff = self.generateOffset()
        
        #debug
        if self.debug: self.showOffsetArea(x, y, "Please check if red rectangle is within refresh button's border", 'click refresh area')

        adb_process = subprocess.run([self.adb_path] + self.device_args + ['shell', 'input', 'tap', str(x+xoff), str(y+yoff)])
        time.sleep(self.tap_sleep)

        if not self.loop_active: return
        #confirm
        x = self.screenwidth * 0.5828
        y = self.screenheight * 0.6411
        xoff, yoff = self.generateOffset()
        
        #debug
        if self.debug: self.showOffsetArea(x, y, "Please check if red rectangle is within buy confirm's border", 'click confirm area')
        
        adb_process = subprocess.run([self.adb_path] + self.device_args + ['shell', 'input', 'tap', str(x+xoff), str(y+yoff)])
        time.sleep(self.tap_sleep)

def getDevices(print_output):
        check_devices = subprocess.run([adb_path, 'devices'], capture_output=True, text=True)
        if print_output: print(check_devices.stdout)
        lines = check_devices.stdout.splitlines()
        devices = []
        for line in lines[1:-1]:
            seq = line.split('\t')
            devices.append(seq[0])
        return devices

CONFIG_FILE = "ADBconfig.ini"

def saveConfigFile(tap_sleep, budget, stop_refresh_key, random_offset):
    config = configparser.ConfigParser()
    config["Settings"] = {
        "tap_sleep": str(tap_sleep),
        "budget": str(budget),
        "stop_refresh_key": str(stop_refresh_key),
        "random_offset": str(random_offset)
    }
    with open(CONFIG_FILE, "w") as f:
        config.write(f)
    print('Setting saved')

if __name__ == '__main__':

    #intro
    print('Epic Seven Shop Refresh with ADB')
    print('Before launching this application')
    print('Make sure Epic Seven is opened and that ADB is turned on')
    print('Ingame resolution should be set to 1920 x 1080')
    print('(relaunch this application if the above conditions are not met)')
    print()
    print('It is normal for adb to take a few second to respond')
    input('when you finish reading, press enter to continue!')

    print()

    if not os.path.isdir(os.path.join('adb-assets')):
        print('adb-assets folder is missing!')
        input('Press enter to exit ...')
        sys.exit(0)

    ip_port = None
    adb_path = os.path.join('adb-assets', 'platform-tools', 'adb')
    #use below to test ip port on google beta developer
    #subprocess.run([adb_path, 'kill-server'])
    devices = getDevices(False)

    while(len(devices) == 0 or len(devices) > 1):
        
        print('ADB Setup')
        devices = getDevices(True)
        print('Type the ip and port of the device that you want to select or add')
        print('By leaving it blank it wil default to 127.0.0.1:5555')
        user_choice = input('Device: ') or 'localhost:5555'
        if user_choice in devices:
            ip_port = user_choice
        else:
            test_connection = subprocess.run([adb_path, 'connect', user_choice], capture_output=True, text=True)
            print(test_connection.stdout)
            test_res = test_connection.stdout.split(' ')
            if test_res[0] == 'connected' and test_res[1] == 'to':
                ip_port = user_choice
                break
            else:
                print('Fail to connect, try again')
    
    if os.path.exists(CONFIG_FILE):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        print("Last Saved Setting:")
        for section in config.sections():
            for key, value in config[section].items():
                print(f'{key} = {value}')
        print()
        print('Use last saved setting?')
        if input('leave blank for yes, or type (yes/no): ') == 'no':
            print()
            print('Update setting')
            print()
        else:
            #print statistic
            if config.getfloat("Settings", "budget") >= 1000:
                ev_cost = 1691.04536 * config.getfloat("Settings", "budget") * 2
                ev_cov = 0.006602509 * config.getfloat("Settings", "budget") * 2
                ev_mys = 0.001700646 * config.getfloat("Settings", "budget") * 2
                print()
                print('Approximation(EV) based on current budget:')
                print(f'Cost: {int(ev_cost):,} (make sure you have at least this much gold)')
                print(f'Cov: {ev_cov:.1f}')
                print(f'mys: {ev_mys:.1f}')
                print()
            
            #Run refresh based on config file
            input('Press enter to start!')
            print(f'Press "{config["Settings"]["stop_refresh_key"]}" to terminate anytime!')
            print()
            print('Progress:')
            ADBSHOP = E7ADBShopRefresh(tap_sleep=config.getfloat("Settings", "tap_sleep"),
                                    budget=config.getfloat("Settings", "budget"),
                                    ip_port=ip_port,
                                    stop_refresh_key=config["Settings"]["stop_refresh_key"],
                                    random_offset=config.getboolean("Settings", "random_offset"),
                                    debug=False)
            ADBSHOP.start()
            print()
            input('press enter to exit...')
            sys.exit(0)


    debug = False
    print('First time user should always launch in debug mode')
    if input('Launch in debug mode? leave bank for no (yes/no): ').lower() == 'yes':
        debug = True
        print()
        print('Debug mode:')
        print('Program will buy friendship bookmarks for testing purpose')
        print('It will pause to generate a image window - will show up in the taskbar')
        print('If the click area shown is not within the UI button, do not use the randomize click feature')
        print('Closing the image window will continue to refresh action')
    else:
        print('Running as normal')
        print()

    #setting
    stop_refresh_key = 'esc'
    if debug:
        print('Keep looking at image until friendship bookmark or any bm is purchased')
        print('Use "esc" key to exit in debug mode')
    else:
        print("Input the key that you want to use to stop refresh (0-9 a-z /.,';[]) ")
        print('Leave blank to use "esc" key')
        stop_refresh_key = input('Key: ')
        
        if stop_refresh_key:
            print(f'"{stop_refresh_key}" key will be use to stop refresh')
        else:
            stop_refresh_key = 'esc'
            print('Default "esc" key to stop refresh')
    print()
    
    random_offset = False
    print('Only enable randomize click after going through a full loop of buying something in debug mode')
    if debug:
        random_offset = True
        print('Automatically enable randomize click due to debug mode')
    elif input('Enable randomize click (yes/no): ').lower() == 'yes':
        random_offset = True
        print('Randomize click enabled')
    else:
        print('Randomize click disabled')
    print()
    

    try:
        tap_sleep = float(input('Tap sleep(in seconds) Recommend - leave blank for 0.3 sec : '))
        tap_sleep = max(0.3, tap_sleep)
    except:
        print('Default to tap sleep of 0.3 second')
        tap_sleep = 0.3
    print()
    try:
        budget = 100
        if debug:
            print('Default to 100 skystone for debug testing')
        else:
            budget = float(input('Amount of skystone that you want to spend: '))
    except:
        print('invalid input, default to 1000 skystone budget')
        budget = 1000
    
    if not debug:
        print()
        saveConfigFile(tap_sleep=tap_sleep, budget=budget, stop_refresh_key=stop_refresh_key, random_offset=random_offset)
        print()

    if budget >= 1000:
            ev_cost = 1691.04536 * int(budget) * 2
            ev_cov = 0.006602509 * int(budget) * 2
            ev_mys = 0.001700646 * int(budget) * 2
            print('Approximation(EV) based on current budget:')
            print(f'Cost: {int(ev_cost):,} (make sure you have at least this much gold)')
            print(f'Cov: {ev_cov:.1f}')
            print(f'mys: {ev_mys:.1f}')
            print()
    input('Press enter to start!')
    print(f'Press "{stop_refresh_key}" to terminate anytime!')
    print()
    print('Progress:')
    ADBSHOP = E7ADBShopRefresh(tap_sleep=tap_sleep,
                               budget=budget,
                               ip_port=ip_port,
                               stop_refresh_key=stop_refresh_key,
                               random_offset=random_offset,
                               debug=debug)
    ADBSHOP.start()
    print()
    input('press enter to exit...')