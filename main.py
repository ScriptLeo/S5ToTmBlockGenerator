from tkinter import *
from tkinter import filedialog, Entry, messagebox, Text, Scrollbar, Menu
from tkinter.ttk import Frame, Button, Progressbar, Notebook
import csv
import os
import logging
from datetime import datetime
import traceback


class Gui:
    """

    """

    def __init__(self):
        self.root = Tk()
        self.root.title("Block Generator")
        self.root.geometry("400x400")
        self.root.minsize(width=200, height=200)

        self.DEBUG_MODE = False
        self.help_text = "This won't help you at all.."
        self.children = {}
        self._next_child_id = 0

        self.__init_menu()

        # Debug
        self.frame_debug = Frame(self.root)
        lbl_debug = Label(self.frame_debug, text="DEBUG MODE", fg="red")

        lbl_debug.pack(side=RIGHT)

        # Separator
        separator = Frame(height=2, borderwidth=1, relief=GROOVE)

        # Frame - Source
        self.frame_source = Frame(self.root)
        self.entry_new_path = Entry(self.frame_source)
        btn_set_directory = Button(self.frame_source,
                                   text="Set source",
                                   command=lambda: self.__set_directory(self.entry_new_path))
        self.entry_new_path.bind(sequence='<KeyRelease>', func=self.__path_keypress)

        btn_set_directory.pack(side=LEFT, padx=5, pady=5)
        self.entry_new_path.pack(side=LEFT, fill=X, expand=YES, padx=5)

        # Frame - Generate
        frame_generate = Frame(self.root)
        self.btn_generate = Button(frame_generate,
                                   text="Generate",
                                   state='disabled',
                                   )
        self.btn_generate.pack(side=RIGHT, padx=5, pady=5, fill=X)

        # Frame - Progress
        frame_progress = Frame(self.root)
        progressbar = Progressbar(frame_progress, style='black.Horizontal.TProgressbar')
        self.lbl_progress = Label(frame_progress, text="Idle", width=10)

        self.lbl_progress.pack(side=LEFT)
        progressbar.pack(side=RIGHT, padx=5, pady=5, fill=X, expand=YES)

        # Frame - Tabs
        self.frame_tabs = Frame(self.root)
        tab_control = Notebook(self.frame_tabs)

        frame_log = Frame(tab_control)
        self.txt_log = Text(frame_log, wrap='none', state='disabled')
        scrollbar_hori = Scrollbar(frame_log, orient=HORIZONTAL, command=self.txt_log.xview)
        self.txt_log['xscrollcommand'] = scrollbar_hori.set
        scrollbar_vert = Scrollbar(frame_log, command=self.txt_log.yview)
        self.txt_log['yscrollcommand'] = scrollbar_vert.set
        self.txt_log.bind('<Control-f>', self.__tab_hotkeys)
        self.txt_log.tag_configure("blue", foreground="blue")

        scrollbar_vert.pack(side=RIGHT, fill=Y, pady=(5, 25))
        scrollbar_hori.pack(side=BOTTOM, fill=X, padx=(5, 5))
        self.txt_log.pack(side=LEFT, padx=5, pady=5, fill=BOTH, expand=YES)

        tab_control.add(frame_log, text='Log')
        tab_control.pack(fill=BOTH, expand=YES)

        # Frame - Search
        self.frame_search = Frame(self.root)
        self.entry_search = Entry(self.frame_search, width=10)
        self.entry_search.bind(sequence='<KeyRelease>', func=self.__search_keypress)
        lbl_search = Label(self.frame_search, text='Search')

        self.entry_search.pack(side=RIGHT, padx=(0, 25))
        lbl_search.pack(side=RIGHT)

        # Pack to root
        # Order in pack_list determines order in root
        self.packing = {
            'list': [
                {'widget': frame_progress, 'order': 0, 'side': BOTTOM, 'fill': X, 'flag': True},
                {'widget': separator, 'order': 1, 'side': BOTTOM, 'fill': X, 'flag': True, 'pady': (3, 0)},
                {'widget': frame_generate, 'order': 2, 'side': BOTTOM, 'fill': X, 'flag': True},
                {'widget': self.frame_debug, 'order': 3, 'side': TOP, 'fill': X, 'flag': False},
                {'widget': self.frame_source, 'order': 4, 'side': TOP, 'fill': X, 'flag': True},
                {'widget': self.frame_search, 'order': 5, 'side': TOP, 'fill': X, 'flag': False},
                {'widget': self.frame_tabs, 'order': 6, 'side': TOP, 'fill': BOTH, 'expand': YES, 'flag': True}
            ],
            'indices': {
                'frame_progress': 0,
                'separator': 1,
                'frame_generate': 2,
                'frame_debug': 3,
                'frame_source': 4,
                'frame_search': 5,
                'frame_tab': 6
            }
        }
        self.repack()
        self.__connect_to_users()
        self.root.mainloop()

    def __init_menu(self):
        menubar = Menu(self.root)

        # Cascade options
        menu_options = Menu(menubar, tearoff=0)
        menu_options.add_command(label="debug", command=self.__toggle_debug)
        menu_options.add_command(label="help", command=self.menu_help)

        # Add to menubar
        menubar.add_cascade(label="options", menu=menu_options)
        menubar.add_command(label="flags")
        menubar.add_command(label="addons")
        self.root.config(menu=menubar)

    def __init_frame_source(self):
        pass

    def __init_frame_generate(self):
        pass

    def __init_frame_progress(self):
        pass

    def __init_frame_tabs(self):
        pass

    def __init_frame_search(self):
        pass

    def __provide_child_id(self):
        self._next_child_id += 1
        return str(self._next_child_id)

    def __connect_to_users(self):
        child_id = self.__provide_child_id()
        self.children[child_id] = BlockGenerator()
        self.children[child_id].connect_to_gui(self, child_id)

    def __set_flag(self, widget, state):
        self.packing['list'][self.packing['indices'][widget]]['flag'] = state

    def __toggle_debug(self):
        if self.DEBUG_MODE:
            self.DEBUG_MODE = False
            self.__set_flag('frame_debug', False)
            if not os.path.isfile(self.entry_new_path.get()):
                self.btn_generate.config(state='disabled')
            self.txt_log.config(state='disabled')
            self.repack(TOP)

        else:
            self.DEBUG_MODE = True
            self.__set_flag('frame_debug', True)
            self.btn_generate.config(state='normal')
            self.txt_log.config(state='normal')
            self.repack(TOP)

    @staticmethod
    def __val(d, key):
        return d[key] if key in d.keys() else None

    def repack(self, s=None):

        for w in self.packing['list']:
            if s is None or s == w['side']:
                w['widget'].pack_forget()

        for w in self.packing['list']:
            if (s is None or s == w['side']) and w['flag']:
                w['widget'].pack(side=self.__val(w, 'side'),
                                 fill=self.__val(w, 'fill'),
                                 expand=self.__val(w, 'expand'),
                                 padx=self.__val(w, 'padx'),
                                 pady=self.__val(w, 'pady')
                                 )

    def menu_help(self):
        messagebox.showinfo("Help", self.help_text)

    def __search_keypress(self, _):
        text: str = self.txt_log.get('1.0', 'end-1c')
        text_array = text.splitlines()
        try:
            # TODO include column position
            index = [i for i, s in enumerate(text_array) if self.entry_search.get() in s]
            self.txt_log.see(str(index[0] + 1)+'.0')

        except:
            pass

    def __tab_hotkeys(self, _):
        if self.frame_search.winfo_ismapped():
            self.__set_flag('frame_search', False)
            self.repack()

        else:
            self.__set_flag('frame_search', True)
            self.repack()

    def __path_keypress(self, _):
        self.btn_generate.config(state='normal' if os.path.isfile(self.entry_new_path.get()) else 'disabled')

    def __set_directory(self, widget):
        """
        Select directory for files.

        :return:
        """
        response = filedialog.askopenfilename(
            title="Select file", filetypes=(("Taglist", "*.csv"), ("all files", "*.*")))
        if response != '':
            widget.delete(0, END)
            widget.insert(0, response)
            widget.xview_moveto(1.0)
            self.btn_generate.config(state='normal')


class BlockGenerator:
    """

    """
    def __init__(self):
        self.source_file: str = ''
        self.output_file: str = 'code.txt'
        self.deviations_file: str = 'blockdefs/@deviations.csv'
        self.parent: Gui = None
        self.child_id = None

    def connect_to_gui(self, parent, child_id):
        self.child_id = child_id
        self.parent = parent
        self.parent.btn_generate.config(command=lambda: self.generate_blocks(self.parent.entry_new_path.get()))

    @staticmethod
    def interpret_file(file):
        """

        :return:
        """
        raw_file = open(file, 'r', newline='')
        eval_buffer = []
        for line in raw_file.readlines():
            if line.strip(' \t\r\n') and line[0] != '@':
                eval_buffer.append(line)
        interpreted_file = csv.reader(eval_buffer, delimiter=';', quotechar='"', skipinitialspace=True)
        return interpreted_file

    def generate_blocks(self, source_file):
        """

        :param source_file:
        :return:
        """
        self.parent.lbl_progress.config(text='Processing')
        self.source_file = source_file

        raw_output = open(self.output_file, 'w+')
        deviations = self.interpret_file(self.deviations_file)
        list_tags = [] if self.parent.DEBUG_MODE else self.interpret_file(source_file)

        for line in deviations:
            self.parent.txt_log.config(state='normal')
            self.parent.txt_log.insert('end', ''.join(line) + '\n')
            # self.gui_handle.txt_log.tag_add('red', )  # TODO add colored text support
            self.parent.txt_log.config(state='disabled')

        # idx_of_MKZ = list_tags[0].index('Type')
        # for line_data in list_tags[1:]:
        #     pass

        self.parent.lbl_progress.config(text='Idle')


def get_timestamp():
    return datetime.now().strftime('_%Y-%m-%d_%Hh%M')


def main():
    try:
        Gui()

    except:
        traceback.print_exc()
        logging.basicConfig(filename='log.txt',
                            level=logging.DEBUG,
                            format='%(asctime)s',
                            datefmt='%m-%d %H:%M')
        logging.exception("message")


if __name__ == '__main__':
    main()