#!/usr/bin/python
# Copyright (c) 2013-2016 SUSE LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from tkinter import Tk, Canvas, NW, Button, Entry, Label
from PIL import Image, ImageTk
import json
import optparse
import sys
import shutil
from os.path import basename

import os, signal, time, atexit, copy

import shlex, subprocess
from UiArea import UiArea, Empty

help_text = """\n> python3 cropper.py --port 5901 --pid 16564  # it accesses your running qemu instance\n> # Or:\n> python3 cropper.py --test='qemu-system-x86_64 -hda tumbleweed.img --enable-kvm -display vnc=:1'\n> # start a qemu instance and access it. VNC has to be enabled"""
base_area = {'height': 80, 'type': 'match', 'xpos': 0, 'ypos': 0, 'width': 80, 'margin': 100}

global port         # integer after 5900
global p_qemu       # qemu instance
global p_vncviewer  # vncviewer
global p_vncdo      # vncdotool

global master       # Tk()

p_qemu = None       # initilized for cleanup
p_vncdo = None
p_vncviewer = None

# register clean up function to reap zombies
def cleanup():
    if p_vncdo:
        os.kill(p_vncdo.pid, signal.SIGTERM)
    if p_qemu:
        if options.pid:
            os.kill(p_qemu.pid, signal.SIGCONT)
        else:
            os.kill(p_qemu.pid, signal.SIGTERM)
    if p_vncviewer:
        os.kill(p_vncviewer.pid, signal.SIGTERM)
    # delete __tmp__.png
    subprocess.call(["rm", "__tmp__.png"])
    print("Cleaned up!")
     
atexit.register(cleanup)

import tkinter as tk
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()
        self.filename = ''
        self.tag = ''
        self.uiareas = []
        self.current_area = None
        self.current_area_id = 0
        self.paused = 0

    def create_widgets(self):
        # activate tk window for capture button
        self.b_capture = Button(self.master, text="Capture and Pause", command=self.capture)
        self.b_resume = Button(self.master, text='Resume Qemu', command=self.cont_p)
        self.b_save = Button(self.master, text='Save needle', command=self.saveneedle)
        self.b_capture.pack()
        self.b_resume.pack()
        self.b_save.pack()

        self.e_filename = Entry(self.master, width=100)
        self.e_filename.pack()
        self.e_filename.insert(0, "filename with .png suffix      e.g. zypper_up_yesno-20141115")

        self.e_tag = Entry(self.master, width=100)
        self.e_tag.pack()
        self.e_tag.insert(0, "tags splited with whitespace      e.g. test-zypper_up-confirm test-zypper_up-test")

        self.help_text = Label(master, text="1. Capture & Pause\n 2. <Insert> to add an area, arrow keys to move, shift-arrowkeys to resize, \n<Alt> to change area type, <Tab> switch between areas\n 3. enter filenames and tags\n4. click save needle or press <Esc> to quit without saving", width=400, justify='left')
        self.help_text.pack()

        self.master.title('Press <Esc> to exit')

        self.width = 1024
        self.height = 768

        self.caw = Canvas(master, width=self.width, height=self.height)
        self.caw.pack()
         
        self.__add_bindings()

    def delrect(self, arg=''):
        num = len(self.uiareas) 
        if num == 0:
            return
        self.uiareas[self.current_area_id].destroy()
        if num == 1:
            # Delete the only one rectangular
            self.uiareas = []
            self.current_area = None
            self.current_area_id = 0
        else:
            # remove from all areas
            del self.uiareas[self.current_area_id]
            # set current_area to be latest
            self.current_area_id = num - 2
            print("new current area id "+str(self.current_area_id))
            self.current_area = self.uiareas[self.current_area_id]

    def switch(self, arg):
        """
        # if area lastest
        #     switch to the first one
        # else # meaning we have switched before
        #     switch to area after current
        """

        if len(self.uiareas) == 0:
            return
        if len(self.uiareas)-1 == self.current_area_id:
            self.current_area = self.uiareas[0]
            self.current_area_id = 0
            print("current_area_id "+str(self.current_area_id))
        else:
            for i in range(0, len(self.uiareas)-1):
                # print("LEN: "+str(len(self.uiareas)))
                if i == self.current_area_id:
                   self.current_area = self.uiareas[i+1]
                   self.current_area_id = i + 1
                   print("current_area_id "+str(self.current_area_id))
                   return

    def changetype(self, arg=''):
        if len(self.uiareas) == 0:
            return
        types = ('match', 'exclude', 'ocr')
        self.current_area.area['type'] = types[(types.index(self.current_area.area['type']) + 1) % len(types)]
        self.uiareas[self.current_area_id].updatetype(self.current_area.area)

    def resize(self, arg):
        width = self.width
        height = self.height
        area = self.current_area.area
        incr = 5

        if arg.keysym == 'Right':
            if width - area['xpos'] - area['width'] >= incr:
                area['width'] = area['width'] + incr
            elif area['width'] > incr:
                area['xpos'] = area['xpos'] + incr
                area['width'] = area['width'] - incr
        elif arg.keysym == 'Left':
            if area['width'] > incr:
                area['width'] = area['width'] - incr
        elif arg.keysym == 'Down':
            if height - area['ypos'] - area['height'] >= incr:
                area['height'] = area['height'] + incr
            elif area['height'] > incr:
                area['ypos'] = area['ypos'] + incr
                area['height'] = area['height'] - incr
        elif arg.keysym == 'Up':
            if area['height'] > incr:
                area['height'] = area['height'] - incr

        self.current_area.updatearea(area)

    def saveneedle(self):
        # for the moment there should be __tmp__.png in current directory
        # if not, alert `please capture needle`
        try:
            f = open("__tmp__.png", 'r')
        except FileNotFoundError:
            print("Alert: please capture needle")
            return
        # Rename __tmp__.png to be the needle filename
        self.filename = self.e_filename.get()
        self.tag = self.e_tag.get()
        if self.__check_legal() == None:
            print("Alert: illegal filename or tags")
            return
        subprocess.call(["cp", "__tmp__.png", "needles/"+self.filename])
        self.__dumpjson()
        # reset text in entry button
        self.__savetext()

    def quit(self, args):
        print("Quit without saving")
        master.quit()

    def move(self, arg):
        width = self.width
        height = self.height
        area = copy.deepcopy(self.current_area.area)
        #for i in range(0, len(self.uiareas)):
        #    print("ID: "+str(i)+" ")
        #    print(self.uiareas[i].area)
        incr = 5

        if arg.keysym == 'Right':
            if width - area['xpos'] - area['width'] >= incr:
                area['xpos'] = area['xpos'] + incr
        elif arg.keysym == 'Left':
            if area['xpos'] >= incr:
                area['xpos'] = area['xpos'] - incr
        elif arg.keysym == 'Down':
            if height - area['ypos'] - area['height'] >= incr:
                area['ypos'] = area['ypos'] + incr
        elif arg.keysym == 'Up':
            if area['ypos'] >= incr:
                area['ypos'] = area['ypos'] - incr
        self.current_area.updatearea(area)

    def addrect(self, args):
        area = copy.deepcopy(base_area)
        self.uiareas.append(UiArea(self.caw, area))
        # Current focus on latest area
        self.current_area = self.uiareas[len(self.uiareas)-1]
        self.current_area_id = len(self.uiareas) - 1
        self.__selectarea()
        # update position of new rect
        self.current_area.updatearea(area)

    def capture(self):
        # return if already paused
        if self.paused == 1:
            return
        else:
            self.paused = 1
        # else
        # capture
        self.__capture()
        # stop qemu instance
        self.pause_p('')
        # update background img
        image = Image.open('__tmp__.png')
        photo = ImageTk.PhotoImage(image)
        self.bg = self.caw.create_image(0, 0, anchor=NW, image=photo)
        self.caw.draw()
        self.master.update()

    def pause_p(self, arg=''):
        print("PAUSE")
        # pause vm
        os.kill(p_qemu.pid, signal.SIGSTOP)

    def cont_p(self, arg=''):
        print("CONTINUED")
        self.paused = 0
        os.kill(p_qemu.pid, signal.SIGCONT)

    def __savetext(self):
        self.e_filename.delete(0, len(self.filename))
        self.e_tag.delete(0, len(self.tag))
        self.tag = ''
        self.filename = ''

    def __capture(self):
        print('CAPTURE')
        port_str = str(port)
        if port < 10:
            port_str = '0'+port_str
        commandline = "vncdotool -s 127.0.0.1::59"+port_str+" capture __tmp__.png"
        capture_args = shlex.split(commandline)
        p_vncdo = subprocess.Popen(capture_args)
        p_vncdo.wait()

    def __dumpjson(self):
        #    needle = json.loads("""{
        #        "tags": [ "EXAMPLE" ],
        #        "area": [ { "height": 100, "width": 100,
        #        "xpos": 0, "ypos": 0, "type": "match" } ]
        #    }""")

        # parse tags, possibly have multiple tags
        needle = {}
        # add tags
        tags = self.tag.split()
        needle['tags'] = tags 
        # add areas
        if len(self.uiareas) == 0:
            print("Alert: no area selected")
            return
        areas = []
        for i in self.uiareas:
            areas.append(i.area)
        needle['area'] = areas

        # Dump json to filename.json
        json_filename = ''
        if '.png' in self.filename:
            json_filename = "needles/"+self.filename[:len(self.filename)-4]+".json"
        else:
            json_filename = "needles/"+self.filename+".json"
        f = open(json_filename, "w")
        # print(json.dumps(needle, sort_keys=True, indent=4, separators=(',', ': ')))
        f.write(json.dumps(needle, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()

    def __check_legal(self):
        # check if filename and tags are legal
        if len(self.tag) == 0:
            return None
        if len(self.filename) == 0:
            return None
        return 1

    def __selectarea(self):
        for r in range(0, len(self.uiareas)):
            color = "green"
            #if r == rect:
            #    color = "cyan"
            self.uiareas[r].setcolor(color)

    def __add_bindings(self):
        self.master.bind('<Escape>', self.quit)
        self.master.bind('<Alt_L>', self.changetype)
        self.master.bind('<Insert>', self.addrect)
        self.master.bind('<Up>', self.move)
        self.master.bind('<Down>', self.move)
        self.master.bind('<Left>', self.move)
        self.master.bind('<Right>', self.move)
        self.master.bind('<Shift-Up>', self.resize)
        self.master.bind('<Shift-Down>', self.resize)
        self.master.bind('<Shift-Left>', self.resize)
        self.master.bind('<Shift-Right>', self.resize)        
        self.master.bind('<Tab>', self.switch)
        self.master.bind('<Delete>', self.delrect)

if __name__ == '__main__':
    parser = optparse.OptionParser(usage=help_text)
    parser.add_option("--port", metavar="NAME", help="port number")
    parser.add_option("--pid", metavar="NAME", help="pid number")
    parser.add_option("--test", metavar="NAME", help="--test=<command for creating qemu instance>")
    (options, args) = parser.parse_args()

    # either port or test has to be specified
    if not options.test:
         if not options.port:
             print(help_text)
             exit(1)

    # check port validity
    if options.port:
         if int(options.port) <= 5900:
             print("VNC port should be more than 5900")
             exit(1)
         else:
             port = int(str(options.port)[2:])
         if options.pid:
             p_qemu = Empty(int(options.pid))
         else:
             print("Please specify pid")
             print(help_text)

    if options.test:
        # start a new qemu instance
        # open qemu log file
        err_file = open("qemu_stderr.log", "wb")
        out_file = open("qemu_stdout.log", "wb")
        # Start qemu vm
        commandline = options.test
        qemu_args = shlex.split(commandline)
        if '-display' in qemu_args:
            has_vnc = 0
            for i in enumerate(qemu_args):
                if 'vnc=:' in i[1]:
                    port = int(i[1][5:])
                    if port >= 1:
                        has_vnc = 1
            if has_vnc != 1:
                print("Please use vnc to start qemu instance")
                print(help_text)
                exit(1)
        else:
            # Did not enable vnc
            print(help_text)
            exit(1)    
        p_qemu = subprocess.Popen(qemu_args, stdout=out_file, stderr=err_file)
      
    # sleep for qemu to start at port
    time.sleep(1)
    err_vnc = open("log/vncviewer_stderr.log", "wb")
    out_vnc = open("log/vncviewer_stdout.log", "wb")
    port_str = str(port)
    if port < 10:
        port_str = "0"+port_str
    commandline_viewer = "vncviewer -Shared :59"+port_str
    vncviewer_args = shlex.split(commandline_viewer)
    p_vncviewer = subprocess.Popen(vncviewer_args, stdout=out_vnc, stderr=err_vnc)

    master = Tk()
    app = Application(master)
    app.mainloop()

