# "SimitConfigurationComparisonTool"
# Comparison of SIMIT PIQ and DB files
# by
# Eivind Inderøy and
# Eivind Brate Midtun
# Version release 06.11.2018

import os
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import Frame, Button, Entry, Label, Checkbutton, Radiobutton
from multiprocessing import Process, Value
import time
from tacoshell import TacoShell


class SimitConfigurationComparisonTool:

    def __init__(self):
        self.parent: TacoShell = None
        self.child_id = None
        self.progressbar = None

        self.entry_output_path = None
        self.entry_new_path = None
        self.entry_old_path = None
        self.ignore_var = IntVar()
        self.mode = IntVar()
        self.output = None

        self.program_mode = 0  # 0: Normal, 1: Debug
        self.date_release = 'Release@23-Nov-2018'
        self.output_field_separator = '; '
        self.my_process = Process
        self.shared_status = Value('i', 0)
        self.shared_file_count = Value('i', 0)
        self.shared_file_total = Value('i', 0)
        self.shared_line_count = Value('d', 0.0)
        self.time_of_start = time

    @staticmethod
    def list_files(main_path: str):
        '''
        Find all files with .txt format in folder/sub folders in given path.

        :param main_path:
        :return:
        '''
        file_list = []
        for subdir, dirs, files in os.walk(main_path):
            for file in files:
                file_path = str(subdir + os.sep + file)
                if file_path.endswith(".txt"):
                    file_list.append([main_path, file_path.replace(main_path, '')])

        return file_list

    def buffer_file(self, file):
        '''
        Append text files in buffer.

        :param file:
        :return buffer:
        '''
        with open(file, 'rb') as f:
            s = f.read()
            f.close()
            encodings = ['utf-8', 'iso-8859-1']
            for encoding in encodings:
                try:
                    buffer = s.decode(encoding).split('\n')
                    break
                except UnicodeDecodeError:
                    pass
            else:
                buffer = s.decode('utf-8', 'ignore').split('\n')

        buffer[0] = ''.join(c for c in buffer[0] if c.isprintable()) \
            .replace(self.output_field_separator, ' ')  # First line is cleared of remaining encoding data

        if self.ignore_var:
            self.adapt_to_simit_export(buffer)

        return buffer

    @staticmethod
    def adapt_to_simit_export(buffer):
        '''

        :param buffer:
        :return:
        '''
        array = buffer[1].split('\t')
        idx_of_default = array.index('Default')
        idx_of_type = array.index('Type')
        if "Symbol" in array:
            idx_of_symbol = array.index('Symbol')
        else:
            idx_of_symbol = -1
        if "InOut" in array:
            idx_of_inout = array.index('InOut')
        else:
            idx_of_inout = -1
        if "ScalingLowerPhys" in array:
            idx_of_scalinglowerphys = array.index('ScalingLowerPhys')
        else:
            idx_of_scalinglowerphys = -1
        if "ScalingUpperPhys" in array:
            idx_of_scalingupperphys = array.index('ScalingUpperPhys')
        else:
            idx_of_scalingupperphys = -1

        for line in reversed(buffer[2:]):
            new_line = line.split('\t')
            new_line = [x.lstrip(' ').rstrip(' ') for x in new_line]
            if idx_of_symbol < len(new_line):
                if new_line[idx_of_symbol] == '':
                    buffer.remove(line)

        for list_idx, line in enumerate(buffer[2:], 2):
            new_line = line.split('\t')
            new_line = [x.lstrip(' ').rstrip(' ') for x in new_line]

            if idx_of_default < len(new_line):
                if new_line[idx_of_default] in ('False', '0'):
                    new_line[idx_of_default] = ''

                elif new_line[idx_of_default] == 'True':
                    new_line[idx_of_default] = '1'

            if idx_of_type < len(new_line):
                new_line[idx_of_type] = new_line[idx_of_type].lower()

            if idx_of_inout < len(new_line):
                if new_line[idx_of_inout] in ('ID', 'IW'):
                    new_line[idx_of_inout] = 'ID/IW'

            if idx_of_scalinglowerphys < len(new_line):
                if new_line[idx_of_scalinglowerphys].endswith('.0'):
                    new_line[idx_of_scalinglowerphys] = new_line[idx_of_scalinglowerphys][:-2]

            if idx_of_scalingupperphys < len(new_line):
                if new_line[idx_of_scalingupperphys].endswith('.0'):
                    new_line[idx_of_scalingupperphys] = new_line[idx_of_scalingupperphys][:-2]

            buffer[list_idx] = '\t'.join(new_line)

    def set_directory(self, widget, browse_folder=False):
        '''
        Select directory for files.

        :return:
        '''
        response = ''
        if self.mode.get() == 1 or browse_folder:
            response = filedialog.askdirectory()
        elif self.mode.get() == 2:
            response = filedialog.askopenfilename()

        if response != '':
            widget.delete(0, END)
            widget.insert(0, response)
            widget.xview_moveto(1.0)

    def verify_paths(self):
        message = ''
        if not self.exists(self.entry_old_path):
            message += "-Selected 'Old dir' does not exist\n"
        if not self.exists(self.entry_new_path):
            message += "-Selected 'New dir' does not exist\n"
        if self.entry_old_path.get() == self.entry_new_path.get():
            message += "-'New dir' is equal to 'Old dir'\n"
        if not self.exists(self.entry_output_path, True):
            message += "-Selected 'target' path does not exist\n"
        if message != '':
            mode_str = 'Folder' if self.mode.get() == 1 else 'File'
            messagebox.showinfo("Warning", "Invalid directories (Mode=" + mode_str + "):\n" + message)
            return False
        return True

    def exists(self, widget, as_folder=False):
        if self.mode.get() == 1 or as_folder:
            return True if os.path.isdir(widget.get()) else False
        elif self.mode.get() == 2:
            return True if os.path.isfile(widget.get()) else False

    def run(self):
        if not self.verify_paths():
            return
        self.compare_files(self.entry_old_path.get(),
                           self.entry_new_path.get(),
                           self.entry_output_path.get(),
                           self.shared_status,
                           self.shared_file_count,
                           self.shared_file_total,
                           self.shared_line_count,
                           self.mode.get())

    def compare_files(self, file_path_old, file_path_new, output_path,
                      _status, _file_count, _file_total, _line_count,
                      mode):
        # Listed files
        file_paths_old = self.list_files(file_path_old)
        file_paths_new = self.list_files(file_path_new)
        _file_total.value = len(file_paths_old)

        # Listed changes
        list_line_changed = []
        list_line_removed = []
        list_line_added = []
        list_file_changed = []
        _status.value = 1  # Processing
        print('Processing')
        count_file = 0

        # Start searching through old files
        for file_old in file_paths_old.copy():
            count_file += 1
            _file_count.value = count_file
            old_directory = file_old[0]
            filename_old = file_old[1]

            # Start searching through new files
            for file_new in file_paths_new.copy():
                new_directory = file_new[0]
                filename_new = file_new[1]

                # Compare same files from different folders
                if (filename_old == filename_new) or mode == 2:
                    buffer_old = self.buffer_file(old_directory + filename_old)
                    buffer_new = list(enumerate(self.buffer_file(new_directory + filename_new), 1))
                    file_paths_new.remove(file_new)
                    file_paths_old.remove(file_old)
                    file_was_changed = False
                    count_line = 0
                    size = len(buffer_old)

                    # Loop through lines in buffer_old except header
                    for line_old in buffer_old:
                        count_line += 1
                        _line_count.value = (count_line / size) * 100
                        array = line_old.split('\t')
                        symbol_old = array[0].lstrip(' ')
                        idx = 0
                        line_not_found = False

                        # Loop through lines in buffer_new
                        while 0 < len(buffer_new) > idx:
                            line_new = buffer_new[idx][1]
                            array_new = line_new.split('\t')
                            symbol_new = array_new[0].lstrip(' ')

                            if symbol_old == symbol_new:
                                line_not_found = True

                                # Accepting trailing blank space
                                # Remove trailing '\n'. These are added by the append in buffer_file.
                                if line_new.rstrip('\n').rstrip(' ') != line_old.rstrip('\n').rstrip(' '):
                                    # Handle changed
                                    list_line_changed.append(
                                             # First line
                                             filename_old + self.output_field_separator +
                                             "Old" + self.output_field_separator +
                                             "Changed" + self.output_field_separator +
                                             symbol_old + self.output_field_separator +
                                             str(count_line) + self.output_field_separator +
                                             line_old.replace('\t', ' ').rstrip('\n') +
                                             '\n' +
                                             # Second line
                                             filename_new + self.output_field_separator +
                                             "New" + self.output_field_separator +
                                             "Changed" + self.output_field_separator +
                                             symbol_new + self.output_field_separator +
                                             str(buffer_new[idx][0]) + self.output_field_separator +
                                             line_new.replace('\t', ' ').rstrip('\n')
                                             )
                                    file_was_changed = True
                                buffer_new.pop(idx)
                                break
                            idx += 1

                        if not line_not_found:
                            # Handle not found
                            list_line_removed.append(filename_old + self.output_field_separator +
                                                     "Old" + self.output_field_separator +
                                                     "Removed" + self.output_field_separator +
                                                     symbol_old + self.output_field_separator +
                                                     str(count_line) + self.output_field_separator +
                                                     line_old.replace('\t', '   ').rstrip('\n')
                                                     )
                            file_was_changed = True

                    # Handle remaining in buffer_new (new items)
                    for element in buffer_new:
                        c = element[0]
                        line = element[1]
                        array_new = line.split('\t')
                        symbol_new = array_new[0]
                        list_line_added.append(filename_new + self.output_field_separator +
                                               "New" + self.output_field_separator +
                                               "Added" + self.output_field_separator +
                                               symbol_new + self.output_field_separator +
                                               str(c) + self.output_field_separator +
                                               line.replace('\t', ' ').rstrip('\n')
                                               )
                        file_was_changed = True

                    # Note that file was changed
                    if file_was_changed:
                        list_file_changed.append(file_old)

        # Write to output
        self.output = open(output_path + "\\Comparison" + self.parent.get_timestamp(True) + ".csv", "w+",
                           errors='ignore', encoding='iso-8859-1')

        # Description of which files were compared
        self.write("Compared file '" + file_path_old + "' with '" + file_path_new, new_line=False)
        # line = "Compared file '" + file_path_old + "' with '" + file_path_new
        # output.write(line)
        # self.parent.write_to_log(line, 'muted', False)

        # removed files
        if 0 < len(file_paths_old):
            self.write('Removed files:')
            # output.write("\nRemoved files:")
            # self.parent.write_to_log("\nRemoved files:", 'warning', False)
            for line in file_paths_old:
                self.write(''.join(line), font='bad')
                # line_ = '\n' + ''.join(line)
                # output.write(line_)
                # self.parent.write_to_log(line_, 'warning', False)
        else:
            self.write('No removed files')
            # output.write("\nNo removed files")
            # self.parent.write_to_log("\nNo removed files", 'good', False)

        # new files
        if 0 < len(file_paths_new):
            self.write('Added files:')
            # output.write("\nAdded files:")
            # self.parent.write_to_log("\nAdded files:", 'warning', False)
            for line in file_paths_new:
                self.write(''.join(line), font='good')
                # line_ = '\n' + ''.join(line)
                # output.write(line_)
                # self.parent.write_to_log(line_, 'warning', False)
        else:
            self.write('No added files')
            # output.write("\nNo added files")
            # self.parent.write_to_log("\nNo added files", 'good', False)

        # changed files
        if 0 < len(list_file_changed):
            self.write('Changed files:')
            # output.write("\nChanged files:")
            # self.parent.write_to_log("\nChanged files:", 'warning', False)
            for line in list_file_changed:
                self.write(''.join(line), font='warning')
                # line_ = '\n' + ''.join(line)
                # output.write(line_)
                # self.parent.write_to_log(line_, 'warning', False)

        else:
            self.write('No change in files')
            # output.write("\nNo change in files")
            # self.parent.write_to_log("\nNo change in files", 'good', False)

        if 0 < len(list_line_changed) or 0 < len(list_line_removed) or 0 < len(list_line_added):
            line = "Filename" + self.output_field_separator + \
                   "From" + self.output_field_separator + \
                   "Action" + self.output_field_separator + \
                   "Symbol" + self.output_field_separator + \
                   "Line number" + self.output_field_separator + \
                   "Line text"
            self.write(line.replace('\r', ''))
            # output.write(line)
            # self.parent.write_to_log(line, 'muted', False)

        for line in list_line_changed:
            self.write(line.replace('\r', ''), font='warning')
            # line_ = '\n' + line.replace('\r', '')
            # output.write(line_)
            # self.parent.write_to_log(line_, 'warning', False)

        for line in list_line_removed:
            self.write(line.replace('\r', ''), font='bad')
            # line_ = '\n' + line.replace('\r', '')
            # output.write(line_)
            # self.parent.write_to_log(line_, 'bad', False)

        for line in list_line_added:
            self.write(line.replace('\r', ''), font='good')
            # line_ = '\n' + line.replace('\r', '')
            # output.write(line_)
            # self.parent.write_to_log(line_, 'good', False)

        self.output.close()

    def write(self, line, new_line=True, font='normal'):
        self.output.write(('\n' if new_line else '') + line)
        self.parent.write_to_log(line, font, False)

    def init_frame(self, parent):
        frame_container = Frame(parent, borderwidth=2, relief='raised')
        row_1 = Frame(frame_container)
        lbl_mode = Label(row_1, text='Mode')
        self.mode.set(1)
        radio_button_1 = Radiobutton(row_1, text="Folder", variable=self.mode, value=1)
        radio_button_2 = Radiobutton(row_1, text="File", variable=self.mode, value=2)

        lbl_mode.pack(side=LEFT)
        radio_button_1.pack(side=LEFT)
        radio_button_2.pack(side=LEFT)

        row_2 = Frame(frame_container)
        self.entry_old_path = Entry(row_2)
        btn_old_path = Button(row_2, text="Old dir", width=7,
                              command=lambda: self.set_directory(self.entry_old_path))

        btn_old_path.pack(side=LEFT, padx=[0, 5])
        self.entry_old_path.pack(side=RIGHT, fill=X, expand=YES)

        row_3 = Frame(frame_container)
        self.entry_new_path = Entry(row_3)
        btn_new_path = Button(row_3, text="New dir", width=7,
                              command=lambda: self.set_directory(self.entry_new_path))

        btn_new_path.pack(side=LEFT, padx=[0, 5])
        self.entry_new_path.pack(side=RIGHT, fill=X, expand=YES)

        row_4 = Frame(frame_container)
        check = Checkbutton(row_4, variable=self.ignore_var)
        lbl_check = Label(row_4, text="Either was exported from SIMIT")

        check.pack(side=LEFT)
        lbl_check.pack(side=LEFT)

        row_5 = Frame(frame_container)
        self.entry_output_path = Entry(row_5)
        self.entry_output_path.insert(0, os.path.dirname(sys.executable))
        self.entry_output_path.xview_moveto(1.0)
        btn_output_path = Button(row_5, text="Target", width=7,
                                 command=lambda: self.set_directory(self.entry_output_path, True))

        btn_output_path.pack(side=LEFT, padx=[0, 5])
        self.entry_output_path.pack(side=RIGHT, fill=X, expand=YES)

        row_1.pack(side=TOP, fill=X, expand=YES, padx=5, pady=5)
        row_2.pack(side=TOP, fill=X, expand=YES, padx=5)
        row_3.pack(side=TOP, fill=X, expand=YES, padx=5, pady=5)
        row_4.pack(side=TOP, fill=X, expand=YES, padx=5)
        row_5.pack(side=TOP, fill=X, expand=YES, padx=5, pady=5)

        return frame_container

    def eat_taco(self, parent: TacoShell, child_id):
        self.child_id = child_id
        self.parent = parent
        self.parent.root_window.title("SimitConfigurationComparisonTool")
        self.parent.components['btn_generate_command'] = self.run
        self.progressbar = self.parent.components['bar_progress']

        frame = self.init_frame(self.parent.root_frame)
        kwargs = {'side': TOP, 'fill': X,  'pady': 5}
        self.parent.add_to_packing('CmpTool', frame, kwargs, index=3)


if __name__ == "__main__":
    root = Tk()
    o = SimitConfigurationComparisonTool()
    f = o.init_frame(root)
    f.pack(side=TOP, fill=X, expand=YES, anchor='n')
    root.mainloop()


def make_taco():
    return SimitConfigurationComparisonTool()