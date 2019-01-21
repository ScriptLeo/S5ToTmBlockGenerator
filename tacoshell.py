from tkinter import Tk, filedialog, messagebox, Text, Menu, LEFT, RIGHT, TOP, BOTTOM, BOTH, YES, X, Y, \
    Toplevel, StringVar, BooleanVar, HORIZONTAL, VERTICAL, GROOVE, CENTER, END, INSERT
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
import xml.etree.cElementTree as ElementTree
from xml.dom.minidom import parseString
from collections import OrderedDict
from time import time


class TacoShell:
    """Generic shell class for configurable GUIs"""
    # pyinstaller --onefile --noconsole --icon=tacoshell.ico tacoshell.py

    def __init__(self):
        # TODO: After a new mod is added, restart is required for it to show up in flags - FIX
        #       Place mods in a separate folder

        """Initialize"""
        self.EXPERIMENTAL_MODE = True  # Temporary variable for testing extensive program changes
        self.version = '1.0'

        # ROOT settings
        self.root_window = Tk()
        Tk.report_callback_exception = self.__on_error
        self.root_window.title("Shell GUI")
        # self.root.wm_iconbitmap('tacoshell.ico')
        self.root_window.minsize(width=200, height=200)
        self.root_window.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.root_frame = Frame(self.root_window)
        self.root_frame.pack(fill=BOTH, expand=YES)

        # Declarations
        self.progress_update_cycle = 1/10
        self.debug_mode = False
        self.override = False
        self.help_text = 'This won\'t help you at all..'
        self.about_text = 'TacoShell v' + self.version + '\nby Eivind Brate Midtun'
        self.children = {}
        self._next_child_id = 0
        self.components = {}
        self.instance_changes = []
        self.config_file = 'shellconfig.xml'
        self.mod_list = OrderedDict()
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
        self.__set_packing()
        self.__get_mods()
        self.__read_xml_config()
        self.__position_window(self.root_window, *self.components['window_dimensions'])
        self.__set_theme()
        self.__repack()
        self.__display_initialization_summary()
        self.root_window.mainloop()

    def __on_closing(self):
        """Define Tkinter instance close event"""
        self.__save_as_xml()
        if 'window_flags' in self.components.keys():
            self.components['window_flags'].destroy()
        self.root_window.destroy()

    def __on_error(self, *_):
        """Display Tkinter instance errors"""
        try:
            self.print_error()
        except:
            pass

    def __init_appearance(self):
        """Initialize color presets and buffer icons"""
        self.components['window_dimensions'] = [600, 400]
        self.colors = {'black': '#000000',
                       'dark': '#2B2B2B',
                       'milddark': '#3C3F41',
                       'lightgray': '#5E6366',
                       'tabactive': '#515658',
                       'tablazy': '#3C3E3F',
                       'lighttext': '#A3B1BF',
                       'muted': '#3592C4'}
        self.font_colors = {'normal': '#A9B7C6',
                            'dark': '#2B2B2B',
                            'highlighted': '#A35E9C',
                            'bad': '#DE553F',
                            'warning': '#FFC66D',
                            'good': '#00AA00',
                            'muted': '#3592C4',
                            'debug': '#499C54'}

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
                 {'name': 'switch_off', 'size': (30, 15)},
                 {'name': 'debug_on', 'size': (30, 15)},
                 {'name': 'debug_off', 'size': (30, 15)},
                 {'name': 'next', 'size': default_mini_icon_size},
                 {'name': 'previous', 'size': default_mini_icon_size}]
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
        """Initialize theme"""
        # Defaults
        background_map_default = [('active', self.colors['lightgray']),
                                  ('pressed', self.colors['lightgray'])]
        foreground_map_default = [('active', self.colors['black']),
                                  ('pressed', self.colors['black'])]

        self.style.theme_use('clam')
        self.style.configure("TNotebook", background=self.colors['milddark'])
        self.style.map("TNotebook.Tab",
                       background=[("selected", self.colors['tabactive'])],
                       foreground=[("selected", self.colors['lighttext'])])
        self.style.configure('TNotebook.Tab',
                             background=self.colors['tablazy'],
                             foreground=self.colors['lighttext'])
        self.style.configure('TFrame', background=self.colors['milddark'])
        self.style.map("TButton",
                       background=background_map_default,
                       foreground=foreground_map_default)
        self.style.configure('TButton',
                             background=self.colors['milddark'],
                             foreground=self.colors['lighttext'],
                             relief='raised')
        self.style.configure('TLabel',
                             background=self.colors['milddark'],
                             foreground=self.colors['lighttext'])
        self.style.configure('TEntry',
                             background=self.colors['dark'],
                             foreground=self.colors['lighttext'],
                             fieldbackground=self.colors['milddark'])
        self.style.map("TMenubutton",
                       background=background_map_default,
                       foreground=foreground_map_default)
        self.style.configure('TMenubutton',
                             background=self.colors['dark'],
                             foreground=self.colors['lighttext'])
        self.style.configure("Horizontal.TProgressbar",
                             background=self.colors['muted'])
        self.style.map("TCheckbutton", background=background_map_default)
        self.style.configure("TCheckbutton", background=self.colors['milddark'])
        self.style.map("TRadiobutton", background=background_map_default)
        self.style.configure("TRadiobutton", background=self.colors['milddark'])

    @staticmethod
    def __position_window(window, x=None, y=None, width=None, height=None):
        """Position a window on screen, considering boundaries"""
        # TODO: Fix multimonitor support
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        x = int((screen_width / 2) - (width / 2)) if x is None else int(x)
        y = int((screen_height / 2) - (height / 2)) if y is None else int(y)
        width = window.winfo_rootx() if width is None else int(width)
        height = window.winfo_rooty() if height is None else int(height)

        margin = 10
        # Modify width and height
        width = min(width, screen_width)
        height = min(height, screen_height)

        # Modify x and y
        x = min(max(x, 0), screen_width - width - margin)
        y = min(max(y, 0), screen_height - height - margin)

        window.geometry("{}x{}+{}+{}".format(width, height, x, y))

    def __set_packing(self):
        """Set packing order and parameters"""
        self.components['packing_indexed'] = [
            ('frame_progress', {'widget': self.components['frame_progress'],
                                'kwargs': {'side': BOTTOM, 'fill': X},
                                'default': True}),
            ('frame_generate', {'widget': self.components['frame_generate'],
                                'kwargs': {'side': BOTTOM, 'fill': X},
                                'default': True}),
            ('frame_debug', {'widget': self.components['frame_debug'],
                             'kwargs': {'side': TOP, 'fill': X},
                             'default': False}),
            ('frame_source', {'widget': self.components['frame_source'],
                              'kwargs': {'side': TOP, 'fill': X},
                              'default': True}),
            ('frame_tabs', {'widget': self.components['frame_tabs'],
                            'kwargs': {'side': TOP, 'fill': BOTH, 'expand': YES},
                            'default': True})]
        self.components['packing'] = OrderedDict(self.components['packing_indexed'])
        for _, d in self.components['packing'].items():
            d['flag'] = d['default']

    def add_to_packing(self, name, frame_handle, pack_kwargs, index=None, flag=True, default=True, refresh=True):
        if index is None:
            index = len(self.components['packing_indexed'])
        self.components['packing_indexed'].insert(index, (name, {'widget': frame_handle,
                                                                 'kwargs': pack_kwargs,
                                                                 'flag': flag,
                                                                 'default': default}))
        if refresh:
            self.components['packing'] = OrderedDict(self.components['packing_indexed'])

    def __repack(self):
        """Repack GUI based on flag settings"""
        for _, v in self.components['packing'].items():
            v['widget'].pack_forget()
            if v['flag']:
                v['widget'].pack(v['kwargs'])

    def __set_flags(self, v):
        """Update flags according to specified in flag settings"""
        for i, [_, w] in enumerate(self.components['packing'].items()):
            w['flag'] = True if v[i].get() in ('True', 'True(default)') else False
        self.__repack()
        if 'flags_changed' not in self.instance_changes:
            self.instance_changes.append('flags_changed')

    def __open_tool_window(self, window_key, mem, title='tool', table=None, actions: list = None):
        """Generic tool window"""
        # TODO: Make list scrollable
        window = self.components[window_key] = Toplevel(self.root_frame)
        window.grab_set()
        window.title(title)
        self.__position_window(window,
                               self.root_frame.winfo_rootx() + 50,
                               self.root_frame.winfo_rooty() + 50,
                               270,
                               350)
        window.minsize(width=200, height=200)
        window.attributes('-toolwindow', True)

        frame_container = self.components[window_key + '_container'] = Frame(window)
        frame_container.pack(fill=BOTH, expand=YES)

        frame_bottom = Frame(frame_container, borderwidth=2, relief=GROOVE)
        for action in actions:
            Button(frame_bottom, width=10, text=action['text'], command=action['command']).pack(side=RIGHT, padx=3, pady=3)
        frame_bottom.pack(side=BOTTOM, fill=X)

        for name, obj in table.items():
            self.__add_row(frame_container, mem, name, obj)
        window.focus_set()

    @staticmethod
    def __add_row(window, mem, name, obj):
        """Add a row to tool window"""
        row = Frame(window, borderwidth=2, relief=GROOVE)
        mem.append(StringVar(row))
        val = 'True{}' if obj['flag'] else 'False{}'.format('(default)' if obj['flag'] == obj['default'] else '')
        mem[-1].set(val)

        choices = [('True' if obj['flag'] else 'False') + '{}'.format('(default)' if obj['default'] == obj['flag'] else ''),
                   'True{}'.format('(default)' if obj['default'] else ''),
                   'False{}'.format('(default)' if not obj['default'] else '')]

        opt = OptionMenu(row, mem[-1], *choices)
        opt.config(width=12)
        opt.pack(side=RIGHT, padx=1, pady=1)

        description = Frame(row)
        Label(description, text=name).pack(side=TOP)
        # TODO: Consider changing the extra info is added (flag specific)
        if 'kwargs' in obj.keys():
            if 'side' in obj['kwargs'].keys():
                Label(description, text=str(obj['kwargs']['side'])).pack(side=TOP, anchor='w')
        description.pack(side=LEFT)

        row.pack(side=TOP, fill=X, padx=2, pady=1)

    def __get_mods(self):
        """Checks \mod folder for any mods and adds them"""
        if not os.path.isdir('mods'):
            os.makedirs('mods')
        for file in os.listdir(os.getcwd() + '\mods'):
            name, ext = os.path.splitext(file)
            if ext == '.py':
                flag = {'flag': False, 'default': False}
                self.mod_list[name] = flag

    def __set_mods(self, v):
        """Connect to a soft-specified mod"""
        for i, [k, d] in enumerate(self.mod_list.items()):
            if v[i].get() in ('True', 'True(default)'):
                self.mod_list[k]['flag'] = True
                self.__get_ingredients(k, d)
            else:
                self.mod_list[k]['flag'] = False

    def __provide_child_id(self):
        """Provide hooked mod an ID"""
        self._next_child_id += 1
        return str(self._next_child_id)

    def __get_ingredients(self, name, mod):
        """Initialize mods, create hooks"""
        child_id = self.__provide_child_id()
        try:
            # https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
            # import_module('mods')
            module = import_module('.' + name, 'mods')
            instance = module.make_taco()
            self.children[child_id] = instance
            self.children[child_id].eat_taco(self, child_id)
            self.write_to_log("Added " + name + " to taco")
            self.__repack()

        except:
            self.print_error()
            print("Failed to add ingredient " + mod['name'])

    @staticmethod
    def __bool(string):
        """Convert a string representation of boolean to boolean"""
        return True if string == 'True' else False

    def __read_xml_config(self):
        """Read program configuration from XML"""
        try:
            tree = ElementTree.parse(self.config_file)

            # Read mods (Before flags)
            mod_node = tree.find('mods')
            for child in mod_node:
                name = child.tag
                mod = {'flag': self.__bool(child.text), 'default': False}
                self.mod_list[name] = mod
                if mod['flag']:
                    self.__get_ingredients(name, mod)

            # Read flags
            c = self.components['packing']
            for key in c.keys():
                node = tree.find('flags/' + key)
                c[key]['flag'] = self.__bool(node.text) if node is not None else c[key]['default']

            # Read path
            path_child = tree.find('paths/entry_path_text')
            if path_child is not None:
                self.components['entry_path_text'].set(path_child.text)
                if os.path.isfile(self.components['entry_path_text'].get()):
                    self.components['btn_generate'].config(state='normal')

            # Read window settings
            x = tree.find('window/window_x').text
            y = tree.find('window/window_y').text
            width = tree.find('window/window_width').text
            height = tree.find('window/window_height').text
            self.components['window_dimensions'] = [x, y, width, height]

        except:
            self.print_error(True)

    def __save_as_xml(self):
        """Create data structure for saving to XML"""
        flag_data = []
        for item in self.instance_changes:
            if item == 'flags_changed':
                response = messagebox.askyesno("Unsaved flag changes",
                                               "Save flag settings?")
                if response:
                    for k, v in self.components['packing'].items():
                        flag_data.append({'tag': k, 'value': v['flag']})

        mod_data = []
        for k, d in self.mod_list.items():
            mod_data.append({'tag': k, 'value': d['flag']})

        path_data = []
        if os.path.isfile(self.components['entry_path_text'].get()):
            path_str = self.components['entry_path_text'].get()
            path_data.append({'tag': 'entry_path_text', 'value': path_str})

        window_data = [{'tag': 'window_width', 'value': self.root_window.winfo_width()},
                       {'tag': 'window_height', 'value': self.root_window.winfo_height()},
                       {'tag': 'window_x', 'value': self.root_window.winfo_x()},
                       {'tag': 'window_y', 'value': self.root_window.winfo_y()}]

        save_data = [
            {'tag': 'mods', 'elements': mod_data},
            {'tag': 'flags', 'elements': flag_data},
            {'tag': 'paths', 'elements': path_data},
            {'tag': 'window', 'elements': window_data}
        ]
        self.__write_xml('shellconfig.xml', save_data)

    @staticmethod
    def __write_xml(file, data: list = None):
        """Partly generic method for writing XML"""
        if os.path.isfile(file):
            try:
                tree = ElementTree.parse(file)
                root = tree.getroot()

            except:
                root = ElementTree.Element('root')

        else:
            root = ElementTree.Element('root')

        for element in data:
            child = root.find(element['tag'])
            if child is None:
                child = ElementTree.SubElement(root, element['tag'])

            for data_element in element['elements']:
                sub_child = root.find(element['tag'] + '/' + data_element['tag'])
                if sub_child is None:
                    sub_child = ElementTree.SubElement(child, data_element['tag'])

                sub_child.text = str(data_element['value'])

        xml_str = str(ElementTree.tostring(root), 'utf-8').replace('\n', '').replace('\t', '').encode('utf-8')
        pretty_xml = parseString(xml_str).toprettyxml(newl='\n', indent="\t")
        with open(file, 'w+') as f:
            f.write(pretty_xml)
            f.close()

    def __display_initialization_summary(self):
        """If notable items occur during initialization, this function will display them in the GUI"""
        for ele in self.init_summary:
            self.write_to_log(ele, 'bad')

    def __init_menu(self):
        """Initialize window top menu"""
        menubar = Menu(self.root_frame)

        # Cascade options
        menu_options = Menu(menubar, tearoff=0)
        menu_options.add_command(label="help", command=self.menu_help)
        menu_options.add_command(label="about", command=self.__menu_about)

        # Add to menubar
        mem1 = []
        menubar.add_command(label="flags",
                            command=lambda: self.__open_tool_window(
                                window_key='window_flags',
                                mem=mem1,
                                title='flags',
                                table=self.components['packing'],
                                actions=[{'text': 'set', 'command': lambda: self.__set_flags(mem1)}]))

        mem2 = []
        menubar.add_command(label="mods",
                            command=lambda: self.__open_tool_window(
                                window_key='window_mods',
                                mem=mem2,
                                title='mods',
                                table=self.mod_list,
                                actions=[{'text': 'set', 'command': lambda: self.__set_mods(mem2)}]))

        menubar.add_cascade(label="?", menu=menu_options)
        self.root_window.config(menu=menubar)

    def menu_help(self):
        """Pop a help dialogue"""
        messagebox.showinfo("Help", self.help_text)

    def __menu_about(self):
        """Pop an about dialogue"""
        messagebox.showinfo("About", self.about_text)

    def __init_debug(self):
        """Initialize debug frame"""
        frame_debug = Frame(self.root_frame)

        btn_test1 = self.ShellButton(frame_debug,
                                     text='test print',
                                     width=15,
                                     fg=self.font_colors['normal'],
                                     command=lambda: self.write_to_log('this is a test'))

        btn_test2 = self.ShellButton(frame_debug,
                                     text='Btn 2',
                                     width=15,
                                     fg=self.font_colors['normal'])

        panel_debug = Frame(frame_debug)
        lbl_debug = TkLabel(panel_debug,
                            bg=self.colors['milddark'],
                            fg=self.font_colors['debug'],
                            text="debug",
                            font='semi-bold')
        btn_debug = TkButton(panel_debug,
                             image=self.icons['debug_off'],
                             bg=self.colors['milddark'],
                             activebackground=self.colors['milddark'],
                             borderwidth=0,
                             command=self.__toggle_debug)

        lbl_debug.pack(side=TOP)
        btn_debug.pack(side=BOTTOM)

        panel_override = Frame(frame_debug)
        lbl_override = TkLabel(panel_override,
                               bg=self.colors['milddark'],
                               fg=self.font_colors['warning'],
                               text="override",
                               font='semi-bold')
        btn_override = TkButton(panel_override,
                                image=self.icons['switch_off'],
                                bg=self.colors['milddark'],
                                activebackground=self.colors['milddark'],
                                borderwidth=0,
                                command=self.__toggle_override)

        lbl_override.pack(side=TOP)
        btn_override.pack(side=BOTTOM)

        panel_override.pack(side=RIGHT, padx=5)
        panel_debug.pack(side=RIGHT, padx=[5, 0])
        btn_test1.pack(side=LEFT, padx=5)
        btn_test2.pack(side=LEFT)

        self.components['btn_debug'] = btn_debug
        self.components['btn_override'] = btn_override
        self.components['frame_debug'] = frame_debug

    def __toggle_debug(self):
        """Toggle debugging"""
        if self.debug_mode:
            if not os.path.isfile(self.components['entry_path'].get()):
                self.components['btn_generate'].config(state='disabled')
            self.components['txt_log'].config(state='disabled')
            self.debug_mode = False
            self.components['btn_debug'].configure(image=self.icons['debug_off'])
            self.write_to_log('Debug mode deactivated', 'debug')
        else:
            self.components['btn_generate'].config(state='normal')
            self.components['txt_log'].config(state='normal')
            self.debug_mode = True
            self.components['btn_debug'].configure(image=self.icons['debug_on'])
            self.write_to_log('Debug mode activated', 'debug')

    def __toggle_override(self):
        """Toggle override option which can be used to heighten debug mode"""
        if self.override:
            self.override = False
            self.components['btn_override'].configure(image=self.icons['switch_off'])
            self.write_to_log('Override deactivated', 'warning')
        else:
            self.override = True
            self.components['btn_override'].configure(image=self.icons['switch_on'])
            self.write_to_log('Override activated', 'warning')

    def __create_element_source(self, handle, btn_txt='?', btn_image=None, filetypes=None, validation_func=None,
                                index=None, flag=True, default=True):
        # TODO: Convert to using this
        if handle in self.components.keys():
            self.init_summary.append('Key \'{}\' was already registered in \'self.components\', but was added'
                                     .format(handle))

        frame = Frame(self.root_frame)
        var = StringVar()
        entry = Entry(frame, textvariable=var)
        button = self.ShellButton(frame)

        kwargs = {'command': lambda: self.__browse_file(filetypes=filetypes, var=var)}
        if btn_image is None:
            kwargs['text'] = btn_txt
        else:
            kwargs['image'] = btn_image
        button.configure(**kwargs)

        if validation_func is not None:
            var.trace('w', validation_func)

        button.pack(side=LEFT, padx=5, pady=5)
        entry.pack(side=LEFT, fill=X, expand=YES, padx=[0, 5])

        self.components[handle] = {'frame': frame,
                                   'entry': entry,
                                   'button': button}

        self.add_to_packing(handle, frame, {'side': TOP, 'fill': X}, index=index, flag=flag, default=default)

    def __init_frame_source(self):
        """Initialize source frame"""
        frame_source = Frame(self.root_frame)
        self.components['entry_path_text'] = StringVar()
        entry_path = Entry(frame_source, textvariable=self.components['entry_path_text'])
        btn_set_directory = self.ShellButton(frame_source,
                                             image=self.icons['browse_excel'],
                                             command=lambda: self.__browse_file(entry_path))
        entry_path.bind(sequence='<KeyRelease>', func=self.__path_keypress)

        btn_set_directory.pack(side=LEFT, padx=5, pady=5)
        entry_path.pack(side=LEFT, fill=X, expand=YES, padx=[0, 5])

        self.components['frame_source'] = frame_source
        self.components['entry_path'] = entry_path
        self.components['btn_set_directory'] = btn_set_directory

    def __path_keypress(self, _):
        """Evaluate entered path"""
        if not self.debug_mode:
            self.components['btn_generate'].config(
                state='normal' if os.path.isfile(self.components['entry_path'].get()) else 'disabled')

    def __init_frame_generate(self):
        """Initialize generate frame"""
        frame_generate = Frame(self.root_frame)
        btn_generate = self.ShellButton(frame_generate,
                                        image=self.icons['play'],
                                        state='disabled',
                                        command=self.__generate_command)

        btn_stop = self.ShellButton(frame_generate,
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
        """Define stop command action"""
        self.components['STOP_COMMAND'] = True

    def __generate_command(self):
        """Wrap the soft-hooked command"""
        c = self.components
        c['STOP_COMMAND'] = False
        c['btn_stop'].configure(state='normal')
        c['btn_generate'].configure(state='disabled')
        c['lbl_progress'].config(text='Processing')
        self.__clear_log()
        self.write_to_log('Started processing', 'good')
        self.components['count_failed'] = 0
        start_time = c['start_time'] = c['last_update'] = time()

        try:
            c['btn_generate_command']()
            self.write_to_log('Finished processing in {} seconds\n'.format(str(time() - start_time)), 'good')
            if not self.components['STOP_COMMAND']:
                c['bar_progress']['value'] = c['bar_progress']['maximum']
            c['lbl_progress'].config(text='Completed')
            c['btn_stop'].configure(state='disabled')
            c['btn_generate'].configure(state='normal')

        except Exception as e:
            self.write_to_log('Stopped code execution due to error\n'.format(str(time() - start_time)), 'bad')
            c['btn_stop'].configure(state='disabled')
            c['btn_generate'].configure(state='normal')
            c['lbl_progress'].config(text='Error')
            c['txt_log'].yview_moveto(1)
            raise e

    def __clear_log(self):
        txt = self.components['txt_log']
        txt.config(state='normal')
        txt.delete('1.0', END)
        if not self.debug_mode:
            txt.config(state='disabled')

    def __init_frame_progress(self):
        """Initialize progress frame"""
        frame_progress = Frame(self.root_frame, relief='solid')
        bar_progress = Progressbar(frame_progress, mode='determinate')
        lbl_progress = Label(frame_progress, text='Idle', width=15)

        var_est = StringVar()
        lbl_estimated_time = Label(frame_progress, textvariable=var_est, width=15)

        lbl_progress.pack(side=LEFT, padx=5)
        lbl_estimated_time.pack(side=RIGHT, padx=5)
        bar_progress.pack(side=RIGHT, fill=X, pady=5, expand=YES)

        self.components['count_failed'] = 0  # Counter for loops that that were expected but that were skipped
        self.components['var_estimated_time_remaining'] = var_est
        self.components['frame_progress'] = frame_progress
        self.components['lbl_progress'] = lbl_progress  # TODO change labels to StringVar()
        self.components['bar_progress'] = bar_progress

    def __create_element_text(self, name, tabbed=False):
        # TODO: Create generic text elements with this method
        pass

    def __init_frame_tabs(self):
        """Initialize tabs frame"""
        frame_tabs = Frame(self.root_frame)
        tab_control = Notebook(frame_tabs)

        frame_log = Frame(tab_control)
        txt_log = self.ScrollableText(frame_log,
                                      wrap='none',
                                      background=self.colors['dark'],
                                      foreground=self.font_colors['normal'],
                                      insertbackground=self.font_colors['normal'],
                                      state='disabled')

        for key, color in self.font_colors.items():
            txt_log.tag_configure(key, foreground=color)

        frame_open = Frame(tab_control)
        btn_open = self.ShellButton(frame_open, image=self.icons['browse'],
                                    command=self.__open_definition)

        btn_open.place(relx=0.5, rely=0.5, anchor=CENTER)

        tab_control.add(frame_log, text='Log')
        tab_control.add(frame_open, text='➕')
        tab_control.pack(fill=BOTH, expand=YES)

        self.components['btn_open_definition_command'] = self.__open_files
        self.components['tabs'] = []
        self.components['frame_tabs'] = frame_tabs
        self.components['tab_control'] = tab_control
        self.components['txt_log'] = txt_log

    @staticmethod
    def __open_files():
        """Default method connected to open tab"""
        return filedialog.askopenfilenames(title="Select file",
                                           filetypes=([("All files", ".*")]))

    def __open_definition(self):
        """Open a file in a tab"""
        files = self.components['btn_open_definition_command']()
        for file in list(files):
            tab_control: Notebook = self.components['tab_control']
            new_tab = Frame(tab_control)
            name, _ = os.path.basename(file).split('.')
            tab_control.insert(tab_control.index(END) - 1, new_tab, text=name)
            self.components['tabs'].append(new_tab)
            tab_control.select(tab_control.index(END) - 2)

            txt_contents = self.ScrollableText(new_tab,
                                               wrap='none',
                                               background=self.colors['dark'],
                                               foreground=self.font_colors['normal'],
                                               insertbackground=self.font_colors['normal'])

            button_panel = Frame(new_tab)
            btn_close = self.ShellButton(button_panel, image=self.icons['close'],
                                         command=lambda: self.__close_tab(tab_control))

            lbl_status = Label(button_panel)

            btn_save = self.ShellButton(button_panel, image=self.icons['save'],
                                        command=lambda: self.__save_tab_contents(txt_contents, file, lbl_status))

            btn_reset = self.ShellButton(button_panel, image=self.icons['revert'],
                                         command=lambda: self.__reset_tab_contents(txt_contents, file, lbl_status))

            txt_contents.bind('<Key>', lambda e: lbl_status.configure(
                text='*unsaved changes'))  # TODO this triggers on all kinds of keypresses

            btn_close.pack(side=RIGHT, padx=5)
            btn_save.pack(side=LEFT, padx=5)
            btn_reset.pack(side=LEFT)
            lbl_status.pack(side=LEFT, padx=5)

            button_panel.pack(side=TOP, fill=X, pady=(5, 0))
            txt_contents.pack(side=BOTTOM, fill=BOTH, expand=YES)

            f = open(file, 'r')
            for line in f.readlines():
                txt_contents.insert('end', line)

    def __close_tab(self, tab_control):
        """Close a tab"""
        for tab in self.components['tabs']:
            if tab._w == tab_control.select():
                tab.destroy()
                self.components['tabs'].remove(tab)
                tab_control.select(tab_control.index(END) - 2)
                break

    @staticmethod
    def __save_tab_contents(widget, file, label):
        """Save changes of opened file back to file"""
        f = open(file, 'w')
        for line in widget.get('1.0', 'end').rstrip('\n'):
            f.write(line)
        f.close()
        label.configure(text='saved')

    @staticmethod
    def __reset_tab_contents(widget, file, label):
        """Reset changes done in file back to file"""
        widget.delete('1.0', 'end')
        f = open(file, 'r')
        for line in f.readlines():
            widget.insert('end', line)
        f.close()
        label.configure(text='reverted')

    @staticmethod
    def __val(d, key):
        """Helper"""
        return d[key] if key in d.keys() else None

    def __browse_file(self, var, filetypes=None):
        """Browse source directory"""
        if self.EXPERIMENTAL_MODE:
            kwargs = {'title': "Select file"}
            if filetypes is not None:
                kwargs['filetypes'] = filetypes
            response = filedialog.askopenfilename(**kwargs)
        else:
            response = filedialog.askopenfilename(title="Select file",
                                                  filetypes=(("Taglist", "*.csv"), ("all files", "*.*")))

        if response != '':
            if self.EXPERIMENTAL_MODE:
                var.set(response)
            else:
                self.components['entry_path_text'].set(response)
                self.components['btn_generate'].config(state='normal')

    @staticmethod
    def interpret_file(file, delimiter=None, quotechar=None, buffermode=''):
        """Interpret .csv"""
        raw_file = open(file, 'r', newline='')
        eval_buffer = []
        index = 0  # This will return as a count
        for index, line in enumerate(raw_file.readlines()):
            strip_line = line.strip(' \t\r\n')
            if strip_line[0] != '@':
                eval_buffer.append(strip_line)

        kwargs = {'delimiter': delimiter,
                  'skipinitialspace': True}
        if quotechar is None:
            kwargs['quoting'] = csv.QUOTE_NONE
        else:
            kwargs['quotechar'] = quotechar
        csv_interator = csv.reader(eval_buffer, **kwargs)

        if buffermode == 'list':
            # Returns a buffer in the form of a list instead of iterator
            out_buffer = [line for line in csv_interator]
            interpretation = out_buffer
        elif buffermode == 'dict':
            # Returns a buffer in the form of a dict with the first index element as key and the second as value
            # Requires return from iterator to be exactly two values
            out_buffer = {key: value for key, value in csv_interator}
            interpretation = out_buffer
        else:
            interpretation = csv_interator

        return interpretation, index

    @staticmethod
    def get_timestamp(file_friendly=False):
        """Create a timestamp"""
        if file_friendly:
            return datetime.now().strftime('%Y-%m-%d_%Hh%M')
        else:
            return datetime.now().strftime('%Y.%m.%d %H:%M')

    def update_progress(self, failed=False, force=False):
        """Update progress frame elements through hook"""
        current_time = time()
        start_time = self.components['start_time']
        delta_update = current_time - self.components['last_update']
        delta_start = current_time - start_time
        maximum = self.components['bar_progress']['maximum']
        value = self.components['bar_progress']['value']
        update = False
        if failed:
            self.components['count_failed'] += 1
        count_failed = self.components['count_failed']
        num = delta_start*(maximum - count_failed)
        det = (value - count_failed)
        estimated_time_remaining = round(num/det - delta_start) if 0 < det else 0

        if force:
            update = True
        else:
            if self.progress_update_cycle < delta_update:
                if estimated_time_remaining < 30 or 1 < delta_update or delta_start < 10:
                    update = True
        if update:
            self.components['var_estimated_time_remaining'].set('{}s'.format(estimated_time_remaining))
            self.components['bar_progress'].update()  # ~25% processing time cost for blockgenerator
            self.components['last_update'] = current_time
            self.components['lbl_progress'].configure(text='{}/{}'.format(value, maximum))

    def write_to_log(self, text, font='normal', timestamp=True):
        """Print to GUI txt_log"""
        txt: Text = self.components['txt_log']
        txt.config(state='normal')
        if font in ('normal', 'good') and timestamp:
            txt.insert('end', self.get_timestamp() + ':\t', 'highlighted')
        txt.insert('end', ''.join(text) + '\n', font)
        if not self.debug_mode:
            txt.config(state='disabled')
        txt.yview_moveto(1)

    def print_error(self, suppress_from_gui=False):
        logging.exception("message")
        formatted_lines = traceback.format_exc()
        traceback.print_exc()
        if not suppress_from_gui:
            self.write_to_log(formatted_lines, 'bad')

    class ShellButton(TkButton):
        # TODO: Give ShellButton colors as parameter
        def __init__(self, *args, **kwargs):
            self.color_enter = '#A3A3A3'
            self.color_leave = '#3C3F41'
            super().__init__(*args, **kwargs)
            if 'image' in kwargs.keys():  # Store image so it is not garbage collected
                self.image = kwargs['image']
            super().configure(bg=self.color_leave)
            super().bind("<Enter>", self.__on_enter)
            super().bind("<Leave>", self.__on_leave)

        def __on_enter(self, _):
            self.configure(bg=self.color_enter)

        def __on_leave(self, _):
            self.configure(bg=self.color_leave)

    class ScrollableText(Text):
        def __init__(self, parent, *args, **kwargs):
            # Add search field
            search_handle = Frame(parent)
            # TODO get image as in parameter
            im_next = PhotoImage(Image.open('resources/next.png').resize((20, 20), ANTIALIAS))
            im_prev = PhotoImage(Image.open('resources/previous.png').resize((20, 20), ANTIALIAS))
            # TODO add correct handles for func=
            TacoShell.ShellButton(search_handle,
                                  image=im_next,
                                  command=self.__search_next
                                  ).pack(side=RIGHT, padx=5)
            TacoShell.ShellButton(search_handle,
                                  image=im_prev,
                                  command=self.__search_previous
                                  ).pack(side=RIGHT, padx=[5, 0])
            entry_search = Entry(search_handle, width=10)
            entry_search.pack(side=RIGHT, padx=[5, 0])
            Label(search_handle, text='Search').pack(side=RIGHT)

            scrollbar_vert = TacoShell.AutoScrollbar(index=1,
                                                master=parent,
                                                command=super().yview)
            scrollbar_hori = TacoShell.AutoScrollbar(index=2,
                                                master=parent,
                                                orient=HORIZONTAL,
                                                command=super().xview)

            search_var = BooleanVar()
            search_var.set(False)
            txt_var = BooleanVar()
            txt_var.set(True)

            # TODO: Consider packing so that each element points in a unique direction,
            #       repacking all elements will be obsolete
            scrollbar_hori.pack_group = scrollbar_vert.pack_group = [
                {'handle': search_handle, 'flag': search_var, 'old_flag': BooleanVar(),
                 'kwargs': {'side': TOP, 'fill': X, 'pady': (5, 0)}},
                {'handle': scrollbar_vert, 'flag': BooleanVar(), 'old_flag': BooleanVar(),
                 'kwargs': {'side': RIGHT, 'fill': Y, 'pady': (5, 25)}},
                {'handle': scrollbar_hori, 'flag': BooleanVar(), 'old_flag': BooleanVar(),
                 'kwargs': {'side': BOTTOM, 'fill': X, 'padx': (5, 5)}},
                {'handle': super(), 'flag': txt_var, 'old_flag': BooleanVar(),
                 'kwargs': {'side': LEFT, 'fill': BOTH, 'expand': YES, 'padx': 5, 'pady': 5}}]

            self.entry_search = entry_search
            self.text_widget = super()
            super().__init__(parent, *args, **kwargs)
            super().configure(xscrollcommand=scrollbar_hori.set)
            super().configure(yscrollcommand=scrollbar_vert.set)
            super().bind('<Control-f>', lambda e: self.__hotkey_toggle(search_var, scrollbar_hori))

        @staticmethod
        def __hotkey_toggle(var, aut):
            """Pressed ctrl+f"""
            var.set(not var.get())
            aut.pack_all()

        def __search_next(self):
            start_idx = self.text_widget.index(INSERT)
            # text = self.text_widget.get('1.0', 'end-1c')
            text = self.text_widget.get(start_idx, 'end-1c')
            text_array = text.splitlines()
            try:
                # TODO include column position
                offset_idx = [i for i, s in enumerate(text_array) if self.entry_search.get() in s]
                idx = int(start_idx.split('.')[0]) + offset_idx[0] + 1  # TODO: Fix hacked code
                self.text_widget.see(str(idx) + '.0')
                print('{} at idx {}'.format(self.entry_search.get(), idx))

            except:
                pass

        @staticmethod
        def __search_previous():
            # TODO: Finish method
            pass

    class AutoScrollbar(Scrollbar):
            """Scrollbars that auto-hide themselves"""
            def __init__(self,
                         shell=None,
                         index=None,
                         master=None,
                         orient=VERTICAL,
                         command=None,
                         pack_group=None):
                self.pack_group = pack_group
                self.index = index
                self.shell = shell
                super().__init__(master=master, orient=orient, command=command)

            def set(self, lo, hi):
                pg = self.pack_group
                if float(lo) <= 0.0 and 1.0 <= float(hi):
                    pg[self.index]['flag'].set(False)
                else:
                    pg[self.index]['flag'].set(True)
                self.pack_all()
                Scrollbar.set(self, lo, hi)

            def pack_all(self):
                pg = self.pack_group
                for w in pg:
                    if w['old_flag'].get() and not w['flag'].get():  # Change from True to False
                        w['handle'].pack_forget()
                        w['old_flag'].set(w['flag'].get())

                    elif w['flag'].get() and not w['old_flag'].get():  # Change from False to True
                        for w_ in pg:
                            w_['handle'].pack_forget()
                            if w_['flag'].get():  # Check if member should be packed
                                w_['handle'].pack(**w_['kwargs'])
                                w_['old_flag'].set(w_['flag'].get())
                        return


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