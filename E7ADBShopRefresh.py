import subprocess
import os
from io import BytesIO
import time

from PIL import Image
import threading
import cv2
import numpy as np
import keyboard

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
        newItem = E7Item(image, price=0, count=0)
        self.inventory[name] = newItem 

class E7ADBShopRefresh:
    def __init__(self, tap_sleep:float = 0.5, budget=None):
        self.loop_active = False
        self.end_of_refresh = True
        self.tap_sleep = tap_sleep
        self.budget = budget
        self.refresh_count = 0
        self.keyboard_thread = threading.Thread(target=self.checkKeyPress)
        self.adb_path = os.path.join('adb-assets','platform-tools', 'adb')
        self.storage = E7Inventory()
        self.screenwidth = 1080
        self.screenheight = 1920
        self.updateScreenDimension()

        self.storage.addItem('cov.jpg', 'Covenant bookmark', 184000)
        self.storage.addItem('mys.jpg', 'Mystic medal', 280000)
        #self.storage.addItem('fb.jpg', 'Friendship bookmark', 18000)

    def start(self):
        self.loop_active = True
        self.end_of_refresh = False
        self.keyboard_thread.start()
        self.refreshShop()

    #threads
    def checkKeyPress(self):
        while(self.loop_active and not self.end_of_refresh):
            self.loop_active = not keyboard.is_pressed('esc')
        print('Shop refresh terminated!\n')

    def refreshShop(self):
        self.clickShop()
        #time needed for item to drop in after refresh
        sliding_time = 0.8

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
            x1 = str(1.111 * self.screenwidth)
            y1 = str(0.365 * self.screenheight)
            y2 = str(0.260 * self.screenheight)
            adb_process = subprocess.run([self.adb_path, 'shell', 'input', 'swipe', x1, y1, x1, y2])
            #wait for action to complete
            time.sleep(0.5)

            if not self.loop_active: break
            #look at shop (page 2)
            screenshot = self.takeScreenshot()
            for key, value in self.storage.inventory.items():
                pos = self.findItemPosition(screenshot, value.image)
                if pos is not None and key not in brought:
                    self.clickBuy(pos)
                    value.count += 1

            if not self.loop_active: break
            if self.budget:
                if self.refresh_count >= self.budget//3:
                    break

            self.clickRefresh()
            self.refresh_count += 1
        
        self.end_of_refresh = True
        self.loop_active = False
        self.printResult()
    
    #helper function
    def printResult(self):
        print('---Result---')
        for key, value in self.storage.inventory.items():
            print(key, ':', value.count)
        print('Skystone spent:', self.refresh_count*3)

    def updateScreenDimension(self):
        adb_process = subprocess.run([self.adb_path, 'exec-out', 'screencap','-p'], stdout=subprocess.PIPE)
        byte_image = BytesIO(adb_process.stdout)
        pil_image = Image.open(byte_image)
        pil_image = np.array(pil_image)
        x, y, _ = pil_image.shape
        self.screenwidth = x
        self.screenheight = y


    def takeScreenshot(self):
        adb_process = subprocess.run([self.adb_path, 'exec-out', 'screencap','-p'], stdout=subprocess.PIPE)
        byte_image = BytesIO(adb_process.stdout)
        pil_image = Image.open(byte_image)
        pil_image = np.array(pil_image)
        screenshot = cv2.cvtColor(pil_image, cv2.COLOR_BGR2GRAY)
        # ims = cv2.resize(screenshot, (960, 540))
        # cv2.imshow('image window', ims)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        return screenshot

    def findItemPosition(self, screen_image, item_image):
        result = cv2.matchTemplate(screen_image, item_image, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= 0.75)

        if loc[0].size > 0:
            x = loc[1][0] + self.screenwidth * 0.829
            y = loc[0][0] + self.screenheight * 0.052
            pos = (x, y)
            return pos
        return None

    #macro
    def clickShop(self):
        #newshop
        x = self.screenwidth * 0.072
        y = self.screenheight * 0.164
        adb_process = subprocess.run([self.adb_path, 'shell', 'input', 'tap', str(x), str(y)])
        time.sleep(self.tap_sleep)

        #oldshop
        x = self.screenwidth * 0.791
        y = self.screenheight * 0.134
        adb_process = subprocess.run([self.adb_path, 'shell', 'input', 'tap', str(x), str(y)])
        time.sleep(self.tap_sleep)

        #newshop
        x = self.screenwidth * 0.072
        y = self.screenheight * 0.164
        adb_process = subprocess.run([self.adb_path, 'shell', 'input', 'tap', str(x), str(y)])
        time.sleep(self.tap_sleep)

    def clickBuy(self, pos):
        if pos is None:
            return False
        
        x, y = pos
        adb_process = subprocess.run([self.adb_path, 'shell', 'input', 'tap', str(x), str(y)])
        time.sleep(self.tap_sleep)

        #confirm
        x = self.screenwidth * 0.997
        y = self.screenheight * 0.394
        adb_process = subprocess.run([self.adb_path, 'shell', 'input', 'tap', str(x), str(y)])
        time.sleep(self.tap_sleep)
    
    def clickRefresh(self):
        x = self.screenwidth * 0.302
        y = self.screenheight * 0.514
        adb_process = subprocess.run([self.adb_path, 'shell', 'input', 'tap', str(x), str(y)])
        time.sleep(self.tap_sleep)

        if not self.loop_active: return
        #confirm
        x = self.screenwidth * 1.031
        y = self.screenheight * 0.343
        adb_process = subprocess.run([self.adb_path, 'shell', 'input', 'tap', str(x), str(y)])
        time.sleep(self.tap_sleep)


if __name__ == '__main__':

    #intro
    print('Epic Seven Shop Refresh with ADB')
    print('Before launching this application')
    print('Make sure Epic Seven is opened and that ADB is turned on')
    print('(relaunch this application if the above condition is not met)')
    print()
    input('when you finish reading, press enter to continue!')
    print()

    #settings
    try:
        tap_sleep = float(input('Tap sleep(in seconds) recommand 0.5: '))
    except:
        print('invalid input, default to tap sleep of 0.5 second')
        tap_sleep = 0.5
    try:
        budget = float(input('Amount of skystone that you want to spend:'))
    except:
        print('invalid input, default to 1000 skystone budget')
        budget = 1000
    print()
    input('Press enter to start!')
    print('Press Esc to terminate anytime!')
    ADBSHOP = E7ADBShopRefresh(tap_sleep=tap_sleep, budget=budget)
    ADBSHOP.start()
    print()
    input('press enter to exit...')