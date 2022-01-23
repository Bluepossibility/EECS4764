from PIL import Image, ImageTk
import tkinter as tk
import RPi.GPIO as GPIO
import requests
import time
import json
import cv2

weather_key = "8d5da1574033d2aeb3212b37cd3234a7"
map_http = 'https://www.google.com/maps/embed/v1/'
map_key = 'AIzaSyDVsu34HwY6IHeqaah5CLT_pMZbhgr9mQo'
height = 1080
width = 1920


def detect_display():
    root_detect = tk.Tk()
    root_detect.title("Detecting")
    root_detect.geometry("{0}x{1}".format(width, height))

    photo_detect = Image.open("/home/pi/Desktop/detect.jpeg")
    resize_detect = photo_detect.resize((width, height), Image.ANTIALIAS)
    convert_detect = ImageTk.PhotoImage(resize_detect)

    label = tk.Label(root_detect,
                     image=convert_detect,
                     width=width, height=height,
                     bg='black', fg='yellow')
    label.pack()
    root_detect.after(45000, lambda: root_detect.destroy())
    root_detect.mainloop()


def rotate_display():
    root_rotate = tk.Tk()
    root_rotate.title("Rotating")
    root_rotate.geometry("{0}x{1}".format(width, height))

    photo_rotate = Image.open("/home/pi/Desktop/rotate.jpeg")
    resize_rotate = photo_rotate.resize((width, height), Image.ANTIALIAS)
    convert_rotate = ImageTk.PhotoImage(resize_rotate)

    label = tk.Label(root_rotate,
                     image=convert_rotate,
                     width=width, height=height,
                     bg='black', fg='yellow')
    label.pack()
    # root_rotate.after(3000, lambda: root_rotate.destroy())
    root_rotate.mainloop()


def plastic_display():
    root_plastic = tk.Tk()
    root_plastic.title("Plastic Detected")
    root_plastic.geometry("{0}x{1}".format(width, height))

    photo_plastic = Image.open("/home/pi/Desktop/plastic.jpeg")
    resize_plastic = photo_plastic.resize((width, height), Image.ANTIALIAS)
    convert_plastic = ImageTk.PhotoImage(resize_plastic)

    label = tk.Label(root_plastic,
                     image=convert_plastic,
                     width=width, height=height,
                     bg='black', fg='yellow')
    label.pack()
    root_plastic.after(5000, lambda: root_plastic.destroy())
    root_plastic.mainloop()


def metal_display():
    root_metal = tk.Tk()
    root_metal.title("Metal Detected")
    root_metal.geometry("{0}x{1}".format(width, height))

    # photo_metal = tk.PhotoImage(file = "")
    photo_metal = Image.open("/home/pi/Desktop/metal.jpeg")
    resize_metal = photo_metal.resize((width, height), Image.ANTIALIAS)
    convert_metal = ImageTk.PhotoImage(resize_metal)

    label = tk.Label(root_metal,
                     image=convert_metal,
                     width=width, height=height,
                     bg='black', fg='yellow')
    root_metal.after(5000, lambda: root_metal.destroy())
    label.pack()
    root_metal.mainloop()


def paper_display():
    root_paper = tk.Tk()
    root_paper.title('Paper Detected')
    root_paper.geometry("{0}x{1}".format(width, height))

    photo_paper = Image.open("/home/pi/Desktop/paper.jpeg")
    resize_paper = photo_paper.resize((width, height), Image.ANTIALIAS)
    convert_paper = ImageTk.PhotoImage(resize_paper)

    label = tk.Label(root_paper,
                     image=convert_paper,
                     width=width, height=height,
                     bg='black', fg='yellow')
    root_paper.after(5000, lambda: root_paper.destroy())
    label.pack()
    root_paper.mainloop()


def trash_display():
    root_trash = tk.Tk()
    root_trash.title("Plastic Detected")
    root_trash.geometry("{0}x{1}".format(width, height))

    photo_trash = Image.open("/home/pi/Desktop/other.jpeg")
    resize_trash = photo_trash.resize((width, height), Image.ANTIALIAS)
    convert_trash = ImageTk.PhotoImage(resize_trash)

    label = tk.Label(root_trash,
                     image=convert_trash,
                     width=width, height=height,
                     bg='black', fg='yellow')
    label.pack()
    root_trash.after(5000, lambda: root_trash.destroy())
    root_trash.mainloop()


class Camera(object):
    def __init__(self, url='http://192.168.1.10:5000/'):
        self.text_flag = -1  # 用来是否添加文字
        self.start_time = time.time()
        self.counter = 0  # 用来算帧率
        self.url = url

    def initialize(self):
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 160)  # 好像我的摄像头最高支持的情况就是1280*720
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)

    def read(self, show=False):
        flag, picture = self.capture.read()  # flag是标志位，是否开启摄像头
        picture = cv2.flip(picture, 1)  # 图像翻转，1为水平（即向着行），0为竖直（即向着列）

        self.counter += 1  # 用来算帧率
        c = cv2.waitKey(1)  # 等待按键时间，50ms，如果没按就是0

        if c in [ord('q'), ord('Q')]:  # 选择按键
            print('开关fps')
            self.text_flag = -1 * self.text_flag

        if c == 27:
            return False  # use this to close camera

        if self.text_flag > 0:
            real_fps = self.counter / (time.time() - self.start_time)
            cv2.putText(picture, 'FPS: %.2f' % (real_fps), (10, 30), cv2.FONT_HERSHEY_DUPLEX, 1,
                        color=(200, 120, 255), lineType=3)
            self.counter, self.start_time = 0, time.time()
        if show: cv2.imshow('Imagetest', picture)

        return picture, True

    def get(self, picture):
        url = self.url + '/picture'
        picture = picture.tolist()
        response = requests.put(url, data=json.dumps(picture))
        return response.json()

    def send_volume(self, volume):
        url = self.url + '/volume'
        response = requests.put(url, data=json.dumps(volume))
        return response.json()

    def send_location(self, location):
        url = self.url + 'location'
        response = requests.put(url, data=json.dumps(location))

    def reset(self, id):
        url = self.url + 'reset'
        response = requests.put(url, data=json.dumps({id: 'trash can'}))
        return response.json()

    def close(self):
        self.capture.release()
        cv2.destroyAllWindows()


class API:
    def __init__(self, url, printf=0):
        self.url = url

    def linkUrl(self, url, parameters):
        url += '?'
        for k in parameters:
            url += k
            url += '='
            url += str(parameters[k])
            url += '&'
        return url[:-1]

    def post(self, parameters=None):
        url = self.url
        if parameters: url = self.linkUrl(url, parameters)
        response = requests.post(url)
        return response.json()

    def put(self, parameters=None):
        url = self.url
        response = requests.put(url, data=json.dumps(parameters))
        return response.json()


class NemaMotor(object):
    """class to control a Nema stepper motor with TB6612 controller
    by a raspberry pi"""

    def __init__(self, name="MyMotorOne", motor_type="Nema"):
        self.name = name
        self.motor_type = motor_type
        self.stop_motor = False

    def motor_stop(self):
        """ Stop the motor """
        self.stop_motor = True

    def motor_run(self, gpiopins, wait=.001, steps=512, ccwise=False,
                  verbose=False, steptype="half", initdelay=.001):
        """motor_run,  moves stepper motor based on 7 inputs
         (1) GPIOPins, type=list of ints 4 long, help="list of
         4 GPIO pins to connect to motor controller
         These are the four GPIO pins we will
         use to drive the stepper motor, in the order
         they are plugged into the controller board. So,
         GPIO 18 is plugged into Pin 1 on the stepper motor.
         (2) wait, type=float, default=0.001, help=Time to wait
         (in seconds) between steps.
         (3) steps, type=int, default=512, help=Number of steps sequence's
         to execute. Default is one revolution , 512 (for a 28BYJ-48)
         (4) counterclockwise, type=bool default=False
         help="Turn stepper counterclockwise"
         (5) verbose, type=bool  type=bool default=False
         help="Write pin actions",
         (6) steptype, type=string , default=half help= type of drive to
         step motor 3 options full step half step or wave drive
         where full = fullstep , half = half step , wave = wave drive.
         (7) initdelay, type=float, default=1mS, help= Intial delay after
         GPIO pins initialized but before motor is moved.
        """
        try:
            self.stop_motor = False
            for pin in gpiopins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, False)
            time.sleep(initdelay)

            # select step based on user input
            # Each step_sequence is a list containing GPIO pins that should be set to High
            if steptype == "half":  # half stepping.
                step_sequence = list(range(0, 8))
                step_sequence[0] = [gpiopins[0]]
                step_sequence[1] = [gpiopins[0], gpiopins[1]]
                step_sequence[2] = [gpiopins[1]]
                step_sequence[3] = [gpiopins[1], gpiopins[2]]
                step_sequence[4] = [gpiopins[2]]
                step_sequence[5] = [gpiopins[2], gpiopins[3]]
                step_sequence[6] = [gpiopins[3]]
                step_sequence[7] = [gpiopins[3], gpiopins[0]]
            elif steptype == "full":  # full stepping.
                step_sequence = list(range(0, 4))
                step_sequence[0] = [gpiopins[0], gpiopins[1]]
                step_sequence[1] = [gpiopins[1], gpiopins[2]]
                step_sequence[2] = [gpiopins[2], gpiopins[3]]
                step_sequence[3] = [gpiopins[0], gpiopins[3]]

            #  To run motor in reverse we flip the sequence order.
            if ccwise:
                step_sequence.reverse()

            def display_degree():
                """ display the degree value at end of run if verbose"""
                degree = 7.2
                print("Size of turn in degrees = {}".format(round(steps * degree, 2)))

            # Iterate through the pins turning them on and off.
            steps_remaining = steps
            while steps_remaining > 0:
                for pin_list in step_sequence:
                    for pin in gpiopins:
                        if self.stop_motor:
                            raise StopMotorInterrupt
                        else:
                            if pin in pin_list:
                                GPIO.output(pin, True)
                            else:
                                GPIO.output(pin, False)
                    time.sleep(wait)
                steps_remaining -= 1

        except KeyboardInterrupt:
            print("User Keyboard Interrupt : RpiMotorLib: ")
        except StopMotorInterrupt:
            print("Stop Motor Interrupt : RpiMotorLib: ")
        except Exception as motor_error:
            print(motor_error)
            print("RpiMotorLib  : Unexpected error:")

        finally:
            # switch off pins at end
            for pin in gpiopins:
                GPIO.output(pin, False)




