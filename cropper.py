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

from tkinter import Tk, Canvas, NW, Button, Entry
from PIL import Image, ImageTk
import json
import optparse
import sys
import shutil
from os.path import basename

import os, signal, time, atexit

import shlex, subprocess
from UiArea import UiArea, Empty

help_text = """\n> python3 cropper.py --port 5901 --pid 16564  # it accesses your running qemu instance\n> # Or:\n> python3 cropper.py --test='qemu-system-x86_64 -hda tumbleweed.img --enable-kvm -display vnc=:1'\n> # start a qemu instance and access it. VNC has to be enabled"""
base_area = {'height': 80, 'type': 'match', 'xpos': 0, 'ypos': 0, 'width': 80, 'margin': 100}

global port         # integer after 5900
global p_qemu       # qemu instance
global p_vncviewer  # vncviewer
global p_vncdo      # vncdotool

global master       # Tk()
global caw          # canvas

p_qemu = None       # initilized for cleanup
p_vncdo = None
p_vncviewer = None

# register clean up function to reap zombies
def cleanup():
    if p_vncdo:
        os.kill(p_vncdo.pid, signal.SIGTERM)
    if p_qemu:
        if options.pid:
            print("Don't kill qemu since it's started outside")
            os.kill(p_qemu.pid, signal.SIGCONT)
        else:
            os.kill(p_qemu.pid, signal.SIGTERM)
    if p_vncviewer:
        os.kill(p_vncviewer.pid, signal.SIGTERM)
    print("Cleaned up!")
     
atexit.register(cleanup)


# open new or and png file
#    needle = json.loads("""{
#        "tags": [ "FIXME" ],
#        "area": [ { "height": 100, "width": 100,
#        "xpos": 0, "ypos": 0, "type": "match" } ]
#    }""")

#print(json.dumps(needle, sort_keys=True, indent=4, separators=(',', ': ')))

"""
for area in needle['area']:
    # make sure we have ints
    for s in ('xpos', 'ypos', 'width', 'height'):
        area[s] = int(area[s])
    uiareas.append(UiArea(w, area))

rect = 0

selectarea()
incr = 5
"""

"""
"""



"""
from UiArea import UiArea

def delrect(arg):
    global rect, area, uiareas, needle
    if len(uiareas) <= 1:
        return
    del needle['area'][rect]
    uiareas[rect].destroy()
    a = []
    for r in range(0, len(uiareas)):
        if r == rect:
            continue
        a.append(uiareas[r])
    uiareas = a
    rect = rect % len(uiareas)
    selectarea()


def changetype(arg):
    types = ('match', 'exclude', 'ocr')
    global rect, area, uiareas, needle
    area['type'] = types[(types.index(area['type']) + 1) % len(types)]
    uiareas[rect].updatetype(area)

def save_quit(arg):
    global filename
    if options.new:
        from os import environ
        if 'CASEDIR' not in environ:
            environ['CASEDIR'] = 'distri/opensuse'
        pat = environ['CASEDIR'] + "/needles/%s.%s"
        shutil.copyfile(png, pat % (options.new, 'png'))
        filename = pat % (options.new, 'json')
    json.dump(needle, open(filename, 'w'), sort_keys=True, indent=4, separators=(',', ': '))
    print("saved %s" % filename)
    master.quit()

master.bind('<space>', pause)
master.bind('+', increment)
master.bind('-', increment)
master.bind('s', save_quit)
master.bind('q', quit)
master.bind('<Delete>', delrect)
master.bind('t', changetype)
"""


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

    def create_widgets(self):
        # activate tk window for capture button
        self.b_capture = Button(self.master, text="Capture", command=self.capture)
        self.b_capture.pack()
        self.b_readfilename = Button(self.master, text='Save filename', command=self.savetext)
        self.b_readfilename.pack()
        self.b_save = Button(self.master, text='Save needle', command=self.saveneedle)
        self.b_save.pack()

        self.e_filename = Entry(self.master, width=100)
        self.e_filename.pack()
        self.e_filename.insert(0, "filename without .png suffix      e.g. zypper_up_yesno-20141115")

        self.e_tag = Entry(self.master, width=100)
        self.e_tag.pack()
        self.e_tag.insert(0, "tags splited with whitespace      e.g. test-zypper_up-confirm test-zypper_up-test")

        self.master.title('p for stop and c for continue')

        self.width = 1024#photo.width()
        self.height = 768#photo.height()

        self.caw = Canvas(master, width=self.width, height=self.height)
        self.caw.pack()
         
        self.__add_bings()


    def switch(self, arg):
        """
        # if area lastest
        #     switch to the first one
        # else # meaning we have switched before
        #     switch to area after current
        """

        if len(self.uiareas)-1 == self.current_area_id:
            # print("LEN: "+str(len(self.uiareas)))
            self.current_area = self.uiareas[0]
            self.current_area_id = 0
        else:
            for i in range(0, len(self.uiareas)-1):
                # print("LEN: "+str(len(self.uiareas)))
                if i == self.current_area_id:
                   self.current_area = self.uiareas[i+1]
                   self.current_area_id = i + 1
                   return

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
        print("TODO: Save needle")

    def quit(self, args):
        print("quit without saving")
        # print(json.dumps(needle, sort_keys=True, indent=4, separators=(',', ': ')))
        master.quit()

    def move(self, arg):
        width = self.width
        height = self.height
        area = self.current_area.area
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
        """
        global rect, area, uiareas, needle
        rect = len(needle['area'])
        needle['area'].append({"height": 100, "width": 100,
                               "xpos": 0, "ypos": 0, "type": "match"})
        area = needle['area'][rect]
        """
        area = base_area
        self.uiareas.append(UiArea(self.caw, area))
        # Current focus on latest area
        self.current_area = self.uiareas[len(self.uiareas)-1]
        self.current_area_id = len(self.uiareas) - 1
        self.__selectarea()

    def savetext(self):
        self.filename = self.e_filename.get()
        print("Filename: "+self.filename+".png")
        self.tag = self.e_tag.get()
        print("tag: "+self.tag)
        self.e_filename.delete(0, len(self.filename))
        self.e_tag.delete(0, len(self.tag))
        self.__check_legal()

    def capture(self):
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
        # qemu instance resume
        self.cont_p('')

    def pause_p(self, arg):
        print("PAUSE")
        # pause vm
        os.kill(p_qemu.pid, signal.SIGSTOP)

    def cont_p(self, arg):
        print("CONTINUED")
        os.kill(p_qemu.pid, signal.SIGCONT)

    def __capture(self):
        print('CAPTURE')
        port_str = str(port)
        if port < 10:
            port_str = '0'+port_str
        commandline = "vncdotool -s 127.0.0.1::59"+port_str+" capture __tmp__.png"
        capture_args = shlex.split(commandline)
        p_vncdo = subprocess.Popen(capture_args)
        p_vncdo.wait()

    def __check_legal(self):
        # check if filename and tags are legal
        print("Checks passed on tags and filename")

    def __selectarea(self):
        for r in range(0, len(self.uiareas)):
            color = "green"
            #if r == rect:
            #    color = "cyan"
            self.uiareas[r].setcolor(color)

    def __add_bings(self):
        self.master.bind('p', self.pause_p)
        self.master.bind('c', self.cont_p)        
        self.master.bind('<Insert>', self.addrect)
        self.master.bind('<Escape>', self.quit)
        self.master.bind('<Up>', self.move)
        self.master.bind('<Down>', self.move)
        self.master.bind('<Left>', self.move)
        self.master.bind('<Right>', self.move)
        self.master.bind('<Shift-Up>', self.resize)
        self.master.bind('<Shift-Down>', self.resize)
        self.master.bind('<Shift-Left>', self.resize)
        self.master.bind('<Shift-Right>', self.resize)        
        self.master.bind('<Tab>', self.switch)


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
    err_vnc = open("vncviewer_stderr.log", "wb")
    out_vnc = open("vncviewer_stdout.log", "wb")
    port_str = str(port)
    if port < 10:
        port_str = "0"+port_str
    commandline_viewer = "vncviewer -Shared :59"+port_str
    vncviewer_args = shlex.split(commandline_viewer)
    p_vncviewer = subprocess.Popen(vncviewer_args, stdout=out_vnc, stderr=err_vnc)

    master = Tk()
    app = Application(master)
    app.mainloop()

