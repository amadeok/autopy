import ctypes
import datetime, pygetwindow as gw
import pyperclip, random
import os, sys, time, argparse, mss, pyautogui, serial, subprocess as sp
import logging, monitor_scaling
from collections import namedtuple
if os.name != "posix":
    import win32gui, win32ui, win32con, numpy
    import win32pipe, threading, win32api, win32file
from PIL import Image

pil_logger = logging.getLogger('PIL')
pil_logger.setLevel(logging.INFO)
log_to_file = False
import pyscreeze

pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = False

if log_to_file:
    logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(message)s', level=level)
else: 
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

class fun_delegate():
    def __init__(self, fun, args : list, interval) -> None:
        self.fun = fun
        self.args = args
        self.interval = interval
        self.prev_time = time.time()
    
    def exec(self):
        if len(self.args) >5: raise Exception("Too many arguments for fun_delegate: > 5")

        cur_time = time.time()
        d = cur_time - self.prev_time 
        if  d > self.interval:        
            self.prev_time  = time.time() 

            if len(self.args) == 0: self.fun()
            elif len(self.args) == 1: self.fun(self.args[0])
            elif len(self.args) == 2: self.fun(self.args[0], self.args[1])
            elif len(self.args) == 3: self.fun(self.args[0], self.args[1], self.args[2])
            elif len(self.args) == 4:  self.fun(self.args[0], self.args[1], self.args[2], self.args[3])                                                                      
            elif len(self.args) == 5:  self.fun(self.args[0], self.args[1], self.args[2], self.args[3],  self.args[4])       
      
      
import subprocess
import json
import sys

def get_monitor_scalings():
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "monitor_scaling.py") ],
            #capture_output=True,
            text=True,
            timeout=1  # seconds
        )
        if result.returncode != 0:
            raise RuntimeError(f"Subprocess failed: {result.stderr}")
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error getting monitor scalings: {e}")
        return []
# 
# # Example usage
# scalings = get_monitor_scalings()
# for m in scalings:
#     print(f"Monitor {m['rect']['left']},{m['rect']['top']}: {m['scaling']:.2f}x ({int(m['scaling']*100)}%)")
#     

                                                                     

#from avee_utils import is_avee_running
def adb_output(cmd):
    device = "emulator-5554"

    base = f"adb  -s {device} shell "

    process = sp.Popen(base + cmd,
                        shell=True,
                           stdout=sp.PIPE, 
                           stderr=sp.PIPE)

    out, err = process.communicate()
    errcode = process.returncode
    return out if len(out) else err

def is_avee_running():
    ret =  adb_output(f"pidof com.daaw.avee")
    if ret != b'':
        return True
    return False

    
class image:
    def __init__(self, c, name, conf, base_path):
        self.name = name
        self.r = c.default_region
        self.rs = None
        self.conf = conf
        self.first = 1
        self.click_area = None
        self.basename = name.split('.png')[0]
        if sys.platform == 'win32':
            sep = "\\"
        else:
            sep = "/"
        try:
            self.obj = Image.open(base_path + sep + self.name).convert('RGB')
        except Exception as e:
            logging.error(f"Failed to load file {e}")
        self.found = False
        self.prev_time = 0
    @property
    def coors(self):
        return self.found[:2] if self.found else None
class imgs:
    def __init__(self, ctx, path, prefix):
        file_list = os.listdir(path if path is not None else 'imgs/') #os.listdir('imgs/')
        self.base_path = path
        self.dict = {}
        for file in file_list:
            if not ".png" in file:
                continue
            basename = file.split('.png')[0]
            img = image(ctx, file, 0.8, self.base_path)
            self.dict[basename] = img
            setattr(self, basename, img)
            if len(prefix):
                basename2 = basename.split(prefix)
                if len(basename2) > 1:
                    setattr(self, basename2[1], img)

        


def background_screenshot(hwnd, width, height, save_file=False):
    #t0 = time.time#pop()
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj=win32ui.CreateDCFromHandle(wDC)
    cDC=dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, width, height) #1020 - 960
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0,0),(width, height) , dcObj, (0,0), win32con.SRCCOPY)
   # print(time.time() - t0)
    #dataBitMap.SaveBitmapFile(cDC, 'screenshot2.bmp')

    bmpinfo = dataBitMap.GetInfo()
    bmparray = numpy.asarray(dataBitMap.GetBitmapBits(), dtype=numpy.int8)
    pil_im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmparray, 'raw', 'BGRX', 0, 1)
    pil_im = pil_im.crop((0, 52, width, height))
    
    if save_file:
        pil_im.save("test.png")
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())
    return pil_im
    #haystackImage =    Image.frombytes('RGB', sct_img.size, sct_img.rgb)

def mss_locate(obj, ctx , confidence=None, region=None, grayscale=True,  center=True):
    ctx : autopy = ctx
    if region == None:
       # res = pyautogui.size()
        region = ctx.default_region #[0, 0, res[0], res[1]]
    if confidence== None: 
        confidence = obj.conf
    ctx.rlog(f"mss_locate {obj.name}, {region}")

    r = {"top": int(region[1]), "left": int(region[0]),  "width": int(region[2]), "height": int(region[3])} 

    if not ctx.ext_src:
        with mss.mss() as sct:
            sct_img = sct.grab(r) 
            haystackImage =    Image.frombytes('RGB', sct_img.size, sct_img.rgb)
    elif type(ctx.ext_src) == int:
        haystackImage = background_screenshot(ctx.ext_src, region[2], region[3])
    elif ctx.ext_src == "phone":
        haystackImage = receive_screen_shot_from_phone(ctx)


    # if confidence == 0.99:
    #haystackImage.save('test.bmp')
    # if grayscale: gray = grayscale
    # else: gray = ctx.locate_grayscale
    found = pyautogui.locate(obj.obj, haystackImage, confidence=confidence, grayscale=grayscale)

    #t()
    if center and found:
        found0 = (found[0]+ found[2]/2 + r['left'], found[1] + found[3] /2 + r['top'], obj.obj.width, obj.obj.height)# r['width'], r['height'])
    elif found:
        found0 = (found[0]+ r['left'], found[1] + r['top'], obj.obj.width, obj.obj.height)#r['width'], r['height'])
    else:
        return None
    return  found0

def check_timeout2(ctx, sec, pt):
    curr_time = time.time()
    d = curr_time - pt#ctx.prev_time
    ctx.rlog(f"checking timeout, delta: {d}")

    if d > sec:
        ctx.rlog(f"timeout reached, delta: {d}")

        return 0
    return 1

from io import BytesIO

def start_screen_cap(dev = "ce041714f506223101"):
    time.sleep(0.01)
    print("starting phone screencap")
    os.system(f"adb -s {dev} exec-out screencap -p >" +  r"\\.\pipe\dain_a_id")


def receive_screen_shot_from_phone(ctx=None, save_file=False, dev="ce041714f506223101"):
    output_pipe =  r'\\.\pipe\dain_a_id' 
    arr = ctx.ext_src_buffer if ctx else  bytearray(1080*1920*3)

    mode = win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT
    fd0 = win32pipe.CreateNamedPipe( output_pipe, win32pipe.PIPE_ACCESS_DUPLEX, mode, 1, 65536, 65536, 0, None)
    t = threading.Thread(target=lambda: start_screen_cap(dev), args=())
    t.start()
    #sp.Popen(["adb", "-s", "ce041714f506223101", "exec-out", "screencap", "-p", ">",  "\\.\pipe\dain_a_id"])
    print("connecting to pipe")
    ret = win32pipe.ConnectNamedPipe(fd0, None)

    if ret != 0:
        print("error fd0", win32api.GetLastError())
    print(f'Python capture ID : Output pipe opened')
    t0 = time.time()

    tot_data = b''
    pos = 0
    buffer_size= 20480
    t0 = time.time()
    while 1:
        try:
            data = win32file.ReadFile(fd0, buffer_size) #w*h*s
        except:
            break
        lenght_read = len(data[1])
        arr[pos:pos+lenght_read] = data[1]
        pos+=lenght_read
        #tot_data+=data[1]
        if not data:
            break
    
    f = BytesIO(arr[0:pos])
    pil_im = Image.open(f)
    #pil_im = Image.frombuffer('RGB', (1080, 2220, ctx.ext_src_buffer[0:len(pos)], 'raw', 'BGRX', 0, 1)
    # print(time.time() -t0)
    if save_file:
        with open("f.png", "wb") as f_o:
            f_o.write(arr[0:pos])
    return pil_im

def get_quadrant(quadrant_str):
    size = pyautogui.size()
    w = size.width // 2
    h = size.height // 2
    
    if quadrant_str == "tl":  # Top-left
        return [0, 0, w, h]
    elif quadrant_str == "tr":  # Top-right
        return [w, 0, w, h]
    elif quadrant_str == "bl":  # Bottom-left
        return [0, h, w, h]
    elif quadrant_str == "br":  # Bottom-right
        return [w, h, w, h]
    else:
        raise ValueError("Invalid quadrant string. Use 'tl', 'tr', 'bl', or 'br'.")
    
class autopy:
    def __init__(self, imgs_path, ext_src=None, img_prefix="", use_arduino_click=None, rand_click_area=0, default_click_fun=pyautogui.click):
        self.imgs_path = imgs_path
        self.find_fun_timeout = 15
        self.default_confidence = 0.8
        self.prev_time = time.time()
        self.screen_res = pyautogui.size()
        self.default_region = [0, 0, self.screen_res.width, self.screen_res.height]
        self.stop_t = False
        self.i = imgs(self, imgs_path, img_prefix)
        self.ext_src = ext_src
        self.ext_src_buffer = None
        self.conn = None
        self.store_first = False
        self.ard_click = use_arduino_click
        self.rand_click_area = rand_click_area # from 0 to 1
        self.default_click_function = default_click_fun
        assert self.rand_click_area >= 0 and self.rand_click_area <= 1
        
#         DPI_AWARENESS_CONTEXT_SYSTEM_AWARE = -1  # from windef.h
#         user32 = ctypes.windll.user32
# 
#         if hasattr(user32, "SetProcessDpiAwarenessContext"):
#             user32.SetProcessDpiAwarenessContext.argtypes = [wintypes.HANDLE]
#             user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL
# 
#             success = user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_SYSTEM_AWARE)
#             if success != 0:
#                 raise ctypes.WinError()
#         else:
#             user32.SetProcessDPIAware()
# 
#         dpi = ctypes.windll.user32.GetDpiForSystem()
#         self.dip_scaling = dpi / 96.0
#         print(f"System DPI: {dpi}")
#         print(f"Scaling factor: {self.dip_scaling:.2f}x ({self.dip_scaling * 100:.0f}%)")
        
    def update_def_region(self, handle):
        self.default_region = [handle.left, handle.top, handle.width, handle.height]
        #r = {"top": region[1], "left": region[0],  "width": region[2], "height": region[3]}

    def proc_found(self, p, apply_scaling):
        
        # if apply_scaling and self.dip_scaling != 1:
        #     p[0] = round(p[0]*self.dip_scaling)
        #     p[1] = round(p[1]*self.dip_scaling)
            
        if self.rand_click_area:
            tpx = int((p[2] - p[2]//2) * self.rand_click_area)
            tpy = int((p[3] - p[3]//2) * self.rand_click_area)
            rx = [-tpx, tpx]
            ry = [-tpy, tpy]
            rp = (random.randrange(rx[0], rx[1]), random.randrange(ry[0], ry[1]))
            rp2 = [p[0]+rp[0], p[1]+rp[1], p[2], p[3]]
            return rp2
        else:
            return p
    def handle_click(self, click_function, click, obj, apply_scaling): #obj_l[x]
        coors__ = self.proc_found(list(obj.found), apply_scaling)
        if type(click_function) == list:
            click_function[0](coors__, click_function[1], click_function[2]) 
        elif click_function:
            click_function(*(coors__[:2]))
        elif click:
            # if click == 'popups':
            #     ob = getattr(ctx.i, ctx.pop_up_dict[obj_l[x].basename])
            #     find(ob, ctx, click=2, store_first=2, region=None)
            # else:
                #sct_bmp(obj_l[x].found, ctx)
            # if self.mouse_move(coors__, 0, 0):return -1 #(obj.found[0], obj.found[1])
            # pyautogui.click()
            self.default_click_function(*(coors__[:2]))
                        
    def rlog(self, str_, conn=None,  level=logging.DEBUG):
        str_ = str(str_)
        logging.log(level, str_)
        con = conn if conn else self.conn

        if con:
            now  = datetime.datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            network.send_string("[REMOTE]: " +  dt_string + ": " +  str_, con)

    def init_arduino(reset_arduino):
        while 1:
            try:

                port = f'COM{n}'
                self.ard = serial.Serial(port=port, baudrate=115200, timeout=1000)
                ctx.rlog(f"Found port {port}")
                break
            except: 
                n+=1
                if n == 100:
                    ctx.rlog("arduino port not found")
                    print("arduino port not found")
                    sys.exit()


    def mouse_move(self, point, x_of, y_of):
        self.rlog(f"moving mouse  {point[0] + x_of},  {point[1] + y_of}")
        if (self.stop_t):  return -1
        pyautogui.moveTo(point[0] + x_of, point[1] + y_of) 

    def click(self, point, x_of=0, y_of=0,  right=False) :
        self.rlog(f"clicking  {point[0] + x_of},  {point[1] + y_of}")
        if (self.stop_t):  return -1

        pyautogui.moveTo(point[0] + x_of, point[1] + y_of) 
        if right:
            pyautogui.click(button='right')  
        else:
            pyautogui.click() 

    def scroll(self, amount):
        self.rlog(f"scrolling  {amount}")
        if (self.stop_t):  return -1
        pyautogui.scroll(amount)

    def press(self, key):
        self.rlog(f"pressing {key}")
        if (self.stop_t):  return -1
        pyautogui.press(key)

    def _workaround_write(self, text):
        self.rlog(f"typing  {text}")

        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        pyperclip.copy('')
        
    def type(self, text, interval_=0):
        self.rlog(f"typing  {text}")
        if (self.stop_t):  return -1
        # if app_logging.ubuntu_ver == "20.04" and 0:
        #     sendSequence(text)
        # else:
        pyautogui.write(text, interval=interval_)

    def find(self, obj_l, loop=-1,  timeout=None, confidence=None, region=None, do_until =None, 
             grayscale=True,  center=True, click=False, store_first=None, check_avee_running=False, 
             timeout_exception=True, click_function=None, apply_scaling=False):
        # if do_until and type(do_until) != fun_delegate: raise Exception("Wrong fun_delegate type")
        
        if type(region) == str:
            region = get_quadrant(region)
        elif type(region) == gw.Window:
            region = [region.left, region.top, region.width, region.height ]
        store_first = self.store_first
        
        confidence = confidence if confidence else self.default_confidence
        timeout = timeout if timeout else self.find_fun_timeout
        
        #if timeout:  
        prev_time = time.time()
        
        if not isinstance(obj_l, list):
            obj_l = [obj_l]
        for ob in obj_l:
            
            if type(ob) == str and hasattr(self.i, ob): 
                str_o = ob[:]
                ob = getattr(self.i, ob)
                
                additional_objs = []
                counter = 2#2 if obj_l[0].basename.endswith("1")  else 1
                while True:
                    attr_name = f"{ob.basename}{counter}"
                    if hasattr(self.i, attr_name):
                        additional_objs.append(getattr(self.i, attr_name))
                        counter += 1
                    else:
                        break
                obj_l[obj_l.index(str_o)] = ob
                obj_l += additional_objs
        

        if do_until and not isinstance(do_until, list):
            do_until = [do_until]

        for i in obj_l:
            i.found = None

        def set_region(r, center):
            
            if not center:
                r =  [int(r[0]-10), int(r[1]- 10), r[2]+20, r[3]+20]
                return r

            else:
                r = [int(r[0]- r[2]/2), int(r[1]- r[3]/2), r[2], r[3]]
                r =  [int(r[0]-10), int(r[1]- 10), r[2]+20, r[3]+20]
                return r
                

        def find_partial_(confidence, region, grayscale, center):
            for x in range (len(obj_l)):

                if not region:
                    if store_first == 1:
                        if obj_l[x].rs == None:
                            region = self.default_region
                        else: 
                            region = obj_l[x].rs
                            #region = correct_region(obj_l[x].basename, obj_l[x].rs)

                cur_conf= confidence if confidence else obj_l[x].conf

                obj_l[x].found = mss_locate(obj_l[x], self, confidence=cur_conf, region=region, grayscale=grayscale, center=center)

                if obj_l[x].found: 
                    if store_first == 1:
                        if obj_l[x].rs == None:
                            obj_l[x].rs = set_region(obj_l[x].found, center)

                    self.handle_click(click_function, click, obj_l[x], apply_scaling)

                    self.rlog(f"found  {obj_l[x].name}, {obj_l[x].found}")

                    return obj_l[x]#, obj_l[x].found 
            return None

        if loop >= 0:
            while 1:
                if check_avee_running:
                    if not is_avee_running():
                        raise Exception("Trying to find an image in ldplayer while avee  is not running, image:" + str([elem.name for elem in obj_l]))
                found  = find_partial_(confidence, region, grayscale, center)
                if found: 
                    return found 
                if self.stop_t: timeout = 1
                if timeout:
                    if not check_timeout2(self, timeout, prev_time):
                        if timeout_exception: 
                            raise Exception(timeout_exception if type(timeout_exception) == str else "Critical image not found: " 
                                            + " || images: " + str([e.name + " " for e in  obj_l]))
                        return None
                if do_until:
                    for del_ in do_until:
                        if callable(del_):  del_()
                        else: del_.exec()
                time.sleep(loop)
        else:
            found  = find_partial_(confidence, region, grayscale, center)
            if found: return found 
            
        return None


    def wait_to_go(self, obj, region=None, confidence=None, timeout=None, sleep=0.01, timeout_exception=None, do_while=None):
        #if timeout:
        prev_time = time.time()
        found = 1
        while found:
            if self.stop_t: 
                #end_events(ctx); 
                return -1
            if not type(obj) == list:
                obj = [obj]
            for o in obj:
                found = self.find(obj, region=region, confidence=confidence)
                if found:
                    break
            if not found:
                logging.debug(f"wait_to_go object gone {found}")
                break
            if timeout:
                if not check_timeout2(self, timeout, prev_time):
                    if timeout_exception: 
                        raise Exception(timeout_exception if type(timeout_exception) == str else "Critical image not found: " + " || image: " + str(obj.name))
                    return None
            if do_while and found:
                do_while()
            time.sleep(sleep)

        return 1
     

