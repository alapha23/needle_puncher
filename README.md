Needle Puncher for openQA
===

Summary
---

Installation
---

This program replies on vncdotool, tkinter, PIL, json and other libraries.
It is suggested to be used under virtualenv. 

#### Set up environment
```
virtualenv --python=/usr/bin/python3 mydir
cd mydir && source bin/activate
git clone https://github.com/alapha23/needle_puncher
```

#### Start a qemu vm
```
qemu-img create tumbleweed.img 20G
qemu-system-x86_64 -hda tumbleweed.img -boot d -cdrom <iso directory> -m <RAM> --enable-kvm
# After installing
qemu-system-x86_64 -hda tumbleweed.img --enable-kvm -display vnc=:1 -m <RAM>
# Please remember to use -display vnc=:<port>
# Feel free to start qemu in other ways, but remeber to use vnc
```
Find the pid of qemu process by `ps aux|grep qemu`. 

#### Start needle puncher

```
python cropper.py --port <port> --pid <pid>
```
If specified `-display vnc=:1`, then please use `--port 5901`.
 
Usages
---

### 1\. Click Capture & Pause
Our qemu vm will be paused and a screen capture would appear. 

### 2\. Select regions

<Insert> to add an area
Arrow keys to move
<Shift>-Arrowkeys to resize
<Alt> to change area type
<Tab> switch between areas

### 3\. Fill in filename and tags

It is suggested to end filenames with `.png`. Also, multiple tags are seperated with whitespaces. 

### 4\. Click Save needle

A png file and json file with your specified filename would be placed under current directory. 

Should any errors happen, please check the command line. 
