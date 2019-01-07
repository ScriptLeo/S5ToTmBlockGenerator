from tkinter import Tk, filedialog, messagebox, Text, Menu, LEFT, RIGHT, TOP, BOTTOM, BOTH, YES, X, Y, \
    Toplevel, StringVar, BooleanVar, HORIZONTAL, VERTICAL, GROOVE, CENTER, END
from tkinter import Label as TkLabel, Button as TkButton
from tkinter.ttk import Button, Progressbar, Notebook, Style, Entry, OptionMenu, Frame, Scrollbar, Label
from PIL.ImageTk import PhotoImage
from PIL.Image import ANTIALIAS
from PIL import Image
import csv
import os
import logging
from datetime import datetime
import traceback
from importlib import import_module
import xml.etree.cElementTree as ET
from xml.dom.minidom import parseString
from collections import OrderedDict
from time import time


class TacoShell:
    def __init__(self):
        # ROOT settings
        self.root = Tk()
        Tk.report_callback_exception = self.__on_error
        self.root.title("Shell GUI")
        self.root.minsize(width=200, height=200)
        self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.__position_window(self.root, 400, 350)

        # Declarations
        self.progress_update_cycle = 1/10
        self.debug_mode = False
        self.override = False
        self.help_text = "This won't help you at all.."
        self.about_text = "TacoShell v 0.1\nby Eivind Brate Midtun"
        self.children = {}
        self._next_child_id = 0
        self.components = {}
        self.instance_changes = []
        self.config_file = 'shellconfig.xml'
        self.mod_list = []
        self.font_colors = {}
        self.colors = {}
        self.icons = {}
        self.style = Style()
        self.init_summary = []

        # Initializations
        self.__init_appearance()
        self.__init_menu()
        self.__init_debug()
        self.__init_frame_source()
        self.__init_frame_generate()
        self.__init_frame_progress()
        self.__init_frame_tabs()
        self.__init_frame_search()
        self.__set_packing()
        self.__read_xml_config()
        self.__set_theme()
        self.__repack()
        self.__initialization_summary()
        self.root.mainloop()

    def __initialization_summary(self):
        for ele in self.init_summary:
            self.write_to_log(ele, 'bad')

    def __on_error(self, *args):
        try:
            self.write_to_log(traceback.format_exception(*args), 'bad')
            traceback.print_exc()
        except:
            pass

    def __init_appearance(self):
        self.colors = {'black': '#000000',
                       'dark': '#2B2B2B',
                       'milddark': '#3C3F41',
                       'lightgray': '#A3A3A3',
                       'tabactive': '#515658',
                       'tablazy': '#3C3E3F',
                       'lighttext': '#A3B1BF'}

        self.font_colors = {'normal': '#A9B7C6',
                            'highlighted': '#A35E9C',
                            'bad': '#DE553F',
                            'good': '#00AA00'}

        default_medium_icon_size = (35, 35)
        default_mini_icon_size = (20, 20)
        icons = [{'name': 'save', 'size': default_mini_icon_size},
                 {'name': 'revert', 'size': default_mini_icon_size},
                 {'name': 'close', 'size': default_mini_icon_size},
                 {'name': 'browse_excel', 'size': default_medium_icon_size},
                 {'name': 'browse', 'size': (100, 100)},
                 {'name': 'play', 'size': default_medium_icon_size},
                 {'name': 'stop', 'size': default_mini_icon_size},
                 {'name': 'switch_on', 'size': (30, 15)},
                 {'name': 'switch_off', 'size': (30, 15)}]
        missing_icons = []

        for icon in icons:
            try:
                self.icons[icon['name']] = PhotoImage(
                    Image.open('resources/' + icon['name'] + '.png').resize(icon['size'], ANTIALIAS))
            except FileNotFoundError:
                self.icons[icon['name']] = PhotoImage(Image.new("RGB", icon['size'], "white"))
                missing_icons.append(icon['name'] + '.png')

        if missing_icons:
            self.init_summary.append('Missing icon(s) in resources/ folder: ' + ', '.join(missing_icons))

    def __set_theme(self):
        self.style.theme_use('clam')
        self.style.configure("TNotebook", background=self.colors['milddark'])
        self.style.map("TNotebook.Tab",
                       background=[("selected", self.colors['tabactive'])],
                       foreground=[("selected", self.colors['lighttext'])])
        self.style.configure('TNotebook.Tab',
                             background=self.colors['tablazy'],
                             foreground=self.colors['lighttext'])
        self.style.configure('TFrame', background=self.colors['milddark'])
        self.style.configure('TButton',
                             background=self.colors['lightgray'],
                             foreground=self.colors['black'])
        self.style.configure('TLabel',
                             background=self.colors['milddark'],
                             foreground=self.colors['lighttext'])
        self.style.configure('TEntry',
                             background=self.colors['dark'],
                             foreground=self.colors['lighttext'],
                             fieldbackground=self.colors['milddark'])

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

    def __set_packing(self):
        """Order in components['packing'] determines order in which widgets are packed to root"""
        # TODO migrate to the OrderedDict
        self.components['packing'] = OrderedDict([
            ('frame_progress', {'widget': self.components['frame_progress'],
                                'side': BOTTOM, 'fill': X, 'default': True}),
            ('frame_generate', {'widget': self.components['frame_generate'],
                                'side': BOTTOM, 'fill': X, 'default': True}),
            ('frame_debug', {'widget': self.components['frame_debug'],
                             'side': TOP, 'fill': X, 'default': False}),
            ('frame_source', {'widget': self.components['frame_source'],
                              'side': TOP, 'fill': X, 'default': True}),
            ('frame_search', {'widget': self.components['frame_search'],
                              'side': TOP, 'fill': X, 'default': False}),
            ('frame_tabs', {'widget': self.components['frame_tabs'],
                            'side': TOP, 'fill': BOTH, 'expand': YES, 'default': True})
        ])
        self.packing = {
            'list': [
                {'name': 'frame_progress', 'widget': self.components['frame_progress'],
                 'side': BOTTOM, 'fill': X, 'default': True, 'operable': True},
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
                'frame_generate': 1,
                'frame_debug': 2,
                'frame_source': 3,
                'frame_search': 4,
                'frame_tabs': 5
            }
        }
        for w in self.packing['list']:
            w['flag'] = w['default']

        for w in self.components['packing'].items():
            w[1]['flag'] = w[1]['default']

    def __on_closing(self):
        self.__save_as_xml()
        if 'window_flags' in self.components.keys():
            self.components['window_flags'].destroy()
        self.root.destroy()

    @staticmethod
    def __bool(string):
        """Converts string to boolean"""
        return True if string == 'True' else False

    """XML read/write"""
    def __read_xml_config(self):
        try:
            tree = ET.parse(self.config_file)

            mod_node = tree.find('mods')
            flags_node = tree.find('flags')

            for child in mod_node:
                mod = {'name': child.tag, 'value': self.__bool(child.text), 'default': False}
                self.mod_list.append(mod)
                self.__get_ingredients(mod)

            for child in flags_node:
                if child.tag in self.packing['indices']:
                    pack = self.packing['list'][self.packing['indices'][child.tag]]
                    pack['flag'] = self.__bool(child.text)
                    if pack['name'] == 'frame_debug':
                        self.__toggle_debug(pack['flag'])

            path_child = tree.find('paths/entry_path_text')
            if path_child is not None:
                self.components['entry_path_text'].set(path_child.text)
                if os.path.isfile(self.components['entry_path_text'].get()):
                    self.components['btn_generate'].config(state='normal')

            # TODO generalize window positioning code and move to own method
            width_raw = tree.find('window/window_width').text
            height_raw = tree.find('window/window_height').text
            if width_raw is not None and height_raw is not None:
                x = str(max(0, int(tree.find('window/window_x').text)))
                y = str(max(0, int(tree.find('window/window_y').text)))
                width = str(min(int(width_raw), self.root.winfo_screenwidth()))
                height = str(min(int(height_raw), self.root.winfo_screenheight()))
                self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        except:
            traceback.print_exc()

    def __save_as_xml(self):
        flag_data = []
        for item in self.instance_changes:
            if item == 'flags_changed':
                response = messagebox.askyesno("Unsaved flag changes",
                                               "Save flag settings?")
                if response:
                    for w in self.packing['list']:
                        flag_data.append({'tag': w['name'], 'value': w['flag']})

        mod_data = []
        for mod in self.mod_list:
            mod_data.append({'tag': mod['name'], 'value': mod['value']})

        path_data = []
        if os.path.isfile(self.components['entry_path_text'].get()):
            path_str = self.components['entry_path_text'].get()
            path_data.append({'tag': 'entry_path_text', 'value': path_str})

        window_data = [{'tag': 'window_width', 'value': self.root.winfo_width()},
                       {'tag': 'window_height', 'value': self.root.winfo_height()},
                       {'tag': 'window_x', 'value': self.root.winfo_x()},
                       {'tag': 'window_y', 'value': self.root.winfo_y()}]

        save_data = [
            {'tag': 'mods', 'elements': mod_data},
            {'tag': 'flags', 'elements': flag_data},
            {'tag': 'paths', 'elements': path_data},
            {'tag': 'window', 'elements': window_data}
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

                sub_child.text = str(data_element['value'])

        xml_str = str(ET.tostring(root), 'utf-8').replace('\n', '').replace('\t', '').encode('utf-8')
        pretty_xml = parseString(xml_str).toprettyxml(newl='\n', indent="\t")
        with open(file, 'w+') as f:
            f.write(pretty_xml)
            f.close()

    def __save_flags(self, file):
        for w in self.packing['list']:
            if w['flag'] != w['default']:
                file.write(w['name'] + '.flag=' + str(w['flag']) + '\n')

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

            frame_flags = Frame(window_flags)
            frame_flags.pack(fill=BOTH, expand=YES)

            v = []
            Button(frame_flags, text='set', command=lambda: self.__set_flags(v)).pack(side=BOTTOM, anchor='e')
            for i, w in enumerate(self.packing['list']):
                if w['operable']:
                    row = Frame(frame_flags)
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
                    Frame(frame_flags, height=2, borderwidth=1, relief=GROOVE).pack(side=TOP, fill=X)

            self.components['window_flags'] = window_flags
            frame_flags.mainloop()

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

    """Initialize frames"""
    def __init_menu(self):
        menubar = Menu(self.root)

        # Cascade options
        menu_options = Menu(menubar, tearoff=0)
        menu_options.add_command(label="help", command=self.menu_help)
        menu_options.add_command(label="about", command=self.__menu_about)

        # Add to menubar
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
        menubar.add_cascade(label="?", menu=menu_options)
        self.root.config(menu=menubar)

    def __init_debug(self):
        frame_debug = Frame(self.root)

        btn_test1 = self.__new_button(frame_debug,
                                      text='test print',
                                      width=15,
                                      fg=self.font_colors['normal'],
                                      command=lambda: self.write_to_log('this is a test'))

        btn_test2 = self.__new_button(frame_debug,
                                      text='Btn 2',
                                      width=15,
                                      fg=self.font_colors['normal'],
                                      command=self.throw_error)

        lbl_debug = TkLabel(frame_debug, text="Debugging", font='semi-bold',
                            bg=self.colors['milddark'],
                            fg=self.font_colors['bad'])

        frame_override = Frame(frame_debug)
        lbl_override = Label(frame_override, text="override")
        btn_override = TkButton(frame_override,
                                image=self.icons['switch_off'],
                                bg=self.colors['milddark'],
                                activebackground=self.colors['milddark'],
                                borderwidth=0,
                                command=self.__toggle_override)

        lbl_override.pack(side=TOP)
        btn_override.pack(side=BOTTOM)

        frame_override.pack(side=RIGHT, padx=5)
        lbl_debug.pack(side=RIGHT, padx=5)
        btn_test1.pack(side=LEFT, padx=5)
        btn_test2.pack(side=LEFT)

        self.components['btn_override'] = btn_override
        self.components['frame_debug'] = frame_debug

    def throw_error(self):
        raise Exception('testetsetests')

    def __toggle_debug(self, state):
        if state:
            self.components['btn_generate'].config(state='normal')
            self.components['txt_log'].config(state='normal')
            self.debug_mode = True
        else:
            if not os.path.isfile(self.components['entry_path'].get()):
                self.components['btn_generate'].config(state='disabled')
            self.components['txt_log'].config(state='disabled')
            self.debug_mode = False

    def __init_frame_source(self):
        frame_source = Frame(self.root)
        self.components['entry_path_text'] = StringVar()
        entry_path = Entry(frame_source, textvariable=self.components['entry_path_text'])
        btn_set_directory = self.__new_button(frame_source,
                                              image=self.icons['browse_excel'],
                                              command=self.__set_directory)
        entry_path.bind(sequence='<KeyRelease>', func=self.__path_keypress)

        btn_set_directory.pack(side=LEFT, padx=5, pady=5)
        entry_path.pack(side=LEFT, fill=X, expand=YES, padx=[0, 5])

        self.components['frame_source'] = frame_source
        self.components['entry_path'] = entry_path
        self.components['btn_set_directory'] = btn_set_directory

    def __init_frame_generate(self):
        frame_generate = Frame(self.root)
        btn_generate = self.__new_button(frame_generate,
                                         image=self.icons['play'],
                                         state='disabled',
                                         command=self.__generate_command)

        btn_stop = self.__new_button(frame_generate,
                                     image=self.icons['stop'],
                                     state='disabled',
                                     command=self.__stop_command)

        lbl_generate = Label(frame_generate, text='Generate', font='semi-bold')

        btn_stop.pack(side=RIGHT, padx=[0, 5], pady=5, anchor='s')
        btn_generate.pack(side=RIGHT, padx=5, pady=5)
        lbl_generate.pack(side=RIGHT)

        self.components['STOP_COMMAND'] = False
        self.components['frame_generate'] = frame_generate
        self.components['btn_generate'] = btn_generate
        self.components['btn_stop'] = btn_stop
        self.components['btn_generate_command'] = \
            lambda: self.write_to_log('No command connected to \'btn_generate\'', 'bad')

    def __stop_command(self):
        self.components['STOP_COMMAND'] = True

    def __generate_command(self):
        c = self.components
        c['STOP_COMMAND'] = False
        c['btn_stop'].configure(state='normal')
        c['lbl_progress'].config(text='Processing')
        self.write_to_log('Started processing', 'good')
        start_time = c['start_time'] = c['last_update'] = time()

        try:
            c['btn_generate_command']()
            self.write_to_log('Finished processing in {} seconds\n'.format(str(time() - start_time)), 'good')
            c['bar_progress']['value'] = c['bar_progress']['maximum']
            c['lbl_progress'].config(text='Completed')
            c['btn_stop'].configure(state='disabled')
            c['txt_log'].yview_moveto(1)

        except Exception as e:
            self.write_to_log('Stopped code execution due to error\n'.format(str(time() - start_time)), 'bad')
            c['btn_stop'].configure(state='disabled')
            c['lbl_progress'].config(text='Error')
            c['txt_log'].yview_moveto(1)
            raise e

    def __init_frame_progress(self):
        frame_progress = Frame(self.root, relief='solid')
        bar_progress = Progressbar(frame_progress, style='black.Horizontal.TProgressbar', mode='determinate')
        lbl_progress = Label(frame_progress, text="Idle", width=10)

        lbl_progress.pack(side=LEFT, padx=[5, 0])
        bar_progress.pack(side=RIGHT, padx=5, pady=5, fill=X, expand=YES)

        self.components['frame_progress'] = frame_progress
        self.components['lbl_progress'] = lbl_progress  # TODO change labels to StringVar()
        self.components['bar_progress'] = bar_progress

    def __new_button(self, *args, **kwargs):
        button = TkButton(*args, **kwargs, bg=self.colors['milddark'])
        button.bind("<Enter>", lambda e: button.configure(bg=self.colors['lightgray']))
        button.bind("<Leave>", lambda e: button.configure(bg=self.colors['milddark']))
        return button

    class AutoScrollbar(Scrollbar):
        def __init__(self, index=None, master=None, orient=VERTICAL, command=None, pack_group=None):
            self.pack_group = pack_group
            self.index = index
            super().__init__(master=master, orient=orient, command=command)

        def set(self, lo, hi):
            pg = self.pack_group
            if float(lo) <= 0.0 and 1.0 <= float(hi):
                self.pack_forget()
                pg[self.index]['flag'].set(False)

            else:
                # TODO only repack if something has changed since last
                pg[self.index]['flag'].set(True)
                for w in pg:
                    w['handle'].pack_forget()
                for i, w in enumerate(pg):
                    if pg[i]['flag'].get():
                        pg[i]['handle'].pack(side=pg[i]['side'],
                                             padx=pg[i]['padx'], pady=pg[i]['pady'],
                                             fill=pg[i]['fill'], expand=pg[i]['expand'])
            Scrollbar.set(self, lo, hi)

    def __init_frame_tabs(self):
        frame_tabs = Frame(self.root)
        tab_control = Notebook(frame_tabs)

        frame_log = Frame(tab_control)
        txt_log = Text(frame_log, wrap='none', state='disabled',
                       background=self.colors['dark'],
                       foreground=self.font_colors['normal'],
                       insertbackground=self.font_colors['normal'])

        scrollbar_vert = self.AutoScrollbar(index=0, master=frame_log, command=txt_log.yview)
        txt_log['yscrollcommand'] = scrollbar_vert.set

        scrollbar_hori = self.AutoScrollbar(index=1, master=frame_log, orient=HORIZONTAL, command=txt_log.xview)
        txt_log['xscrollcommand'] = scrollbar_hori.set

        txt_log_var = BooleanVar()
        txt_log_var.set(True)
        scrollbar_hori.pack_group = scrollbar_vert.pack_group = [
            {'handle': scrollbar_vert, 'flag': BooleanVar(), 'side': RIGHT, 'fill': Y, 'expand': None, 'padx': None, 'pady': (5, 25)},
            {'handle': scrollbar_hori, 'flag': BooleanVar(), 'side': BOTTOM, 'fill': X, 'expand': None, 'padx': (5, 5), 'pady': None},
            {'handle': txt_log, 'flag': txt_log_var, 'side': LEFT, 'fill': BOTH, 'expand': YES, 'padx': 5, 'pady': 5}
        ]

        txt_log.bind('<Control-f>', self.__tab_hotkeys)

        txt_log.tag_configure('normal', foreground=self.font_colors['normal'])
        txt_log.tag_configure('highlighted', foreground=self.font_colors['highlighted'])
        txt_log.tag_configure('bad', foreground=self.font_colors['bad'])
        txt_log.tag_configure('good', foreground=self.font_colors['good'])

        scrollbar_vert.pack(side=RIGHT, fill=Y, pady=(5, 25))
        scrollbar_hori.pack(side=BOTTOM, fill=X, padx=(5, 5))
        txt_log.pack(side=LEFT, padx=5, pady=5, fill=BOTH, expand=YES)

        frame_open = Frame(tab_control)
        btn_open = self.__new_button(frame_open, image=self.icons['browse'],
                                     command=self.__open_definition)

        btn_open.place(relx=0.5, rely=0.5, anchor=CENTER)

        tab_control.add(frame_log, text='Log')
        tab_control.add(frame_open, text='+')
        tab_control.pack(fill=BOTH, expand=YES)

        self.components['frame_tabs'] = frame_tabs
        self.components['tab_control'] = tab_control
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
        # TODO update this to use OrderedDict and spread usage
        self.packing['list'][self.packing['indices'][widget]]['flag'] = state

    def __toggle_override(self):
        if self.override:
            self.override = False
            self.components['btn_override'].configure(image=self.icons['switch_off'])
        else:
            self.override = True
            self.components['btn_override'].configure(image=self.icons['switch_on'])

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

    def __open_definition(self):
        files = self.components['btn_open_definition_command']()
        for file in list(files):
            tab_control: Notebook = self.components['tab_control']
            frame_definition = Frame(tab_control)
            name, _ = os.path.basename(file).split('.')
            tab_control.insert(1, frame_definition, text=name)
            tab_control.select(len(tab_control.children) - 2)

            txt_contents = Text(frame_definition, wrap='none',
                                background=self.colors['dark'],
                                foreground=self.font_colors['normal'],
                                insertbackground=self.font_colors['normal'])

            button_panel = Frame(frame_definition)
            btn_close = self.__new_button(button_panel, image=self.icons['close'],
                                          command=lambda: self.__close_tab(tab_control))

            lbl_status = Label(button_panel)

            btn_save = self.__new_button(button_panel, image=self.icons['save'],
                                         command=lambda: self.__save_tab_contents(txt_contents, file, lbl_status))

            btn_reset = self.__new_button(button_panel, image=self.icons['revert'],
                                          command=lambda: self.__reset_tab_contents(txt_contents, file, lbl_status))

            txt_contents.bind('<Key>', lambda e: lbl_status.configure(
                text='*unsaved changes'))  # TODO this triggers on all kinds of keypresses

            btn_close.pack(side=RIGHT, padx=5, pady=5)
            btn_save.pack(side=LEFT, padx=5, pady=5)
            btn_reset.pack(side=LEFT, pady=5)
            lbl_status.pack(side=LEFT, padx=5, pady=5)

            button_panel.pack(side=TOP, fill=X)
            txt_contents.pack(side=BOTTOM, fill=BOTH, expand=YES)

            f = open(file, 'r')
            for line in f.readlines():
                txt_contents.insert('end', line)

    @staticmethod
    def __close_tab(tab_control):
        tab_control.forget(tab_control.select())

    @staticmethod
    def __save_tab_contents(widget, file, label):
        f = open(file, 'w')
        for line in widget.get('1.0', 'end').rstrip('\n'):
            f.write(line)
        f.close()
        label.configure(text='saved')

    @staticmethod
    def __reset_tab_contents(widget, file, label):
        widget.delete('1.0', 'end')
        f = open(file, 'r')
        for line in f.readlines():
            widget.insert('end', line)
        f.close()
        label.configure(text='reverted')

    def __set_directory(self):
        response = filedialog.askopenfilename(
            title="Select file", filetypes=(("Taglist", "*.csv"), ("all files", "*.*")))
        if response != '':
            self.components['entry_path_text'].set(response)
            self.components['btn_generate'].config(state='normal')

    @staticmethod
    def interpret_file(file, delimiter=None, quotechar=None):
        raw_file = open(file, 'r', newline='')
        eval_buffer = []
        index = 0
        for index, line in enumerate(raw_file.readlines()):
            if line.strip(' \t\r\n') and line[0] != '@':
                eval_buffer.append(line)
        interpreted_file = csv.reader(eval_buffer, delimiter=delimiter, quotechar=quotechar, skipinitialspace=True)
        return interpreted_file, index

    @staticmethod
    def get_timestamp(file_friendly=False):
        if file_friendly:
            return datetime.now().strftime('%Y-%m-%d_%Hh%M')
        else:
            return datetime.now().strftime('%Y.%m.%d %H:%M')

    def update_progress(self, force=False):
        current_time = time()
        start_time = self.components['start_time']
        delta_update = current_time - self.components['last_update']
        delta_start = current_time - start_time
        maximum = self.components['bar_progress']['maximum']
        value = self.components['bar_progress']['value']
        update = False
        if force:
            update = True
        else:
            if self.progress_update_cycle < delta_update:
                if value == 0:
                    return

                if delta_start/value*maximum < 30 or 1 < delta_update or delta_start < 10:
                    update = True
        if update:
            self.components['txt_log'].yview_moveto(1)  # ~10% processing time cost for blockgenerator
            self.components['bar_progress'].update()  # ~25% processing time cost for blockgenerator
            self.components['last_update'] = current_time
            self.components['lbl_progress'].configure(text='{}/{}'.format(value, maximum))

    def write_to_log(self, text, font='normal'):
        txt: Text = self.components['txt_log']
        txt.config(state='normal')
        if font in ('normal', 'good'):
            txt.insert('end', self.get_timestamp() + ':\t', 'highlighted')
        txt.insert('end', ''.join(text) + '\n', font)
        if not self.debug_mode:
            txt.config(state='disabled')


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