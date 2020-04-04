# Spaghetti code galore <3
import sys
import os
import subprocess
import zipfile
import ntpath
import tkinter as tk
from tkinter import filedialog
from math import sin, cos, pi, radians

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

# Functions to rotate and scale coordinates
def rotatexy(x, y, cx, cy):
    x -= cx
    y -= cy
    temp = x
    x = -y
    y = temp
    x += cx
    y += cy
    return x, y

def rotatexy(x, y, cx, cy, theta):
    s = sin(theta)
    c = cos(theta)
    x -= cx
    y -= cy
    xnew = int(x * c - y * s)
    ynew = int(x * s + y * c)
    x = xnew + cx
    y = ynew + cy
    return x, y
     
def scalexy(x, y, cx, cy, s):
    x -= cx
    y -= cy
    x *= s
    y *= s
    x += cx
    y += cy
    return int(x), int(y)

def convert(filename, theta, folder, flag):
    # osu! playfield dimensions
    osu_cx = 256
    osu_cy = 192
    # After rotating, everything needs to be scaled up to the new aspect ratio
    srcw = abs(9 * sin(pi/2 - theta)) + abs(6.75  * sin(theta))
    srch = abs(6.75 * sin(pi/2 - theta)) + abs(9 * sin(theta))
    print(srcw, srch)
    scale = min( 9/srcw, 16/srch)
    #scale = 4.0/3.0

    file = open(filename, "r", encoding="utf-8")
    text = file.read()
    file.close()
    
    offset = text.find("[HitObjects]")
    objects = text[offset:]
    offset += objects.find("\n") + 1
    objects = text[offset:]
    lines = objects.split("\n")

    offset2 = text.find("CircleSize:")
    offset2 += text[offset2:].find(":") + 1

    # Scale the circle size according to the scaling factor. 
    # These conversions are derived from two sources:
    #   - https://osu.ppy.sh/forum/p/4282387
    #   - https://www.reddit.com/r/osugame/comments/4pz8nr/how_to_click_beside_circles_in_osu_and_get_300/d4p2so0/
    # So, new_circle_size = circle_size * cs_scale, where f(circle_size * cs_scale) = f(circle_size) * scale
    # and f(cs) is either of what the sources suggest.
    # The resulting factors of 109/9 and 85/7 are very similar and therefore too hard for me to distinguish.
    # Feel free to correct me on this one.
    str_circle_size = text[offset2:offset2 + text[offset2:].find("\n")]
    circle_size = float(str_circle_size)
    new_circle_size = circle_size * (scale - (109 * (scale - 1) / (9 * circle_size)))
    #new_circle_size = circle_size * (scale - (85 * (scale - 1) / (7 * circle_size)))

    offset3 = text.find("SliderMultiplier:")
    offset3 += text[offset3:].find(":") + 1

    # Scale slider multiplier
    str_slider_multiplier = text[offset3:offset3 + text[offset3:].find("\n")]
    slider_multiplier = float(str_slider_multiplier)
    new_slider_multiplier = slider_multiplier * scale

    newfile = text[0:offset2] + str(new_circle_size) + text[offset2 + len(str_circle_size):offset3] +\
            str(new_slider_multiplier) + text[offset3 + len(str_slider_multiplier):offset]

    offset4 = newfile.find("Version:")
    offset4 += text[offset4:].find("\n")

    newfile = newfile[0:offset4] + flag + newfile[offset4:]


    for line in lines:
        if not line:
            continue
        args = line.split(",")

        # Rotate and scale hitobject positions
        x = int(args[0])
        y = int(args[1])
        x, y = rotatexy(x, y, osu_cx, osu_cy, theta)
        x, y = scalexy(x, y, osu_cx, osu_cy, scale)
        args[0] = str(x)
        args[1] = str(y)

        if int(args[3]) & 2 == 2:
            sliderpoints = []
            new_sliderpoints = ""
            sliderpoints = args[5].split("|")
            new_sliderpoints = sliderpoints.pop(0)

            # Rotate and scale curve points in sliders
            for sliderpoint in sliderpoints:
                sliderpoint = sliderpoint.split(":")
                sx = int(sliderpoint[0])
                sy = int(sliderpoint[1])
                sx, sy = rotatexy(sx, sy, osu_cx, osu_cy, theta)
                sx, sy = scalexy(sx, sy, osu_cx, osu_cy, scale)
                sliderpoint[0] = str(sx)
                sliderpoint[1] = str(sy)
                sliderpoint = ":".join(sliderpoint)
                new_sliderpoints += "|" + sliderpoint
            if new_sliderpoints != "":
                args[5] = new_sliderpoints
                
            # Scale the length of each slider
            args[7] = str(round(float(args[7]) * scale, 10))
        
        newline = ",".join(args) + "\n"
        newfile += newline

    filename = path_leaf(filename)
    new_filename = filename[0:filename.find("]")] + flag + filename[filename.find("]"):]
    with open(folder + "/" + new_filename, "w", encoding="utf-8") as ofile:
        ofile.write(newfile)

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

root = tk.Tk()
root.withdraw()

directory = filedialog.askdirectory()
angle = int(sys.argv[1]) # in degrees
flag = " r-" + int(angle)
print(f"Rotating by {angle} degrees. \"{flag}\" will be appended to each rotated difficulty.")
directory_name = path_leaf(directory)
warn = "\033[93m"
end = "\033[0m"

if directory_name == "Songs":
    # guess we're converting everything
    songs = os.listdir(directory)
    os.system("mkdir Songs")
    print(warn + f"Converting entire songs folder ({len(songs)} beatmaps) into ./songs. Press ctrl-c at anytime to cancel!" + end)

    for song in songs:
        try:
            files = os.listdir(directory + "/" + song)
        except e:
            print(warn + song + " was not a song folder, skipping." + end)
            continue
        print(song)
        os.system(f"cp -r \"{directory}/{song}\" ./Songs")
        for file in files:
            if file.endswith(".osu"):
                print("converting " + file)
                try:
                    convert(directory + "/" + song + "/" + file, radians(angle), "Songs/" + song, flag)
                except:
                    print(warn + "Failed to convert " + file + ", skipping." + end)
                os.system(f"rm \"./Songs/{song}/{file}\"")
        zipf = zipfile.ZipFile(f"./Songs/{song}.osz", 'w', zipfile.ZIP_DEFLATED)
        zipdir("./Songs/" + song, zipf)
        zipf.close()
else:
    os.system(f"rm -r \"{directory_name}\" & cp -r \"{directory}\" .")
    files = os.listdir("./" + directory_name)
    print(directory_name)
    for file in files:
        if file.endswith(".osu"):
            print("converting " + file)
            try:
                convert("./" + directory_name + "/" + file, radians(angle), "./" + directory_name + "/", flag)
            except:
                print(warn + "\nFailed to convert " + file + ", skipping." + end)
            os.system(f"rm \"./{directory_name}/{file}\"")
    zipf = zipfile.ZipFile(f"{directory_name}.osz", 'w', zipfile.ZIP_DEFLATED)
    zipdir("./" + directory_name, zipf)
    zipf.close()
