import os, sys, time, argparse, mss, pyautogui
import logging
from PIL import Image


pil_logger = logging.getLogger('PIL')
pil_logger.setLevel(logging.INFO)
log_to_file = False

if log_to_file:
    logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(message)s', level=level)
else: 
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
    
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
        self.obj = Image.open(base_path + sep + self.name).convert('RGB')
        self.found = False

class imgs:
    def __init__(self, ctx, path):
        file_list = os.listdir(path if path is not None else 'imgs/') #os.listdir('imgs/')
        self.base_path = path
        for file in file_list:
            basename = file.split('.png')[0]
            setattr(self, basename, image(ctx, file, 0.8, self.base_path))


def mss_locate(obj, ctx, confidence=None, region=None, grayscale=True,  center=True):
    if region == None:
       # res = pyautogui.size()
        region = ctx.default_region #[0, 0, res[0], res[1]]
    if confidence== None: 
        confidence = obj.conf
    logging.debug(f"mss_locate {obj.name}, {region}")

    r = {"top": region[1], "left": region[0],  "width": region[2], "height": region[3]} 

    with mss.mss() as sct:
        sct_img = sct.grab(r) 

    haystackImage =    Image.frombytes('RGB', sct_img.size, sct_img.rgb)
    # if confidence == 0.99:
    #haystackImage.save('test.bmp')
    if grayscale: gray = grayscale
    else: gray = ctx.locate_grayscale
    found = pyautogui.locate(obj.obj, haystackImage, confidence=confidence, grayscale=gray)

    #t()
    if center and found:
        found0 = (found[0]+ found[2]/2 + r['left'], found[1] + found[3] /2 + r['top'], obj.obj.width, obj.obj.height)# r['width'], r['height'])
    elif found:
        found0 = (found[0]+ r['left'], found[1] + r['top'], obj.obj.width, obj.obj.height)#r['width'], r['height'])
    else:
        return None
    return found0

def check_timeout2(ctx, sec):
    curr_time = time.time()
    d = curr_time - ctx.prev_time
    logging.debug(f"checking timeout, delta: {d}")

    if d > sec:
        logging.debug(f"timeout reached, delta: {d}")

        return 0
    return 1



class autopy:
    def __init__(self, imgs_path):
        self.imgs_path = imgs_path
        self.find_fun_timeout = 15
        self.prev_time = time.time()
        self.screen_res = pyautogui.size()
        self.default_region = [0, 0, self.screen_res.width, self.screen_res.height]
        self.stop_t = False
        self.i = imgs(self, imgs_path)
        

    def init_arduino(reset_arduino):
        while 1:
            try:

                port = f'COM{n}'
                self.ard = serial.Serial(port=port, baudrate=115200, timeout=1000)
                logging.info(f"Found port {port}")
                break
            except: 
                n+=1
                if n == 100:
                    logging.info("arduino port not found")
                    print("arduino port not found")
                    sys.exit()


    def mouse_move(self, point, x_of, y_of):
        logging.debug(f"moving mouse  {point[0] + x_of},  {point[1] + y_of}")
        if (self.stop_t):  return -1
        pyautogui.moveTo(point[0] + x_of, point[1] + y_of) 

    def click(self, point, x_of, y_of,  right=False) :
        logging.debug(f"clicking  {point[0] + x_of},  {point[1] + y_of}")
        if (self.stop_t):  return -1

        pyautogui.moveTo(point[0] + x_of, point[1] + y_of) 
        if right:
            pyautogui.click(button='right')  
        else:
            pyautogui.click() 

    def press(self, key):
        logging.debug(f"pressing {key}")
        if (self.stop_t):  return -1
        pyautogui.press(key)

    def type(self, text, interval_=0):
        logging.debug(f"typing  {text}")
        if (self.stop_t):  return -1
        pyautogui.write(text, interval=interval_)

    def find(self, obj_l, loop=-1, search_all=None, timeout=None, confidence=None, region=None, grayscale=True,  center=True, click=False, store_first=True):
        
        if timeout == None: 
            timeout = self.find_fun_timeout
        if timeout:  
            self.prev_time = time.time()
        
        if not isinstance(obj_l, list):
            obj_l = [obj_l]
        #found_l = [None for x in range(len(obj_l))]
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

                if obj_l[x].name == 'email_senza_pass.png':
                    c = 0
                    
                if not region:
                    if store_first == 1:
                        if obj_l[x].rs == None:
                            region = self.default_region
                        else: 
                            region = obj_l[x].rs
                            #region = correct_region(obj_l[x].basename, obj_l[x].rs)


                #if check_names(obj_l[x].basename): region = ctx.ui.pop_ups_max
                #if check_names2(obj_l[x].basename): region = ctx.ui.region


                if not confidence: confidence = obj_l[x].conf

                obj_l[x].found = mss_locate(obj_l[x], self, confidence=confidence, region=region, grayscale=grayscale, center=center)

                if obj_l[x].found: 
                    if store_first == 1:
                        if obj_l[x].rs == None:
                            obj_l[x].rs = set_region(obj_l[x].found, center)

                    if click:
                        # if click == 'popups':
                        #     ob = getattr(ctx.i, ctx.pop_up_dict[obj_l[x].basename])
                        #     find(ob, ctx, click=2, store_first=2, region=None)
                        # else:
                            #sct_bmp(obj_l[x].found, ctx)
                        if self.mouse_move((obj_l[x].found[0], obj_l[x].found[1]), 0, 0):return -1
                        pyautogui.click() 

                    logging.debug(f"found  {obj_l[x].name}, {obj_l[x].found}")

                    return obj_l[x]#, obj_l[x].found 
            return None

        if loop >= 0:
            while 1:
                found  = find_partial_(confidence, region, grayscale, center)
                if found: 
                    return found 
                if self.stop_t: timeout = 1
                if timeout:
                    if not check_timeout2(self, timeout):
                        return None
                time.sleep(loop)
        else:
            found  = find_partial_(confidence, region, grayscale, center)
            if found: return found 
            
        return None


    def wait_to_go(self, obj, region=None, confidence=None, timeout=None, sleep=0.01):
        if timeout:
            self.prev_time = time.time()
        found = 1
        while found:
            if self.stop_t: 
                #end_events(ctx); 
                return -1
            found = self.find(obj, region=region, confidence=confidence)
            time.sleep(sleep)
            if timeout:
                if not check_timeout2(self, timeout):
                    return None
        return 1
     

