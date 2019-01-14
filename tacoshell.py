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

    def __init__(self):
        """Initialize"""
        self.EXPERIMENTAL_MODE = False  # Temporary variable for testing extensive program changes

        # ROOT settings
        self.root = Tk()
        Tk.report_callback_exception = self.__on_error
        self.root.title("Shell GUI")
        # self.root.wm_iconbitmap('tacoshell.ico')
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
        self.__set_packing()
        self.__read_xml_config()
        self.__set_theme()
        self.__repack()
        self.__initialization_summary()
        self.root.mainloop()

    def __on_closing(self):
        """Define Tkinter instance close event"""
        self.__save_as_xml()
        if 'window_flags' in self.components.keys():
            self.components['window_flags'].destroy()
        self.root.destroy()

    def __on_error(self, *args):
        """Display Tkinter instance errors"""
        try:
            self.write_to_log(traceback.format_exception(*args), 'bad')
            traceback.print_exc()
        except:
            pass

    def __init_appearance(self):
        """Initialize color presets and buffer icons"""
        self.colors = {'black': '#000000',
                       'dark': '#2B2B2B',
                       'milddark': '#3C3F41',
                       'lightgray': '#A3A3A3',
                       'tabactive': '#515658',
                       'tablazy': '#3C3E3F',
                       'lighttext': '#A3B1BF',
                       'muted': '#3592C4'}

        self.font_colors = {'normal': '#A9B7C6',
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
        self.style.configure('TMenubutton',
                             background=self.colors['dark'],
                             foreground=self.colors['lighttext'])
        self.style.configure("Horizontal.TProgressbar",
                             background=self.colors['muted'])

    @staticmethod
    def __position_window(window, x=None, y=None, width=None, height=None):
        """Position a window on screen, considering boundaries"""
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
        x = max(min(x, screen_width - width - margin), 0)
        y = max(min(y, screen_height - height - margin), 0)

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

    def __add_to_packing(self, index, name, frame_handle, pack_kwargs, flag=True, default=True):
        self.components['packing_indexed'].insert(index, (name, {'widget': frame_handle,
                                                                 'kwargs': pack_kwargs,
                                                                 'flag': flag,
                                                                 'default': default}))

    def __refresh_packing(self):
        self.components['packing'] = OrderedDict(self.components['packing_indexed'])

    def __repack(self):
        """Repack GUI based on flag settings"""
        for _, v in self.components['packing'].items():
            v['widget'].pack_forget()
            if v['flag']:
                v['widget'].pack(v['kwargs'])

    def __open_flag_settings(self):
        """Open soft-configuration of packed elements"""
        if 'window_flags' not in self.components.keys():
            window_flags = Toplevel(self.root)
            window_flags.grab_set()
            window_flags.title("flags")
            self.__position_window(window_flags,
                                   self.root.winfo_rootx() + 50,
                                   self.root.winfo_rooty() + 50,
                                   270,
                                   350)
            window_flags.minsize(width=200, height=200)
            window_flags.attributes('-toolwindow', True)
            window_flags.protocol("WM_DELETE_WINDOW", lambda: self.__tool_window_closing(window_flags))

            frame_flags = Frame(window_flags)
            frame_flags.pack(fill=BOTH, expand=YES)

            v = []
            Button(frame_flags, text='set', command=lambda: self.__set_flags(v)).pack(side=BOTTOM, anchor='e')
            for i, [k, w] in enumerate(self.components['packing'].items()):
                row = Frame(frame_flags)
                Label(row, text=k).pack(side=LEFT)
                v.append(StringVar(row))
                val = 'True{}' if w['flag'] else 'False{}'
                v[-1].set(val.format('(default)' if w['flag'] == w['default'] else ''))
                choices = [('True' if w['flag'] else 'False') + '{}'.format(
                    '(default)' if w['default'] == w['flag'] else ''),
                           'True{}'.format('(default)' if w['default'] else ''),
                           'False{}'.format('(default)' if not w['default'] else '')]
                opt = OptionMenu(row, v[-1], *choices)
                opt.config(width=12)
                opt.pack(side=RIGHT)

                row.pack(side=TOP, fill=X)
                Frame(frame_flags, height=2, borderwidth=1, relief=GROOVE).pack(side=TOP, fill=X)

            self.components['window_flags'] = window_flags
            frame_flags.mainloop()

        elif not self.components['window_flags'].state() == 'normal':
            self.components['window_flags'].deiconify()
            self.components['window_flags'].grab_set()
            self.__position_window(self.components['window_flags'],
                                   self.root.winfo_rootx() + 50,
                                   self.root.winfo_rooty() + 50,
                                   270,
                                   350)

    def __set_flags(self, v):
        """Update flags according to specified in flag settings"""
        for i, [_, w] in enumerate(self.components['packing'].items()):
            w['flag'] = True if v[i].get() in ('True', 'True(default)') else False
        self.__repack()
        if 'flags_changed' not in self.instance_changes:
            self.instance_changes.append('flags_changed')

    def __open_tool_window(self, window_key, v, title='tool', table: list = None, actions: list = None):
        """Generic tool window"""
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
            self.__position_window(window,
                                   self.root.winfo_rootx() + 50,
                                   self.root.winfo_rooty() + 50,
                                   270,
                                   350)
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
            self.__position_window(w, self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50, 270, 350)

    @staticmethod
    def __tool_window_closing(handle):
        """Define a tool window closing event"""
        handle.withdraw()
        handle.grab_release()

    @staticmethod
    def __add_row(window, v, w, i):
        """Add a row to tool window"""
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
        """Add a mod to instance of tool window"""
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
        """Connect to a soft-specified mod"""
        for d in v:
            self.mod_list[d['idx']]['value'] = True if d['var'].get() in ('True', 'True(default)') else False
        for mod in self.mod_list:
            self.__get_ingredients(mod)

    def __provide_child_id(self):
        """Provide hooked mod an ID"""
        self._next_child_id += 1
        return str(self._next_child_id)

    def __get_ingredients(self, mod):
        """Initialize mods, create hooks"""
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
            mod_added = False
            for child in mod_node:
                mod = {'name': child.tag, 'value': self.__bool(child.text), 'default': False}
                self.mod_list.append(mod)
                self.__get_ingredients(mod)
                mod_added = True
            if mod_added:
                self.__refresh_packing()

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
            self.__position_window(self.root, x, y, width, height)

        except:
            traceback.print_exc()

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
    def __write_xml(file, data: list = None):
        """Partly generic method for writing XML"""
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

    def __initialization_summary(self):
        """If notable items occur during initialization, this function will display them in the GUI"""
        for ele in self.init_summary:
            self.write_to_log(ele, 'bad')

    def __init_menu(self):
        """Initialize window top menu"""
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

    def menu_help(self):
        """Pop a help dialogue"""
        messagebox.showinfo("Help", self.help_text)

    def __menu_about(self):
        """Pop an about dialogue"""
        messagebox.showinfo("About", self.about_text)

    def __init_debug(self):
        """Initialize debug frame"""
        frame_debug = Frame(self.root)

        btn_test1 = self.__new_button(frame_debug,
                                      text='test print',
                                      width=15,
                                      fg=self.font_colors['normal'],
                                      command=lambda: self.write_to_log('this is a test'))

        btn_test2 = self.__new_button(frame_debug,
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

    def __init_frame_source(self):
        """Initialize source frame"""
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

    def __path_keypress(self, _):
        """Evaluate entered path"""
        if not self.debug_mode:
            self.components['btn_generate'].config(
                state='normal' if os.path.isfile(self.components['entry_path'].get()) else 'disabled')

    def __init_frame_generate(self):
        """Initialize generate frame"""
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
        frame_progress = Frame(self.root, relief='solid')
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

    def __new_button(self, *args, **kwargs):
        """Create a tk.button with theme"""
        # TODO: Convert to class
        button = TkButton(*args, **kwargs, bg=self.colors['milddark'])
        button.bind("<Enter>", lambda e: button.configure(bg=self.colors['lightgray']))
        button.bind("<Leave>", lambda e: button.configure(bg=self.colors['milddark']))
        return button

    def __init_frame_tabs(self):
        """Initialize tabs frame"""
        frame_tabs = Frame(self.root)
        tab_control = Notebook(frame_tabs)

        frame_log = Frame(tab_control)
        txt_log = ScrollableText(frame_log,
                                 wrap='none',
                                 background=self.colors['dark'],
                                 foreground=self.font_colors['normal'],
                                 insertbackground=self.font_colors['normal'],
                                 state='disabled'
                                 )

        txt_log.tag_configure('normal', foreground=self.font_colors['normal'])
        txt_log.tag_configure('highlighted', foreground=self.font_colors['highlighted'])
        txt_log.tag_configure('bad', foreground=self.font_colors['bad'])
        txt_log.tag_configure('muted', foreground=self.font_colors['muted'])
        txt_log.tag_configure('good', foreground=self.font_colors['good'])
        txt_log.tag_configure('debug', foreground=self.font_colors['debug'])
        txt_log.tag_configure('warning', foreground=self.font_colors['warning'])

        frame_open = Frame(tab_control)
        btn_open = self.__new_button(frame_open, image=self.icons['browse'],
                                     command=self.__open_definition)

        btn_open.place(relx=0.5, rely=0.5, anchor=CENTER)

        tab_control.add(frame_log, text='Log')
        tab_control.add(frame_open, text='➕')
        tab_control.pack(fill=BOTH, expand=YES)

        self.components['tabs'] = []
        self.components['frame_tabs'] = frame_tabs
        self.components['tab_control'] = tab_control
        self.components['txt_log'] = txt_log

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

            txt_contents = ScrollableText(new_tab,
                                          wrap='none',
                                          background=self.colors['dark'],
                                          foreground=self.font_colors['normal'],
                                          insertbackground=self.font_colors['normal'])

            button_panel = Frame(new_tab)
            btn_close = self.__new_button(button_panel, image=self.icons['close'],
                                          command=lambda: self.__close_tab(tab_control))

            lbl_status = Label(button_panel)

            btn_save = self.__new_button(button_panel, image=self.icons['save'],
                                         command=lambda: self.__save_tab_contents(txt_contents, file, lbl_status))

            btn_reset = self.__new_button(button_panel, image=self.icons['revert'],
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

    def __set_directory(self):
        """Browse source directory"""
        response = filedialog.askopenfilename(
            title="Select file", filetypes=(("Taglist", "*.csv"), ("all files", "*.*")))
        if response != '':
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
        # TODO consider averaging the last x seconds
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

    def write_to_log(self, text, font='normal'):
        """Print to GUI txt_log"""
        txt: Text = self.components['txt_log']
        txt.config(state='normal')
        if font in ('normal', 'good'):
            txt.insert('end', self.get_timestamp() + ':\t', 'highlighted')
        txt.insert('end', ''.join(text) + '\n', font)
        if not self.debug_mode:
            txt.config(state='disabled')
        txt.yview_moveto(1)


class ScrollableText(Text):
    def __init__(self, parent, *args, **kwargs):
        # Add search field
        search_handle = Frame(parent)
        # TODO get image as in parameter
        im_next = PhotoImage(Image.open('resources/next.png').resize((20, 20), ANTIALIAS))
        im_prev = PhotoImage(Image.open('resources/previous.png').resize((20, 20), ANTIALIAS))
        # TODO add correct handles for func=
        ShellButton(search_handle,
                    image=im_next,
                    command=self.__search_next
                    ).pack(side=RIGHT, padx=5)
        ShellButton(search_handle,
                    image=im_prev,
                    command=self.__search_previous
                    ).pack(side=RIGHT, padx=[5, 0])
        entry_search = Entry(search_handle, width=10)
        entry_search.pack(side=RIGHT, padx=[5, 0])
        Label(search_handle, text='Search').pack(side=RIGHT)

        scrollbar_vert = AutoScrollbar(index=1,
                                       master=parent,
                                       command=super().yview)
        scrollbar_hori = AutoScrollbar(index=2,
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


class ShellButton(TkButton):
    # TODO: Give ShellButton colors as parameter
    def __init__(self, *args, **kwargs):
        self.color_enter = '#A3A3A3'
        self.color_leave = '#3C3F41'
        super().__init__(*args, **kwargs)
        self.image = kwargs['image']
        super().configure(bg=self.color_leave)
        super().bind("<Enter>", self.__on_enter)
        super().bind("<Leave>", self.__on_leave)

    def __on_enter(self, _):
        self.configure(bg=self.color_enter)

    def __on_leave(self, _):
        self.configure(bg=self.color_leave)


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