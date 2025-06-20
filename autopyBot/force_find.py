import json, pygetwindow as gw, PyHookCpp
import time,win32gui, threading
import my_utils.util_ as ut,pyautogui
import autopyBot.autopy as autopy

def add_json_methods(cls):    
    def to_json(self):
        serializable = {}
        for k, v in self.__dict__.items():
            try:
                json.dumps(v)  # Test if value is serializable
                serializable[k] = v
            except (TypeError, OverflowError):
                continue  # Skip non-serializable fields like 'app'
        return serializable
    
    @classmethod
    def from_json(cls, json_data, app=None):
        """Create an instance from JSON, with optional 'app' argument"""
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        return cls(app=app, **data)  
    cls.to_json = to_json
    cls.from_json = from_json
    return cls



@add_json_methods
class ForceForeTask():
    def __init__(self,  app, sub_win_title,  image_name, region_w_perc, region_h_perc, region_corner ):
        self._app :forceFinder = app
        # self.main_win_title = main_win_title
        self.sub_win_title = sub_win_title
        self.region_w_perc = region_w_perc
        self.region_h_perc = region_h_perc
        self.region_corner = region_corner
        self.image_name = image_name
        self.win = None
        self.rect = None
        self.image = getattr(self._app.at.i, self.image_name)
        self.thread = threading.Thread(target=lambda: 1)
        self.thread.start()
    
    def wait_for_win(self, delay=0.01, timeout=1):
        st = time.time()
        while not self.get_win():
            if time.time() - st > timeout:
                # print(f"Timeout {}")
                return False
            time.sleep(delay)
        print(f"""Found {time.time() - st:5.3f} "{self.win.title}" """)
        return True
        
    def async_exec(self):
        self.thread = threading.Thread(target=self.exec, daemon=True)
        self.thread.start()
        
    def exec(self):
        tt = ut.TimeTracker()
        tt.t("0")

        if self.get_win(): 
            print(f"""Window already open "{self.win.title}" """)
            return
        else:
            print(f"""Opening "{self.sub_win_title}" ...""")
        tt.t("1")

        tt.print_deltas()

        prev_pos = self._app.hook.cmd.get_position()
        self._app.hook.start_hook()
        self._app.hook.set_mouse_block(True)
        self.win = None
        win = self._app.main_win
        ut.remote_set_fore(win._hWnd, True) 
        tt.t("2")
        
        region = ut.get_window_region(win , self.region_w_perc, self.region_h_perc, self.region_corner)
        ut.move_windows_out_of_region(*region, only_always_on_top=True, parent_to_include_childs_of=win._hWnd,  exceptions=[])
        tt.t("3")
        st = time.time()
        while  not self.get_win():
            tt.t("4")
            self._app.at.find(self.image, region=region)
            tt.t("5")
            if self.image.found:
                self._app.hook.cmd.double_click("left", self.image.coors[0], self.image.coors[1], delay=0)
            tt.t("6")
            if self.wait_for_win():break
            if time.time() - st > 5:
                print(f"""timeout find() "{self.sub_win_title}"" """)
                break
            time.sleep(0.05)
        tt.t("7")
        self._app.hook.cmd.set_position(*prev_pos)
        self._app.hook.end_hook()
        self._app.hook.set_mouse_block(False)
        tt.t("8")
        tt.print_deltas()
        tt.print_deltas(["1", "8"])
        # print(f"Took {time.time() - st:5.3f}")
        
        
    def get_win(self):
        self.win = ut.get_first_hwnd_with_partial_titles(self.sub_win_title)
        return self.win


fft = ForceForeTask

class forceFinder():
    def __init__(self, path, main_win_title, aux_path="", class_=ForceForeTask):
        self.main_win_title = main_win_title
        self.aux_path = aux_path
        self.at = autopy.autopy(path)    
        self.tasks : list[class_] = []
        self.hook = PyHookCpp.InputHookController()
        self.cl = class_
        self.cons_win = []
        self.cons_pos = None


    @property
    def main_win(self):
        wins =  ut.get_handles_with_partial_title(self.main_win_title)
        return next((e for e in wins if self.aux_path in e[1]), None)[0] if wins and len(wins) else None
        return ut.get_first_hwnd_with_partial_titles(self.main_win_title)
    
    def get_cons_win(self):    
        if len(self.cons_win) and win32gui.IsWindow(self.cons_win[0]._hWnd): return 1
        self.cons_win = gw.getWindowsWithTitle("Console")
        return len(self.cons_win)
    
    def add(self, tasks):
        for t in tasks:
            t[0] = t[0].split(",")
            self.tasks.append(self.cl(self, *t))
        
    def force_get_cons(self):
        sl = 0.01
        win = self.main_win
        if not win: return None
        while not self.get_cons_win():
            ut.remote_set_fore(win._hWnd, True) 
            # self.write_cmd("show in console")
            pyautogui.hotkey("ctrl", "shiftright", "shiftleft", "alt", "pageup")#show in console
            print("1")
            time.sleep(sl)
            if self.get_cons_win():break
            time.sleep(sl)
            # self.write_cmd("toggle detach console")
            pyautogui.hotkey("ctrl", "f3")#toggle detach console
            print("2")
            time.sleep(sl)
            if self.get_cons_win():break
        
        cons_win  : gw.Window = self.cons_win[0]
        cons_win.resizeTo(450, 750)
        print("cons_win", cons_win._hWnd)
        return cons_win      
if __name__ == "__main__":
    ff = forceFinder(path=r"F:\all\GitHub\window_manager\imgs", main_win_title="Studio One -")
    
    keyscape2_r = [0.2, 0.4, "bottom-left"]
    main_r = [0.2, 0.4, "bottom-right"]
    ff.add(  
        [["UADx Fairchild 670 Compressor", "fairchild", *keyscape2_r ],
        ["UADx Pultec EQP", "pultec", *keyscape2_r ],
        [ "Keyscape,Youlean Loudness Meter 2", "keyscape_youlean", *keyscape2_r ],     
        [ "UADx Ampex", "ampex", *main_r ],          
        [ " - Ozone 10", "ozone10", *main_r ], 
        [ "Main,Youlean Loudness Meter 2", "main_youlean", *main_r ], 
        [ "soundid reference plug", "soundid", *main_r ]])
    
    for t in ff.tasks:
        t.exec()
    # region = ut.get_window_region(ff.main_win , ff.tasks[5].region_w_perc, ff.tasks[5].region_h_perc, ff.tasks[5].region_corner)

    print()