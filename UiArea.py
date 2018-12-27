import tkinter as tk
from tkinter import Tk, Canvas, NW, Button
from PIL import Image, ImageTk
import json
import optparse
import sys
import shutil
from os.path import basename

class UiArea:
    def __init__(self, w, area):
        self.color = "cyan"
        self.w = w
        self.area = area
        self.rect = w.create_rectangle(
            area['xpos'], area['ypos'],
            area['xpos'] + area['width'],
            area['ypos'] + area['height'],
            outline=self.color)
        self.text = w.create_text(area['xpos'] + area['width'], area['ypos'] + area['height'],
                                  anchor="se", text=area['type'],
                                  fill=self.color)
        self.line = None
        self._update_exclude(area)
        self.updatearea(area)

    def _update_exclude(self, area):
        if area['type'] == 'exclude' and self.line is None:
            self.line = w.create_line(
                area['xpos'],
                area['ypos'] + area['height'], area['xpos'] + area['width'],
                area['ypos'],
                fill=self.color)
        if area['type'] != 'exclude' and self.line is not None:
            self.w.delete(self.line)
            self.line = None
            
    def setcolor(self, color):
        self.color = color
        self.w.itemconfig(self.rect, outline=color)
        self.w.itemconfig(self.text, fill=color)
        if self.line is not None:
            self.w.itemconfig(self.line, fill=color)

    def updatearea(self, area):
        self.w.coords(self.rect, area['xpos'], area['ypos'],
                      area['xpos'] + area['width'],
                      area['ypos'] + area['height'])
        self.w.coords(self.text, area['xpos'] + area['width'], area['ypos'] + area['height'])
        if self.line:
            self.w.coords(self.line, area['xpos'], area['ypos'] + area['height'],
                          area['xpos'] + area['width'],
                          area['ypos'])
        self.area['xpos'] = area['xpos']
        self.area['ypos'] = area['ypos']
        self.area['width'] = area['width']
        self.area['height'] = area['height']

    def updatetype(self, area):
        self.w.itemconfig(self.text, text=area['type'])
        self._update_exclude(area)

    def destroy(self):
        self.w.delete(self.rect)
        self.w.delete(self.text)
        if self.line is not None:
            self.w.delete(self.line)

class Empty(object):
    def __init__(self, pid):
        self.pid = pid

