from tkinter import *
from tkinter import filedialog, Entry, messagebox, Text, Scrollbar, Menu, OptionMenu
from tkinter.ttk import Frame, Button, Progressbar, Notebook
import csv
import os
import logging
from datetime import datetime
import traceback
from importlib import import_module
import xml.etree.cElementTree as ET
from xml.dom.minidom import parseString


class TacoShell:
    # TODO create absorb module functionality
    """

    """

    def __init__(self):
        # ROOT
        self.root = Tk()
        self.root.title("Shell GUI")
        self.root.minsize(width=200, height=200)
        self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.__position_window(self.root, 400, 350)

        # Declarations
        self.DEBUG_MODE = False
        self.help_text = "This won't help you at all.."
        self.about_text = "TacoShell v 0.1\nby Eivind Brate Midtun"
        self.children = {}
        self._next_child_id = 0
        self.components = {}
        self.instance_changes = []
        self.config_file = 'shellconfig.xml'
        self.mod_list = []

        # Initializations
        self.__init_menu()
        self.__init_debug()
        self.__init_frame_source()
        self.__init_frame_generate()
        self.__init_frame_progress()
        self.__init_frame_tabs()
        self.__init_frame_search()
        self.__set_pack_order()
        self.__read_from_xml()
        self.__repack()
        self.root.mainloop()

    @staticmethod
    def __position_window(window, window_width, window_height, x=None, y=None):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        if x is None:
            x = int((screen_width / 2) - (window_width / 2))
        if y is None:
            y = int((screen_height / 2) - (window_height / 2))
        window.geometry("{}x{}+{}+{}".format(window_width, window_height,
                                             max(min(x, screen_width - 100), 20),
                                             max(min(y, screen_height - 100), 20)))

    def __set_pack_order(self):
        separator = Frame(height=2, borderwidth=1, relief=GROOVE)

        # Order in pack_list determines order in root
        # TODO look into using an ordered dict
        self.packing = {
            'list': [
                {'name': 'frame_progress', 'widget': self.components['frame_progress'],
                 'side': BOTTOM, 'fill': X, 'default': True, 'operable': True},
                {'name': 'separator', 'widget': separator,
                 'side': BOTTOM, 'fill': X, 'pady': (3, 0), 'default': True, 'operable': True},
                {'name': 'frame_generate', 'widget': self.components['frame_generate'],
                 'side': BOTTOM, 'fill': X, 'default': True, 'operable': True},
                {'name': 'frame_debug', 'widget': self.components['frame_debug'],
                 'side': TOP, 'fill': X, 'default': False, 'operable': True},
                {'name': 'frame_source', 'widget': self.components['frame_source'],
                 'side': TOP, 'fill': X, 'default': True, 'operable': True},
                {'name': 'frame_search', 'widget': self.components['frame_search'],
                 'side': TOP, 'fill': X, 'default': False, 'operable': True},
                {'name': 'frame_tabs', 'widget': self.components['frame_tabs'],
                 'side': TOP, 'fill': BOTH, 'expand': YES, 'default': True, 'operable': True}
            ],
            # Indices must match the order in the list
            'indices': {
                'frame_progress': 0,
                'separator': 1,
                'frame_generate': 2,
                'frame_debug': 3,
                'frame_source': 4,
                'frame_search': 5,
                'frame_tabs': 6
            }
        }
        for w in self.packing['list']:
            w['flag'] = w['default']

    def __on_closing(self):
        self.__save_as_xml()
        if 'window_flags' in self.components.keys():
            self.components['window_flags'].destroy()
        self.root.destroy()

    @staticmethod
    def __b(string):
        """Converts string to boolean"""
        return True if string == 'True' else False

    def __read_from_xml(self):
        tree = ET.parse(self.config_file)
        mod_node = tree.find('mods')
        flags_node = tree.find('flags')
        paths_node = tree.find('paths')

        for child in mod_node:
            mod = {'name': child.tag, 'value': self.__b(child.text), 'default': False}
            self.mod_list.append(mod)
            self.__get_ingredients(mod)

        for child in flags_node:
            if child.tag in self.packing['indices']:
                pack = self.packing['list'][self.packing['indices'][child.tag]]
                pack['flag'] = self.__b(child.text)
                if pack['name'] == 'frame_debug':
                    self.__toggle_debug(pack['flag'])

        for child in paths_node:
            self.components[child.tag].set(child.text)

    def __save_as_xml(self):
        flag_data = []
        for item in self.instance_changes:
            if item == 'flags_changed':
                response = messagebox.askyesno("Unsaved flag changes",
                                               "Save flag settings?")
                if response:
                    for w in self.packing['list']:
                        flag_data.append({'tag': w['name'], 'value': str(w['flag'])})

        mod_data = []
        for mod in self.mod_list:
            mod_data.append({'tag': mod['name'], 'value': str(mod['value'])})

        path_data = []
        if os.path.isfile(self.components['entry_path_text'].get()):
            path_str = self.components['entry_path_text'].get()
            path_data.append({'tag': 'entry_path_text', 'value': path_str})

        save_data = [
            {'tag': 'mods', 'elements': mod_data},
            {'tag': 'flags', 'elements': flag_data},
            {'tag': 'paths', 'elements': path_data}
        ]
        self.__write_xml('shellconfig.xml', save_data)

    @staticmethod
    def __write_xml(file, data: list=None):
        if data is None:
            data = [
                {'tag': 'OpcDataPoint',
                 'elements': [
                     {'tag': 'data_tag', 'value': 'some data'}
                 ]*10
                 }
            ]*10

        if os.path.isfile(file):
            try:
                tree = ET.parse(file)
                root = tree.getroot()

            except:
                root = ET.Element('root')

        else:
            root = ET.Element('root')

        for element in data:
            child = root.find(element['tag'])
            if child is None:
                child = ET.SubElement(root, element['tag'])

            for data_element in element['elements']:
                sub_child = root.find(element['tag'] + '/' + data_element['tag'])
                if sub_child is None:
                    sub_child = ET.SubElement(child, data_element['tag'])

                sub_child.text = data_element['value']

        xml_str = str(ET.tostring(root), 'utf-8').replace('\n', '').replace('\t', '').encode('utf-8')
        pretty_xml = parseString(xml_str).toprettyxml(newl='\n', indent="\t")
        with open(file, 'w+') as f:
            f.write(pretty_xml)
            f.close()

    def __save_flags(self, file):
        for w in self.packing['list']:
            if w['flag'] != w['default']:
                file.write(w['name'] + '.flag=' + str(w['flag']) + '\n')

    def __init_menu(self):
        menubar = Menu(self.root)

        # Cascade options
        menu_options = Menu(menubar, tearoff=0)
        menu_options.add_command(label="help", command=self.menu_help)
        menu_options.add_command(label="about", command=self.__menu_about)

        # Add to menubar
        menubar.add_cascade(label="options", menu=menu_options)
        menubar.add_command(label="flags", command=self.__open_flag_settings)
        v = []
        menubar.add_command(label="mods",
                            command=lambda: self.__open_tool_window(
                                window_key='window_mods',
                                v=v,
                                title='mods',
                                table=self.mod_list,
                                actions=[{'text': 'set', 'command': lambda: self.__install_mod(v)},
                                         {'text': 'add', 'command': lambda: self.__add_mod(v)}]))
        self.root.config(menu=menubar)

    def __open_flag_settings(self):
        if 'window_flags' not in self.components.keys():
            window_flags = Toplevel(self.root)
            window_flags.grab_set()
            window_flags.title("flags")
            self.__position_window(window_flags, 270, 350,
                                   self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)
            window_flags.minsize(width=200, height=200)
            window_flags.attributes('-toolwindow', True)
            window_flags.protocol("WM_DELETE_WINDOW", lambda: self.__tool_window_closing(window_flags))

            v = []
            Button(window_flags, text='set', command=lambda: self.__set_flags(v)).pack(side=BOTTOM, anchor='e')
            for i, w in enumerate(self.packing['list']):
                if w['operable']:
                    row = Frame(window_flags)
                    Label(row, text=w['name']).pack(side=LEFT)
                    v.append({'idx': i, 'var': StringVar(row)})
                    val = 'True{}' if w['flag'] else 'False{}'
                    v[-1]['var'].set(val.format('(default)' if w['flag'] == w['default'] else ''))
                    choices = ['True(default)' if w['default'] else 'True',
                               'False(default)' if not w['default'] else 'False']
                    opt = OptionMenu(row, v[-1]['var'], *choices)
                    opt.config(width=12)
                    opt.pack(side=RIGHT)

                    row.pack(side=TOP, fill=X)
                    Frame(window_flags, height=2, borderwidth=1, relief=GROOVE).pack(side=TOP, fill=X)

            self.components['window_flags'] = window_flags
            window_flags.mainloop()

        elif not self.components['window_flags'].state() == 'normal':
            self.components['window_flags'].deiconify()
            self.components['window_flags'].grab_set()
            self.__position_window(self.components['window_flags'], 270, 350,
                                   self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)

    def __open_tool_window(self, window_key, v, title='tool', table: list=None, actions: list=None):
        # TODO migrate __open_flag_settings users to this generic method
        """
        table in the format:
        {'name': name, 'value': value handle, 'default': default}

        :param window_key:
        :param table:
        :param action_method:
        :return:
        """
        if window_key not in self.components.keys():
            window = self.components[window_key] = Toplevel(self.root)
            window.grab_set()
            window.title(title)
            self.__position_window(window, 270, 350,
                                   self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)
            window.minsize(width=200, height=200)
            window.attributes('-toolwindow', True)
            window.protocol("WM_DELETE_WINDOW", lambda: self.__tool_window_closing(window))

            frame_bottom = Frame(window)
            for action in actions:
                Button(frame_bottom, width=10, text=action['text'], command=action['command']).pack(side=RIGHT)
            frame_bottom.pack(side=BOTTOM, fill=X)

            for i, w in enumerate(table, start=0):
                self.__add_row(window, v, w, i)

        elif not self.components[window_key].state() == 'normal':
            w = self.components[window_key]
            w.deiconify()
            w.grab_set()
            self.__position_window(w, 270, 350, self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)

    @staticmethod
    def __add_row(window, v, w, i):
        row = Frame(window)
        Label(row, text=w['name']).pack(side=LEFT)
        v.append({'idx': i, 'var': StringVar(row)})
        val = 'True{}' if w['value'] else 'False{}'
        v[-1]['var'].set(val.format('(default)' if w['value'] == w['default'] else ''))
        choices = ['True(default)' if w['default'] else 'True',
                   'False(default)' if not w['default'] else 'False']
        opt = OptionMenu(row, v[-1]['var'], *choices)
        opt.config(width=12)
        opt.pack(side=RIGHT)

        row.pack(side=TOP, fill=X)
        Frame(window, height=2, borderwidth=1, relief=GROOVE).pack(side=TOP, fill=X)

    def __add_mod(self, v):
        response = filedialog.askopenfilename(
            title="Select file", filetypes=(("mod file", "*.py"), ("all files", "*.*")))
        if response != '':
            filename_w_ext = os.path.basename(response)
            filename, _ = os.path.splitext(filename_w_ext)
            mod = {'name': filename, 'value': False, 'default': False}
            self.mod_list.append(mod)
            self.__add_row(self.components['window_mods'], v, mod, len(self.mod_list)-1)
            print("added mod: " + mod['name'])

    def __install_mod(self, v):
        for d in v:
            self.mod_list[d['idx']]['value'] = True if d['var'].get() in ('True', 'True(default)') else False
        for mod in self.mod_list:
            self.__get_ingredients(mod)

    @staticmethod
    def __tool_window_closing(handle):
        handle.withdraw()
        handle.grab_release()

    def __set_flags(self, v):
        for d in v:
            self.packing['list'][d['idx']]['flag'] = True if d['var'].get() in ('True', 'True(default)') else False
            if self.packing['list'][d['idx']]['name'] == 'frame_debug':
                self.__toggle_debug(self.packing['list'][d['idx']]['flag'])
        self.__repack()
        if 'flags_changed' not in self.instance_changes:
            self.instance_changes.append('flags_changed')

    def __init_debug(self):
        frame_debug = Frame(self.root)

        btn_test = Button(frame_debug,
                          text='save xml',
                          command=self.__save_as_xml)

        btn_test2 = Button(frame_debug,
                           text='read xml',
                           command=self.__read_from_xml)

        btn_test3 = Button(frame_debug,
                           text='placeholder')

        lbl_debug = Label(frame_debug, text="DEBUG MODE", fg="red")

        lbl_debug.pack(side=RIGHT)
        btn_test.pack(side=LEFT)
        btn_test2.pack(side=LEFT)
        btn_test3.pack(side=LEFT)

        self.components['frame_debug'] = frame_debug

    def __init_frame_source(self):
        frame_source = Frame(self.root)
        self.components['entry_path_text'] = StringVar()
        entry_path = Entry(frame_source, textvariable=self.components['entry_path_text'])
        btn_set_directory = Button(frame_source,
                                   text="Set source",
                                   command=self.__set_directory)
        entry_path.bind(sequence='<KeyRelease>', func=self.__path_keypress)

        btn_set_directory.pack(side=LEFT, padx=5, pady=5)
        entry_path.pack(side=LEFT, fill=X, expand=YES, padx=5)

        self.components['frame_source'] = frame_source
        self.components['entry_path'] = entry_path
        self.components['btn_set_directory'] = btn_set_directory

    def __init_frame_generate(self):
        frame_generate = Frame(self.root)
        btn_generate = Button(frame_generate,
                              text="Generate",
                              state='disabled',
                              )
        btn_generate.pack(side=RIGHT, padx=5, pady=5, fill=X)

        self.components['frame_generate'] = frame_generate
        self.components['btn_generate'] = btn_generate

    def __init_frame_progress(self):
        frame_progress = Frame(self.root)
        progressbar = Progressbar(frame_progress, style='black.Horizontal.TProgressbar')
        lbl_progress = Label(frame_progress, text="Idle", width=10)

        lbl_progress.pack(side=LEFT)
        progressbar.pack(side=RIGHT, padx=5, pady=5, fill=X, expand=YES)

        self.components['frame_progress'] = frame_progress
        self.components['lbl_progress'] = lbl_progress

    def __init_frame_tabs(self):
        frame_tabs = Frame(self.root)
        tab_control = Notebook(frame_tabs)

        frame_log = Frame(tab_control)
        txt_log = Text(frame_log, wrap='none', state='disabled')
        scrollbar_hori = Scrollbar(frame_log, orient=HORIZONTAL, command=txt_log.xview)
        txt_log['xscrollcommand'] = scrollbar_hori.set
        scrollbar_vert = Scrollbar(frame_log, command=txt_log.yview)
        txt_log['yscrollcommand'] = scrollbar_vert.set
        txt_log.bind('<Control-f>', self.__tab_hotkeys)
        txt_log.tag_configure("blue", foreground="blue")

        scrollbar_vert.pack(side=RIGHT, fill=Y, pady=(5, 25))
        scrollbar_hori.pack(side=BOTTOM, fill=X, padx=(5, 5))
        txt_log.pack(side=LEFT, padx=5, pady=5, fill=BOTH, expand=YES)

        tab_control.add(frame_log, text='Log')
        tab_control.pack(fill=BOTH, expand=YES)

        self.components['frame_tabs'] = frame_tabs
        self.components['txt_log'] = txt_log

    def __init_frame_search(self):
        frame_search = Frame(self.root)
        entry_search = Entry(frame_search, width=10)
        entry_search.bind(sequence='<KeyRelease>', func=self.__search_keypress)
        lbl_search = Label(frame_search, text='Search')

        entry_search.pack(side=RIGHT, padx=(0, 25))
        lbl_search.pack(side=RIGHT)

        self.components['frame_search'] = frame_search
        self.components['entry_search'] = entry_search

    def __provide_child_id(self):
        self._next_child_id += 1
        return str(self._next_child_id)

    def __get_ingredients(self, mod):
        child_id = self.__provide_child_id()
        try:
            if mod['value']:
                module = import_module(mod['name'])
                instance = module.make_taco()
                self.children[child_id] = instance
                self.children[child_id].eat_taco(self, child_id)
                print("Added " + mod['name'] + " to taco")

        except:
            print("Failed to add ingredient " + mod['name'])

    def __set_flag(self, widget, state):
        self.packing['list'][self.packing['indices'][widget]]['flag'] = state

    def __toggle_debug(self, state):
        if state:
            self.components['btn_generate'].config(state='normal')
            self.components['txt_log'].config(state='normal')
        else:
            if not os.path.isfile(self.components['entry_path'].get()):
                self.components['btn_generate'].config(state='disabled')
            self.components['txt_log'].config(state='disabled')

    @staticmethod
    def __val(d, key):
        return d[key] if key in d.keys() else None

    def __repack(self, s=None):

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

    def __menu_about(self):
        messagebox.showinfo("About", self.about_text)

    def __search_keypress(self, _):
        text: str = self.components['txt_log'].get('1.0', 'end-1c')
        text_array = text.splitlines()
        try:
            # TODO include column position
            index = [i for i, s in enumerate(text_array) if self.components['frame_search'].get() in s]
            self.components['txt_log'].see(str(index[0] + 1)+'.0')

        except:
            pass

    def __tab_hotkeys(self, _):
        if self.components['frame_search'].winfo_ismapped():
            self.__set_flag('frame_search', False)
            self.__repack()

        else:
            self.__set_flag('frame_search', True)
            self.__repack()

    def __path_keypress(self, _):
        self.components['btn_generate'].config(
            state='normal' if os.path.isfile(self.components['entry_path'].get()) else 'disabled')

    def __set_directory(self):
        """
        Select directory for files.

        :return:
        """
        response = filedialog.askopenfilename(
            title="Select file", filetypes=(("Taglist", "*.csv"), ("all files", "*.*")))
        if response != '':
            self.components['entry_path_text'].set(response)
            self.components['btn_generate'].config(state='normal')

    @staticmethod
    def interpret_file(file, delimiter=None, quotechar=None):
        """

        :return:
        """
        raw_file = open(file, 'r', newline='')
        eval_buffer = []
        for line in raw_file.readlines():
            if line.strip(' \t\r\n') and line[0] != '@':
                eval_buffer.append(line)
        interpreted_file = csv.reader(eval_buffer, delimiter=delimiter, quotechar=quotechar, skipinitialspace=True)
        return interpreted_file

    @staticmethod
    def get_timestamp():
        return datetime.now().strftime('_%Y-%m-%d_%Hh%M')


def main():
    try:
        TacoShell()

    except:
        traceback.print_exc()
        logging.basicConfig(filename='log.txt',
                            level=logging.DEBUG,
                            format='%(asctime)s',
                            datefmt='%m-%d %H:%M')
        logging.exception("message")


if __name__ == '__main__':
    main()