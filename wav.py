from tkinter import *
from tkinter import filedialog
from tkinter import messagebox

import os, math, random
meta = [0x52, 0x49, 0x46, 0x46,   #RIFF master chunk identifier     [0:4]
        0x00, 0x00, 0x00, 0x00,   #file size - 8 bytes  [4:8]
        0x57, 0x41, 0x56, 0x45,   #wave format  [8:12]
        0x66, 0x6d, 0x74, 0x20,   #fmt chunk identifier [12:16]
        0x10, 0x00, 0x00, 0x00,   #chunk size (24) - 8  [16:20]
        0x01, 0x00,   #audio format is 1 for PCM int audio  [20:22]
        0x02, 0x00,   #channel number   [22:24]
        0x80, 0xbb, 0x00, 0x00,   #sample rate (48000hz)    [24:28]
        0x00, 0xee, 0x02, 0x00,   #byte rate (48000 * bytes per block)    [28:32]
        0x04, 0x00,   #bytes per block (channels * bit depth / 8)   [32:34]
        0x10, 0x00,    #bit depth (16)  [34:36]
        0x64, 0x61, 0x74, 0x61,   #data chunk identifier    [36:40]
        0x00, 0x00, 0x00, 0x00   #data chunk size   [40:44]
        ]

try: os.mkdir(".samplecache")
except FileExistsError:
    for file in os.listdir(".samplecache"):
        os.remove(".samplecache/{}".format(file))

def f_add_sample():
    global c_samples, lc_samples
    #create path for new sample and open file dialog
    formatted_sample = ".samplecache/sample_{}.wav".format(str(c_samples))
    sample_path = filedialog.askopenfilename(title = "Choose Sample",
                                             filetypes = [("WAV Audio", "*.wav"),
                                                          ("All files", "*.*")])
    #convert selected audio to stereo 48kHz s16 wav audio
    #if exited file dialog or file not created then raise appropriate errors
    if sample_path == (): return
    print(sample_path)
    os.system("ffmpeg -i {} -ac 2 -ar 48000 -sample_fmt s16 {}".format(sample_path, formatted_sample))
    if not os.path.isfile(formatted_sample):
        messagebox.showerror(title= "Invalid Audio", message = "Invalid audio file")
        return
    #on successful file creation increase sample count and crea a new sample obj
    c_samples += 1
    lc_samples.append(Sample(formatted_sample, "Sample"))
    #destroy sample edit window then restart it
    w_samples.destroy()
    f_edit_samples()
    
def f_edit_samples():
    global w_samples
    #create new window with title
    w_samples = Tk()
    w_samples.title("Edit Samples")
    #create new widgets for each sample that exists
    i = -1
    for i, sample in enumerate(lc_samples.items):
        l_temp = Label(w_samples, text = "#{} - ".format(str(i+1)))
        l_temp.grid(row = i, column = 0)
        e_temp = Entry(w_samples, width = 16)
        e_temp.insert(0, sample.name)
        e_temp.grid(row = i, column = 1)
        b_temp = Button(w_samples, text = "Change name", command = lambda sample2=sample, e_temp2=e_temp:
                        f_set_name(sample2, e_temp2.get()))
        b_temp.grid(row = i, column = 2)
        s_temp = Spinbox(w_samples, width = 5, from_ = 0, to = 100, validate="key")
        s_temp.delete(0, END)
        s_temp.insert(0, sample.probability)
        s_temp["validatecommand"] = (s_temp.register(f_validate_int), "%P")
        s_temp.grid(row = i, column = 3)
        b_temp = Button(w_samples, text = "Change probability (%)", command = lambda sample2=sample, s_temp2=s_temp:
                       f_set_probability(sample2, s_temp2.get()))
        b_temp.grid(row = i, column = 4)
        b_temp = Button(w_samples, text = "Play Sample", command = lambda sample2=sample:
                        f_play_sample(sample2))
        b_temp.grid(row = i, column = 5)
    #button to add new sample
    b_add_sample = Button(w_samples, text = "Add Sample", command = f_add_sample)
    b_add_sample.grid(row = i+1, column = 0)
    #button to finish editing samples
    b_done = Button(w_samples, text = "Done", command = f_exit_samples)
    b_done.grid(row = i+1, column = 1)
    
    w_samples.mainloop()

def f_exit_samples():
    lc_samples.validate_probability()
    w_samples.destroy()
    w_main.destroy()
    f_main_window()
def f_set_name(sample, text): sample.name = text
def f_set_probability(sample, text): sample.probability = int(text)
def f_validate_int(value):
    try: x = int(value)
    except ValueError: return False
    if x > 100 or x < 0: return False
    return True
def f_validate_int2(value):
    try: x = int(value)
    except ValueError: return False
    if x > 4294967295 or x < 0: return False
    return True
def f_validate_int3(value):
    try: x = int(value)
    except ValueError: return False
    if x > 100 or x < 1: return False
    return True
def f_play_sample(sample):
    os.system("ffplay -autoexit {}".format(sample.path))
def f_play():
    try: os.system("ffplay -autoexit out.wav")
    except: pass
def f_generate():
    global meta, bytespersecond
    bytes_written = 0
    data_chunk = []
    x = iv_var.get()
    i = 0
    d_min = int(s_duration_min.get())
    d_max = int(s_duration_max.get())
    while True:
        if x:
            if bytes_written >= bytespersecond * int(s_duration.get()): break
        else:
            if i == int(s_samples.get()): break
            else: i += 1
        try: sample = lc_samples.select_item().raw
        except: break
        sample_unit = len(sample)/100
        sample_unit2 = (len(sample)-1)/100
        try:
            segment_start = random.randrange(1, int(sample_unit2*(100-d_min)))
            segment_end = random.randrange(segment_start+int(sample_unit*d_min), segment_start+int(sample_unit*d_max))
        except:
            messagebox.showerror(title= "Invalid Range", message = "Invalid min/max clip duration range")
            break
        segment = sample[segment_start:segment_end]
        bytes_written += len(segment)*4
        data_chunk.append(b''.join(segment))
    meta[4:8] = list((bytes_written+36).to_bytes(4, byteorder="little"))
    meta[40:44] = list(bytes_written.to_bytes(4, byteorder="little"))
    meta_temp = [bytes(meta)]
    for item in data_chunk: meta_temp.append(item)
    with open("out.wav", "wb") as f:
        f.write(b''.join(meta_temp))
        f.close()
class Sample():
    def __init__(self, path, name):
        self.path = path
        self.name = name
        self.probability = 0
        with open(self.path, "rb") as f:
            self.raw = f.read()
            f.close()
        self.raw = self.raw[(self.raw.find(b'data')+4):]
        self.raw = [self.raw[i:i+4] for i in range(0, len(self.raw), 4)]

class SampleList():
    def __init__(self): self.items = []
    def append(self, member): self.items.append(member)
    def validate_probability(self):
        x = 0
        for item in self.items:
            x += item.probability
            if x > 100:
                item.probability -= x - 100
                x = 100
        if x < 100:
            item.probability += 100 - x
    def select_item(self):
        if len(self.items) == 0:
            messagebox.showerror(title= "No Audio", message = "No samples loaded")
            return False
        v = []
        for item in self.items:
            for i in range(item.probability):
                v.append(item)
        
        return random.choice(v)
c_samples = 0
lc_samples = SampleList()
bytespersecond = 48000*2*2

def f_main_window():
    global w_main, iv_var, s_duration, s_samples, s_duration_max, s_duration_min
    w_main = Tk()
    w_main.title("Main")

    #edit samples button
    b_edit_samples = Button(w_main, text = "Edit samples", command = f_edit_samples)
    b_edit_samples.grid(row = 0, column = 0)
    #label to show how many samples are loaded
    l_samples = Label(w_main, text = "Samples loaded: " + str(c_samples))
    l_samples.grid(row = 0, column = 1)

    l_duration_min = Label(w_main, text = "Minimum clip duration (%):")
    l_duration_min.grid(row = 1, column = 0)
    s_duration_min = Spinbox(w_main, width = 5, from_ = 1, to = 100, validate="key")
    s_duration_min.delete(0, END)
    s_duration_min.insert(0, "1")
    s_duration_min["validatecommand"] = (s_duration_min.register(f_validate_int3), "%P")
    s_duration_min.grid(row = 1, column = 1)
    
    l_duration_max = Label(w_main, text = "Maximum clip duration (%):")
    l_duration_max.grid(row = 2, column = 0)
    s_duration_max = Spinbox(w_main, width = 5, from_ = 1, to = 100, validate="key")
    s_duration_max.delete(0, END)
    s_duration_max.insert(0, "100")
    s_duration_max["validatecommand"] = (s_duration_max.register(f_validate_int3), "%P")
    s_duration_max.grid(row = 2, column = 1)
    
    iv_var = IntVar()
    r_by_samples = Radiobutton(w_main, text = "Target samples", variable = iv_var,
                               value = 0)
    r_by_samples.grid(row = 5, column = 0)
    s_samples = Spinbox(w_main, width = 10, from_ = 0, to = 4294967295, validate="key")
    s_samples["validatecommand"] = (s_samples.register(f_validate_int2), "%P")
    s_samples.grid(row = 5, column = 1)
    r_by_duration = Radiobutton(w_main, text = "Target duration (s)", variable = iv_var,
                               value = 1)
    r_by_duration.grid(row = 6, column = 0)
    s_duration = Spinbox(w_main, width = 10, from_ = 0, to = 4294967295, validate="key")
    s_duration["validatecommand"] = (s_duration.register(f_validate_int2), "%P")
    s_duration.grid(row = 6, column = 1)
    b_generate = Button(w_main, text = "Generate audio", command = f_generate)
    b_generate.grid(row = 99, column = 0)
    b_listen = Button(w_main, text = "Play audio", command = f_play)
    b_listen.grid(row = 99, column = 1)
    w_main.mainloop()
f_main_window()
'''
x=48000
v=x.to_bytes(4, byteorder="little")
v = list(v)
meta[4:8] = v
f = open("/home/l342n/Downloads/out.wav", "rb")
x = f.read()
f.close()
data_start = x[(x.find(b'data')+4):]
print(len(data_start))
meta[4:8] = list((len(data_start)+36).to_bytes(4, byteorder="little"))
meta[40:44] = list(len(data_start).to_bytes(4, byteorder="little"))
meta = [bytes(meta)]
meta.append(x[(x.find(b'data')+4):])
meta = b''.join(meta)
#print(len(meta))
f = open("out.wav", "wb")
f.write(meta)
f.close()
'''
