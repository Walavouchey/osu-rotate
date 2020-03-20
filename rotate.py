# Spaghetti code galore <3
import sys
import os
import zipfile

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
     
def scalexy(x, y, cx, cy, s):
    x -= cx
    y -= cy
    x *= s
    y *= s
    x += cx
    y += cy
    return int(x), int(y)

def convert(filename):
    osu_cx = 256
    osu_cy = 192
    scale = 4.0/3.0

    file = open(filename, "r", encoding="utf-8")
    text = file.read()
    file.close()

    tag = "[HitObjects]"
    offset = text.find(tag)
    objects = text[offset:]
    offset += objects.find("\n") + 1
    objects = text[offset:]
    lines = objects.split("\n")

    tag2 = "CircleSize:"
    offset2 = text.find(tag2)
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

    tag3 = "SliderMultiplier:"
    offset3 = text.find(tag3)
    offset3 += text[offset3:].find(":") + 1

    # Scale slider multiplier
    str_slider_multiplier = text[offset3:offset3 + text[offset3:].find("\n")]
    slider_multiplier = float(str_slider_multiplier)
    new_slider_multiplier = slider_multiplier * scale

    newfile = text[0:offset2] + str(new_circle_size) + text[offset2 + len(str_circle_size):offset3] +\
            str(new_slider_multiplier) + text[offset3 + len(str_slider_multiplier):offset]

    tag4 = "Version:"
    offset4 = newfile.find(tag4)
    offset4 += text[offset4:].find("\n")

    flag = " r-90"
    newfile = newfile[0:offset4] + flag + newfile[offset4:]

    new_filename = filename[0:filename.find("]")] + flag + filename[filename.find("]"):]

    for line in lines:
        if not line:
            continue
        args = line.split(",")

        # Rotate and scale hitobject positions
        x = int(args[0])
        y = int(args[1])
        x, y = rotatexy(x, y, osu_cx, osu_cy)
        x, y = scalexy(x, y, osu_cx, osu_cy, scale)
        args[0] = str(x)
        args[1] = str(y)

        if len(args) > 5 and args[5].find("|") != -1:
            sliderpoints = []
            new_sliderpoints = ""
            sliderpoints = args[5].split("|")
            new_sliderpoints = sliderpoints.pop(0)

            # Rotate and scale curve points in sliders
            for sliderpoint in sliderpoints:
                sliderpoint = sliderpoint.split(":")
                sx = int(sliderpoint[0])
                sy = int(sliderpoint[1])
                sx, sy = rotatexy(sx, sy, osu_cx, osu_cy)
                sx, sy = scalexy(sx, sy, osu_cx, osu_cy, scale)
                sliderpoint[0] = str(sx)
                sliderpoint[1] = str(sy)
                sliderpoint = ":".join(sliderpoint)
                new_sliderpoints += "|" + sliderpoint
            if new_sliderpoints != "":
                args[5] = new_sliderpoints
                
            # Scale the length of each slider
            args[7] = str(float(args[7]) * scale)
        
        newline = ",".join(args) + "\n"
        newfile += newline

    with open(new_filename, "w", encoding="utf-8") as ofile:
        ofile.write(newfile)

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

directory = sys.argv[1]
os.system(f"rm -r rotated & mkdir rotated & cp -r \"{directory}\" ./rotated")
directory_name = os.listdir("./rotated")[0]
files = os.listdir("./rotated/" + directory_name)
for file in files:
    if file.endswith(".osu"):
        print("converting " + file)
        convert("rotated/" + directory_name + "/" + file)
        os.system(f"rm \"./rotated/{directory_name}/{file}\"")

zipf = zipfile.ZipFile(f"{directory_name}.osz", 'w', zipfile.ZIP_DEFLATED)
zipdir("./rotated/" + directory_name, zipf)
zipf.close()

