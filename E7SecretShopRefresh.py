#import built-in
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
import csv
import os
import time
import threading
from datetime import datetime

#Library
import pyautogui
import pygetwindow as gw
import cv2
import numpy as np
import keyboard
from PIL import ImageGrab

class ShopItem:
    def __init__(self, path='', image=None, price=0, count=0):
        self.path=path
        self.image=image
        self.price=price
        self.count=count

    def __repr__(self):
        return f'ShopItem(path={self.path}, image={self.image}, price={self.price}, count={self.count})'

class RefreshStatistic:
    def __init__(self):
        self.refresh_count = 0
        self.items = {}
        
    def addShopItem(self, path: str, name='', price=0, count=0):
        image = cv2.imread(os.path.join('assets', path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        newItem = ShopItem(path, image, price, count)
        self.items[name] = newItem
    
    def getInventory(self):
        return self.items

    def getName(self):
        return list(self.items.keys())

    def getPath(self):
        res = []
        for value in self.items.values():
            res.append(value.path)
        return res
    
    def getItemCount(self):
        res = []
        for value in self.items.values():
            res.append(value.count)
        return res
    
    def getTotalCost(self):
        total = 0
        for value in self.items.values():
            total += value.price * value.count
        return total
    
    def incrementRefreshCount(self):
        self.refresh_count += 1
    
    def writeToCSV(self):
        res_folder = 'ShopRefreshHistory'
        if not os.path.exists(res_folder):
            os.makedirs(res_folder)

        gen_path = 'refreshAttempt'
        for name in self.getName():
            gen_path += name[:4]
        gen_path += '.csv'

        path = os.path.join(res_folder, gen_path)

        if not os.path.isfile(path):
            with open(path, 'w', newline='') as file:
                writer = csv.writer(file)
                column_name = ['Time', 'Refresh count', 'Skystone spent', 'Gold spent']
                column_name.extend(self.getName())
                writer.writerow(column_name)
        with open(path, 'a', newline='') as file:
            writer = csv.writer(file)
            data = [datetime.now(), self.refresh_count, self.refresh_count*3, self.getTotalCost()]
            data.extend(self.getItemCount())
            writer.writerow(data)

class SecretShopRefresh:
    def __init__(self, title_name: str, callback = None, tk_instance: tk = None, budget: int = None, allow_move: bool = False, debug: bool = False, join_thread: bool = False):
        #init state
        self.debug = debug
        self.loop_active = False
        self.loop_finish = True
        self.mouse_sleep = 0.2
        self.screenshot_sleep = 0.3
        self.callback = callback if callback else self.refreshFinishCallback
        self.budget = budget
        self.allow_move = allow_move
        self.join_thread = join_thread

        self.loading_asset = cv2.imread(os.path.join('assets', 'loading.jpg'))
        self.loading_asset= cv2.cvtColor(self.loading_asset, cv2.COLOR_BGR2GRAY)

        #find window
        self.title_name = title_name
        windows = gw.getWindowsWithTitle(self.title_name)
        self.window = next((w for w in windows if w.title == self.title_name), None)

        self.tk_instance = tk_instance
        self.rs_instance = RefreshStatistic()

    #Start shop refresh macro
    def start(self):
        if self.loop_active or not self.loop_finish:
            return
        
        self.loop_active = True
        self.loop_finish = False 
        keyboard_thread = threading.Thread(target=self.checkKeyPress)
        refresh_thread = threading.Thread(target=self.shopRefreshLoop)
        keyboard_thread.daemon = True
        refresh_thread.daemon = True
        keyboard_thread.start()
        refresh_thread.start()
        if self.join_thread:
            keyboard_thread.join()
            refresh_thread.join()

    #Threads
    def checkKeyPress(self):
        while self.loop_active and not self.loop_finish:
            self.loop_active = not keyboard.is_pressed('esc')
        self.loop_active = False
        print('Terminating shop refresh ...')

    def refreshFinishCallback(self):
        print('Terminated!')

    def shopRefreshLoop(self):
        
        try:
            if self.window.isMaximized or self.window.isMinimized:
                self.window.restore()
            if not self.allow_move: self.window.moveTo(0, 0)
            self.window.resizeTo(906, 539)
        except Exception as e:
            print(e)
            self.loop_active = False
            self.loop_finish = True
            self.callback()
            return

        #show mini display
        #generating mini image
        mini_images = []
        hint, mini_labels = None, None
        if self.tk_instance:
            selected_path = self.rs_instance.getPath()
            for path in selected_path:
                img = Image.open(os.path.join('assets', path))
                img = img.resize((45,45))
                img = ImageTk.PhotoImage(img)
                mini_images.append(img)
            hint, mini_labels = self.showMiniDisplays(mini_images)

        #update state on minidisplay
        def updateMiniDisplay():
            for label, count in zip(mini_labels, self.rs_instance.getItemCount()):
                label.config(text=count)
            
        time.sleep(self.mouse_sleep)
        
        if not self.loop_active:
            if hint: hint.destroy()
            self.loop_finish = True
            self.callback()
            return
        
        try:
            #replace with window activate in python
            # window.minimize()
            # window.maximize()
            # window.restore()
            try:
                self.window.activate()
            except Exception as e:
                print(e)

            self.clickShop()
            time.sleep(1)
            
            #item sliding const
            sliding_time = 0.7 + self.screenshot_sleep if self.screenshot_sleep >= 0.3 else 1

            #Loop for how the 
            while self.loop_active:
                
                self.window.resizeTo(906, 539)
                
                #array for determining if an item has been purchsed in this loop
                brought = set()
                if not self.loop_active: break

                #take screenshot, check for items, buy all items that appear
                time.sleep(sliding_time)    #This is a constant sleep to account for the item sliding in frame
                
                ###start of bundle refresh
                screenshot = self.takeScreenshot()
                process_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

                #show image if in debug
                if self.debug:
                    cv2.imshow('Press any key to continue ...', process_screenshot)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()

                #checks if loading screen is blocking
                check_screen, reset = self.checkLoading(process_screenshot)
                if check_screen is None:
                    break      
                else:
                    process_screenshot = check_screen

                if reset:
                    # x = self.window.left + self.window.width * 0.04
                    # y = self.window.top + self.window.height * 0.10
                    # pyautogui.moveTo(x, y)
                    # pyautogui.click()
                    # time.sleep(1)
                    # self.clickShop()
                    self.scrollUp()
                    time.sleep(0.5)
                    continue
                
                #loop through all the assets to find item to buy
                for key, value in self.rs_instance.getInventory().items():
                    pos = self.findItemPosition(process_screenshot, value.image)
                    if pos is not None:
                        self.clickBuy(pos)
                        value.count += 1
                        brought.add(key)

                #real time count UI update
                if hint: updateMiniDisplay()
                if not self.loop_active: break
                
                #scroll shop
                self.scrollShop()
                time.sleep(self.mouse_sleep)
                if not self.loop_active: break

                ###start of bundle refresh
                screenshot = self.takeScreenshot()
                process_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

                #show image if in debug
                if self.debug:
                    cv2.imshow('Press any key to continue ...', process_screenshot)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()

                #checks if loading screen is blocking
                check_screen, reset = self.checkLoading(process_screenshot)
                if check_screen is None:
                    break      
                else:
                    process_screenshot = check_screen

                if reset:
                    for key in brought:
                        value = self.rs_instance.items.get(key)
                        if value:
                            value.count -= 1

                    # x = self.window.left + self.window.width * 0.04
                    # y = self.window.top + self.window.height * 0.10
                    # pyautogui.moveTo(x, y)
                    # pyautogui.click()
                    # time.sleep(1)
                    # self.clickShop()
                    self.scrollUp()
                    time.sleep(0.5)
                    continue
                
                #loop through all the assets to find item to buy
                for key, value in self.rs_instance.getInventory().items():
                    pos = self.findItemPosition(process_screenshot, value.image)
                    if pos is not None and key not in brought:
                        self.clickBuy(pos)
                        value.count += 1

                if hint: updateMiniDisplay()
                if not self.loop_active: break
                
                #check budget
                if self.budget:
                    if self.rs_instance.refresh_count >= self.budget // 3:
                        break
                    
                #refresh shop
                self.clickRefresh()
                self.rs_instance.incrementRefreshCount()
                time.sleep(self.mouse_sleep)
                if self.window.title != self.title_name: break

        except Exception as e:
            print(e)
            if hint: hint.destroy()
            self.rs_instance.writeToCSV()
            self.loop_active = False
            self.loop_finish = True
            self.callback()
            return
            
        if hint: hint.destroy()
        self.rs_instance.writeToCSV()
        self.loop_active = False
        self.loop_finish = True
        self.callback()

    #show mini display
    def showMiniDisplays(self, mini_images):
        bg_color = '#171717'
        fg_color = '#dddddd'

        if self.tk_instance is None:
            return None, None
        #Display exit key
        hint = tk.Toplevel(self.tk_instance)
        hint.geometry(r'200x200+%d+%d' % (self.window.left, self.window.top+self.window.height))
        hint.title('Hint')
        hint.iconbitmap(os.path.join('assets','icon.ico'))
        tk.Label(master=hint, text='Press ESC to stop refreshing!', bg=bg_color, fg=fg_color).pack()
        hint.config(bg=bg_color)

        #Display stat
        mini_stats = tk.Frame(master=hint, bg=bg_color)
        mini_labels = []
        
        #packing mini image
        for img in mini_images:
            frame = tk.Frame(mini_stats, bg=bg_color)
            tk.Label(master=frame, image=img, bg=bg_color).pack(side=tk.LEFT)
            count = tk.Label(master=frame, text='0', bg=bg_color, fg='#FFBF00')
            count.pack(side=tk.RIGHT)
            mini_labels.append(count)
            frame.pack()
        mini_stats.pack()
        return hint, mini_labels

    #add item to list
    def addShopItem(self, path: str, name='', price=0, count=0):
        self.rs_instance.addShopItem(path, name, price, count)

    #take screenshot of entire window
    def takeScreenshot(self):
        try:
            #replace with window activate in python
            # window.minimize()
            # window.maximize()
            # window.restore()
            try:
                self.window.activate()
            except Exception as e:
                print(e)

            #fix pyautogui's multiscreen bug
            #screenshot = pyautogui.screenshot(region=(self.window.left, self.window.top, self.window.width, self.window.height))
            region=[self.window.left, self.window.top, self.window.width, self.window.height]
            screenshot = ImageGrab.grab(bbox=(region[0], region[1], region[2] + region[0], region[3] + region[1]), all_screens=True)
            screenshot = np.array(screenshot)
            return screenshot
        
        except Exception as e:
            print(e)
            return None
        
    def checkLoading(self, process_screenshot):
        result = cv2.matchTemplate(process_screenshot, self.loading_asset, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= 0.75)
        if loc[0].size <= 0:
            return process_screenshot, False
        
        for _ in range(14):
            time.sleep(1)
            screenshot = self.takeScreenshot()
            process_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(process_screenshot, self.loading_asset, cv2.TM_CCOEFF_NORMED)
            loc = np.where(result >= 0.75)
            if loc[0].size <= 0:
                time.sleep(1.5)
                screenshot = self.takeScreenshot()
                process_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                return process_screenshot, True

        return None, False

    #return item position
    def findItemPosition(self, process_screenshot, process_item):
        
        result = cv2.matchTemplate(process_screenshot, process_item, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= 0.75)
        x, y = 1, 1
        
        #debug mode!
        if self.debug and loc[0].size > 0:
            debug_screenshot = process_screenshot.copy()
            for pt in zip (*loc[::-1]):
                cv2.rectangle(debug_screenshot, pt, (pt[0] + process_item.shape[1], pt[1] + process_item.shape[0]), (255, 255,0), 2)
            cv2.imshow('Press any key to continue ...', debug_screenshot)
            #cv2.imwrite('Debug.png', debug_screenshot)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        if loc[0].size > 0:
            x = self.window.left + self.window.width*0.90
            y = self.window.top + loc[0][0] + process_item.shape[0]*0.85
            pos = (x, y)        
            return pos
        return None
    
    #BUY MACRO
    def clickBuy(self, pos):
        if pos is None:
            return False
        x, y = pos
        pyautogui.moveTo(x, y)
        pyautogui.click(clicks=2, interval=self.mouse_sleep)
        time.sleep(self.mouse_sleep)
        self.clickConfirmBuy()
        return True

    def clickConfirmBuy(self):
        x = self.window.left + self.window.width * 0.55
        y = self.window.top + self.window.height * 0.70
        pyautogui.moveTo(x, y)
        pyautogui.click(clicks=2, interval=self.mouse_sleep)
        time.sleep(self.mouse_sleep)
        time.sleep(self.screenshot_sleep)   #Account for Loading

        #checks if loading screen is blocking
        screenshot = self.takeScreenshot()
        process_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        self.checkLoading(process_screenshot)

    #REFRESH MACRO
    def clickRefresh(self):
        x = self.window.left + self.window.width * 0.20
        y = self.window.top + self.window.height * 0.90
        pyautogui.moveTo(x, y)
        pyautogui.click(clicks=2, interval=self.mouse_sleep)
        time.sleep(self.mouse_sleep)
        self.clickConfirmRefresh()

    def clickConfirmRefresh(self):
        x = self.window.left + self.window.width * 0.58
        y = self.window.top + self.window.height * 0.65
        pyautogui.moveTo(x, y)
        pyautogui.click(clicks=2, interval=self.mouse_sleep)
        time.sleep(self.screenshot_sleep)   #Account for Loading

    #SHOP MACRO
    def clickShop(self):
        #wake window
        x = self.window.left + self.window.width * 0.05
        y = self.window.top + self.window.height * 0.41
        pyautogui.moveTo(x, y)
        pyautogui.click()

        time.sleep(self.mouse_sleep)

        #old lobby
        x = self.window.left + self.window.width * 0.44
        y = self.window.top + self.window.height * 0.26
        pyautogui.moveTo(x, y)
        pyautogui.click()

        time.sleep(self.mouse_sleep)

        #new lobby
        x = self.window.left + self.window.width * 0.05
        y = self.window.top + self.window.height * 0.41
        pyautogui.moveTo(x, y)
        pyautogui.click()

    def scrollShop(self):
        x = self.window.left + self.window.width * 0.58
        y = self.window.top + self.window.height * 0.65
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown(button='left')
        pyautogui.moveTo(x, y-self.window.height*0.277)
        pyautogui.mouseUp(button='left')
    
    def scrollUp(self):
        x = self.window.left + self.window.width * 0.58
        y = self.window.top + self.window.height * 0.65
        pyautogui.moveTo(x, y-self.window.height*0.277)
        pyautogui.mouseDown(button='left')
        pyautogui.moveTo(x, y)
        pyautogui.mouseUp(button='left')

class AppConfig():
    def __init__(self):
        # here is where you can config setting
        #general setting
        self.RECOGNIZE_TITLES = {'Epic Seven',
                                 'BlueStacks App Player',
                                 'LDPlayer',
                                 'MuMu Player 12',
                                 '에픽세븐'}        #if detected title show up in the select bar so that you don't need to manual enter
        self.ALL_PATH = ['cov.jpg', 'mys.jpg', 'fb.jpg']        #Path to all the image
        self.ALL_NAME = ['Covenant bookmark','Mystic medal','Friendship bookmark']      #Name to all the image
        self.ALL_PRICE = [184000,280000,18000]      #Price to the image
        self.MANDATORY_PATH = {'cov.jpg', 'mys.jpg'}        #make item unable to be unselected
        self.DEBUG = False
        

class AutoRefreshGUI:
    def __init__(self):
        self.app_config = AppConfig()
        self.root = tk.Tk()
        
        #gui
        #color
        self.unite_bg_color = '#171717'
        self.unite_text_color = '#dddddd'

        self.root.config(bg=self.unite_bg_color)
        self.root.attributes("-alpha", 0.95)

        self.root.title('SHOP AUTO REFRESH')
        self.root.geometry('420x745')
        self.root.minsize(420, 745)
        icon_path = os.path.join('assets', 'gui_icon.ico')
        self.root.iconbitmap(icon_path)
        self.title_name = ''
        self.mouse_speed = 0.2
        self.screenshot_speed = 0.3
        self.ignore_path = set(self.app_config.ALL_PATH)-self.app_config.MANDATORY_PATH
        self.keep_image_open = []
        self.lock_start_button = False
        self.budget = ''

        #app title and image        #apply ui change here
        app_title = tk.Label(self.root, text='Epic Seven shop refresh',
                             font=('Helvetica',24),
                             bg=self.unite_bg_color,
                             fg=self.unite_text_color)
        
        #title selection combo box
        def onSelect(event):
            t_name = titles_combo_box.get()
            if t_name not in gw.getAllTitles():
                self.start_button.config(state=tk.DISABLED)
                return
            
            self.title_name = titles_combo_box.get()
            if not self.lock_start_button:
                self.start_button.config(state=tk.NORMAL)

        def onEnter(event):
            title = titles_combo_box.get()
            if title == '' or title not in gw.getAllTitles():
                self.start_button.config(state=tk.DISABLED)
                return
            self.title_name = titles_combo_box.get()
            if not self.lock_start_button:
                self.start_button.config(state=tk.NORMAL)

        #sort title
        titles = [title for title in self.app_config.RECOGNIZE_TITLES]
        titles.sort()

        titles_combo_box = ttk.Combobox(master=self.root,
                                    values=titles)
        titles_combo_box.config()       #apply ui change here
        titles_combo_box.bind('<<ComboboxSelected>>', onSelect)
        titles_combo_box.bind('<KeyRelease>', onEnter)
        
        #special setting
        special_frame = tk.Frame(self.root, bg=self.unite_bg_color)
        self.hint_cbv = tk.IntVar()
        self.move_zerozero_cbv = tk.IntVar()
        
        def setupSpecialSetting(label, value):
            frame = tk.Frame(special_frame, bg=self.unite_bg_color)
            special_label = tk.Label(master=frame,
                             text=label,
                             bg=self.unite_bg_color,
                             fg=self.unite_text_color,
                             font=('Helvetica',12))
            special_cb = tk.Checkbutton(master=frame,
                                font=('Helvetica',14),
                                variable=value,
                                bg=self.unite_bg_color)
            special_cb.select()
            special_label.pack(side=tk.LEFT)
            special_cb.pack(side=tk.RIGHT)
            frame.pack()

        setupSpecialSetting('Hint:', self.hint_cbv)
        setupSpecialSetting('Auto move emulator window to top left:', self.move_zerozero_cbv)

        #setting frame
        setting_frame = tk.Frame(self.root)
        setting_frame.config(bg=self.unite_bg_color)        #apply ui change here
        def packSettingEntry(text, default = None):
            frame = tk.Frame(setting_frame, bg=self.unite_bg_color, pady=4)
            label = tk.Label(master=frame,
                             text=text,
                             bg=self.unite_bg_color,
                             fg=self.unite_text_color,
                             font=('Helvetica',12))         #apply ui change here
            entry = tk.Entry(master=frame,
                             bg='#333333',
                             fg=self.unite_text_color,
                             font=('Helvetica',12),
                             width=10)
            label.pack(side=tk.LEFT)
            if default or default == 0:
                entry.insert(0, default)
            
            entry.pack(side=tk.RIGHT)
            frame.pack()
            return entry


        #start refreshing button
        self.start_button = tk.Button(master=self.root,
                                text='Start refresh',
                                font=('Helvetica',14),
                                state=tk.DISABLED,
                                command=self.startShopRefresh)
        if titles:
            for t in titles:
                if t in gw.getAllTitles():
                    self.title_name = t
                    titles_combo_box.set(self.title_name)
                    if not self.lock_start_button:
                        self.start_button.config(state=tk.NORMAL)
                    break

        #UI from top to down
        app_title.pack(pady=(15,0))
        #Step 1 Select the emulator
        #Type in the window title of your emulator. For example, window title of this program is: SHOP AUTO REFRESH
        self.packMessage('Select emulator or type emulator\'s window title:')
        titles_combo_box.pack()
        #Step 2 Select item
        self.packMessage('Select item that you are looking for:')
        for index, path in enumerate(self.app_config.ALL_PATH):
            self.keep_image_open.append(ImageTk.PhotoImage(Image.open(os.path.join('assets', path))))
            self.packItem(index, path)
        self.packMessage('Setting:', 18, (10,0))
        #Step 3 Select setting
        #check if input is valid
        def validateFloat(value, action):
            if action == '1':
                try:
                    float_value = float(value)
                    return float_value >= 0 and float_value <= 10
                except:
                    return False
            return True
        
        def validateInt(value):
            try:
                if value == '':
                    return True
                int_value = int(value)
                if int_value > 100000000:
                    return False
                else:
                    return value.isdigit()
            except:
                return False
        
        valid_float_reg = self.root.register(validateFloat)
        self.mouse_speed_entry = packSettingEntry('Mouse speed (s):', self.mouse_speed)
        self.screenshot_speed_entry = packSettingEntry('Screenshot speed (s):', self.screenshot_speed)
        self.mouse_speed_entry.config(validate='key', validatecommand=(valid_float_reg, '%P', '%d'))
        self.screenshot_speed_entry.config(validate='key', validatecommand=(valid_float_reg, '%P', '%d'))

        valid_int_reg = self.root.register(validateInt)
        self.limit_spend_entry = packSettingEntry('How many skystone do you want to spend? :', None)
        self.limit_spend_entry.config(validate='key', validatecommand=(valid_int_reg, '%P'))

        #Step 3.5 special setting and setting
        special_frame.pack(pady=(0,5))
        setting_frame.pack()

        #Step 4 profit
        self.start_button.pack(pady=(30,0))
        
        self.root.mainloop()
        
    def packItem(self, index, path):        #change ui here

        def updateIgnore():
            if cbv.get() == 1:
                self.ignore_path.discard(path)
            else:
                self.ignore_path.add(path)
        
        cbv = tk.IntVar()
        frame = tk.Frame(self.root, bg=self.unite_bg_color, pady=10)
        cb = tk.Checkbutton(master=frame, variable=cbv, command=updateIgnore, bg=self.unite_bg_color)
        cb.pack(side=tk.LEFT)
        
        if path in self.app_config.MANDATORY_PATH:
            cb.config(state=tk.DISABLED)
            cb.select()
        
        image_label = tk.Label(master=frame, image=self.keep_image_open[index], bg='#FFBF00')
        image_label.pack(side=tk.RIGHT)
        frame.pack()

    def packMessage(self, message, text_size=14, pady=10):               #apply ui change here
        new_label = tk.Label(self.root, text=message, font=('Helvetica',text_size), bg=self.unite_bg_color, fg=self.unite_text_color)
        new_label.pack(pady=pady)
        return new_label

    def refreshComplete(self):
        print('Terminated!')
        self.root.title('SHOP AUTO REFRESH')
        self.start_button.config(state=tk.NORMAL)
        self.lock_start_button = False

    #start refresh loop    
    def startShopRefresh(self):
        self.root.title('Press ESC to stop!')
        self.lock_start_button = True
        self.start_button.config(state=tk.DISABLED)

        if self.hint_cbv.get() == 1:
            self.ssr = SecretShopRefresh(title_name=self.title_name, callback=self.refreshComplete, tk_instance=self.root, debug=self.app_config.DEBUG)
        else:
            self.ssr = SecretShopRefresh(title_name=self.title_name, callback=self.refreshComplete, debug=self.app_config.DEBUG)

        if self.move_zerozero_cbv.get() != 1:
            self.ssr.allow_move = True

        #setting item to refresh for
        rs_instance = RefreshStatistic()
        all_data = zip(self.app_config.ALL_PATH, self.app_config.ALL_NAME, self.app_config.ALL_PRICE)
        for path, name, price in all_data:
            if path not in self.ignore_path:
                rs_instance.addShopItem(path, name, price)
        self.ssr.rs_instance = rs_instance
        
        #setting mouse speed
        self.ssr.mouse_sleep = float(self.mouse_speed_entry.get()) if self.mouse_speed_entry.get() != '' else self.mouse_speed
        self.ssr.screenshot_sleep = float(self.screenshot_speed_entry.get()) if self.screenshot_speed_entry.get() != '' else self.screenshot_speed

        #setting up skystone budget
        if self.limit_spend_entry.get() != '':
            self.ssr.budget = int(self.limit_spend_entry.get())

        print('refresh shop start!')
        print('Budget:', self.ssr.budget)
        print('Mouse speed:', self.ssr.mouse_sleep)
        print('Screenshot speed', self.ssr.screenshot_sleep)
        if self.ssr.budget and self.ssr.budget >= 1000:
            ev_cost = 1691.04536 * int(self.ssr.budget) * 2
            ev_cov = 0.006602509 * int(self.ssr.budget) * 2
            ev_mys = 0.001700646 * int(self.ssr.budget) * 2
            print('Approximation based on budget:')
            print(f'Cost: {int(ev_cost):,}')
            print(f'Cov: {ev_cov}')
            print(f'mys: {ev_mys}')
        print()
        
        self.ssr.start()

if __name__ == '__main__':
    # Secret shop with GUI
    gui = AutoRefreshGUI()
    
    # # Uncomment below code start secret shop without gui, remember to comment everything above
    # # Here are some parameter that you can pass in to secret shop calss
    # # title_name: str      name of your emulator window
    # # call_back: func      callback function when the macro terminates
    # # budget: int          the ammont of skystone that you want to spend
    # # debug: boolean       this will help you debug problem with the program
    # # join_thread: boolean        you have to join thread if nothing is blocking the main process from completing
    
    # if not os.path.isdir(os.path.join('assets')):
    #     print('\'assets\' folder is missing! Make sure you have the assets folder in the same directory')
    #     input('Press enter to exit ...')

    # else:
    #     print('Here are the active windows\n')
    #     for title in gw.getAllTitles():
    #         if title != '':
    #             print(title)
    #     print()
    #     win = input('Emulator\'s window name: ')
        
    #     if win in gw.getAllTitles() and win != '':
    #         try:
    #             budget = int(input('Amount of skystone that you want to spend: '))
    #         except:
    #             print('invalid input, default to 1000 skystone budget')
    #             budget = 1000

    #         ssr = SecretShopRefresh(title_name=win, budget=budget, join_thread=True)       #init macro instance with the application title being epic seven
    #         ssr.addShopItem('cov.jpg', 'Covenant bookmark', 184000)     #adding items to refresh, cov.jpg needs to be in: assets/cov.jpg
    #         ssr.addShopItem('mys.jpg', 'Mystic medal', 280000)
    #         #ssr.addShopItem('fb.jpg', 'Friendship bookmark', 18000)     #comment out this, if you don't need to test
    #         input('press Enter to start ...')
    #         print('press esc to stop shop refresh')
    #         ssr.start()     #Start macro instance, use ESC to terminate macro

    #     else:
    #         input('Wrong title, close program')    
    #     # Eric baby piles approved