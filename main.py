
import webview

from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
from pynput import keyboard , mouse
import pyautogui as pg
import time
from pynput.mouse import Controller as mC
from pynput.keyboard import Controller as kC


from tinydb import TinyDB, Query
import ctypes
import os
from pynput.keyboard import Key
from pynput.mouse import Button

awareness = ctypes.c_int()
ctypes.windll.shcore.SetProcessDpiAwareness(2)
CAREA = 50

def getTime():
    return round(time.time()*1000)

class Autom:
    
    def __init__(self, wrapper):
        self.recordName = getTime()
        self.wrapper = wrapper


    def start(self):
        self.db = TinyDB(f"./files/tmp/{self.recordName}")  
        awareness = ctypes.c_int()
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        self.mice = mC()
        self.oldMove = self.mice.position  
        (x,y)=self.mice.position
        # self.db.insert({'x':x, 'y':x, 'c':'move','t':getTime()})

        self.keyboard_listener = KeyboardListener(on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener = MouseListener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)

        # Start the threads and join them so the script doesn't end early
        self.keyboard_listener.start()
        self.mouse_listener.start()
        self.keyboard_listener.join()
        self.mouse_listener.join()

        

    
    def stop(self):
        print("Record Stop")
        self.wrapper.onAutoStop()
        self.db.storage.close()
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
        return True
        
        
   

            
    def on_scroll(self,x, y, dx, dy):
        self.db.insert({'t':getTime(), 'c':'scroll', 'dx':dx, 'dy':dy})

    def on_press(self,key):
        try:

            self.db.insert({'t':getTime(), 'c':'down', 'b':key.char, 'a':0})
            # print(key.char, 'char')


        except AttributeError:
            if key.name=="f12":
                name = getTime()
                x,y=self.mice.position
                region = (x-CAREA/2, y-CAREA/2, CAREA, CAREA)
                print(region, name)
                ss = pg.screenshot(region=region)
                ss.save(f"./files/click/{name}.png")
                self.db.insert({'t':name, 'c':'wait', })
            else:
                self.db.insert({'t':getTime(), 'c':'down', 'b':key.name, 'a':1})
        

    def on_release(self, key):

        try:
            self.db.insert({'t':getTime(), 'c':'up', 'b':key.char,'a':0})


        except AttributeError:
            if key.name=="f12":
                pass
            else:
                self.db.insert({'t':getTime(), 'c':'up', 'b':key.name,'a':1})


        if key == keyboard.Key.esc:
            # Stop listener
            self.stop()
            return False

    def on_move(self,x, y):
        # x1,y1= self.oldMove
        # dx,dy=x-x1,y-y1

        # self.oldMove = (x,y)
        # print(dx,dy)
        # self.db.insert({'x':dx, 'y':dy, 'c':'move','t':getTime()})
        self.db.insert({'x':x, 'y':y, 'c':'move','t':getTime()})
    


    def on_click(self,x, y, button, pressed):
        if pressed:
    
            self.db.insert({'t':getTime(), 'c':'click', 'b':button.value})
        else:
            self.db.insert({'t':getTime(), 'c':'release', 'b':button.value})


class Play:
    
    def __init__(self, name, wrapper):
        self.wrapper = wrapper
        self.name = name
        self.db = TinyDB(f"./files/saved/{name}")
        self.dball = self.db.all()

        self.mice = mC()
        self.kbd = kC()
        self.isPlay = False

    def stop(self):
        print("Stop Play")
        self.isPlay = False
        self.db.storage.close()


    def play(self):
        if self.isPlay:
            return False

        self.isPlay = True
        preTime = self.dball[0]["t"]

        for i in self.dball[0:]:
            if not self.isPlay:
               
                break

            c = i['c']
            if c=="down":
                if i['a']==1:
                    self.kbd.press(Key[i['b']])
                    print(Key[i['b']], 'down')
                else:
                    self.kbd.press(i['b'])
                    print(i['b'], "down")


            elif c=="up":
                if i['a']==1:
                    self.kbd.release(Key[i['b']])
                    print(Key[i['b']], 'up')



                else:
                    self.kbd.release(i['b'])
                    print(i['b'], "up")
            
            elif c=='move':
                self.mice.position =(i['x'], i['y'])
            
            elif c=='click':
             
                if i['b'][0]==4:
                    self.mice.press(Button.left)
                    print("click Left")
                
                if i['b'][0]==16:
                    self.mice.press(Button.right)
                    print("click Right")


            elif c=='release':
                # self.mice.press()
                if i['b'][0]==4:
                    self.mice.release(Button.left)
                    print("Relase Left")

                
                if i['b'][0]==16:
                    self.mice.release(Button.right)
                    print("Release right")

            

            if c=='wait':
                img = pg.locateCenterOnScreen(f"./files/saved/{i['t']}.png", confidence=0.6, grayscale=False)
                while img==None:
                    print('try')
                    img = pg.locateCenterOnScreen(f"./files/saved/{i['t']}.png",confidence=0.6,grayscale=False)
                
                print(img)
                self.mice.position = img
            else:
                time.sleep((i['t']-preTime)/1000)
                preTime = i['t']

        self.stop()
        self.wrapper.handlePlay()




    
    

 


class Api:

 
    

    def __init__(self, wrapper):
        self.cancel_heavy_stuff_flag = False
        self.automPlay=None
        self.autom=None
        self.wrapper = wrapper

    def record(self):
        
        self.autom = Autom(self.wrapper)
        self.autom.start()
        self.automName = self.autom.recordName
    
    def stop(self):
        print(self.autom)
        self.autom.stop()

    def getFiles(self):
        return [{"name":i} for i in os.listdir("./files/saved")]

    def play(self,name):
        print(name)
        self.automPlay = Play(name, self.wrapper)
        
        self.automPlay.play()

    def rename(self, name):
        os.rename(f"./files/tmp/{self.automName}", f"./files/saved/{name}")

    def removeFile(self, name):
        os.remove(f"./files/saved/{name}")
        return self.getFiles()

    def play_stop(self):
     
        self.automPlay.stop()



    def error(self):
        raise Exception('This is a Python exception')


class AutomWrapper:
    def __init__(self):
        self.api = Api(self)
        with open("./gui/index.html") as gui_index_file:
            self.window = webview.create_window('AUTOM v1',"./gui/index.html", js_api=self.api,width=320, height=480, resizable=False)
            webview.start(debug=True)

    def onAutoStop(self):
        self.window.evaluate_js("window.handleState('save')")

    def handlePlay(self):
        self.window.evaluate_js("window.handlePlay()")



a = AutomWrapper()
# if __name__ == '__main__':
#     api = Api()
#     with open("./gui/index.html") as gui_index_file:
#         # window = webview.create_window('AUTOM', html=gui_index_file.read(), js_api=api,width=320, height=480, resizable=False)
#         window = webview.create_window('AUTOM',"./gui/index.html", js_api=api,width=320, height=480, resizable=False)
#         webview.start(debug=True)