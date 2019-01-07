import os
from tacoshell import TacoShell
from tkinter import filedialog, IntVar


class BlockGenerator:

    def __init__(self):
        self.source_file = None
        self.parent = None
        self.child_id = None
        self.progressbar = None

        self.code_path = 'structures/code/'
        self.opc_path = 'structures/opc/'
        self.opc_file = 'OpcProcessTags.XML'
        self.deviations_file = 'structures/deviations.csv'

    def eat_taco(self, parent, child_id):
        self.child_id = child_id
        self.parent: TacoShell = parent
        self.parent.components['btn_generate_command'] = self.generate
        self.parent.components['btn_open_definition_command'] = self.open_definitions
        self.parent.root.title("Block Generator")
        self.progressbar = self.parent.components['bar_progress']

    def generate(self):
        self.generate_blocks(self.parent.components['entry_path'].get())

    @staticmethod
    def open_definitions():
        response = filedialog.askopenfilenames(title="Select file",
                                               filetypes=([("Definition file", "*.codedef *.opcdef")]))
        return response

    def generate_blocks(self, source_file):
        self.source_file = source_file

        deviations, _ = self.parent.interpret_file(self.deviations_file, ';', '"')
        list_tags, count = self.parent.interpret_file(source_file, ';', '"')

        buffered_code_defs = self.buffer_structures(self.code_path, 'codedef')
        buffered_opc_defs = self.buffer_structures(self.opc_path, 'opcdef')

        buffered_code_outputs = {}
        buffered_opc_output = {'data': {'body': ''}}

        header = next(list_tags)
        idx_of_mkz = header.index('MKZ')
        idx_of_tag = header.index('TAG')
        idx_of_description = header.index('PSRV')

        progress = IntVar()
        self.progressbar.configure(variable=progress, maximum=count)

        for index, data in enumerate(list_tags):
            if self.parent.components['STOP_COMMAND']:
                return
            tag = data[idx_of_tag].rstrip(' ')
            mkz = data[idx_of_mkz].rstrip(' ')
            description = data[idx_of_description].rstrip(' ')
            busnode, typ, name = data[idx_of_mkz].rstrip(' ').split('_')
            bus, node = busnode.split('X')

            buffered_code_outputs.setdefault(node, {'body': '', 'tail': ''})
            if typ in buffered_code_defs.keys():
                self.write_to_output(buffered_code_defs, buffered_code_outputs,
                                     typ, tag, node, name, description,
                                     post='\n\n')
            else:
                if not self.parent.override:
                    raise Exception('Tag {} is of type {}, but the block definition file was missing'.format(tag, typ))

            if typ in buffered_opc_defs.keys():
                self.write_to_output(buffered_opc_defs, buffered_opc_output,
                                     typ, tag, node, name, description,
                                     key='data')
            else:
                pass  # allow this case

            self.parent.write_to_log('tag: {}, \ttype: {}, \tmkz: {}'.format(tag, typ, mkz))
            progress.set(index+1)
            self.parent.update_progress()

            # if index == 9:  # Temporary limit
            #     break

        self.parent.update_progress(force=True)

        if not os.path.isdir('outputs'):
            os.makedirs('outputs')

        for key, buffer in buffered_code_outputs.items():
            with open('outputs/' + key + '.LSE', 'w+') as f:
                f.write(buffer['body'])
                f.write(buffer['tail'])

        with open('outputs/' + self.opc_file, 'w+') as f:
            f.write(buffered_opc_output['data']['body'])

    @staticmethod
    def buffer_structures(path, filt):
        buffer = {}
        for file in os.listdir(path):
            name, ext = os.path.basename(file).split('.')
            if ext == filt:
                with open(path + file, 'r') as f:
                    buffer[name] = f.read().rstrip('\n')
        return buffer

    @staticmethod
    def write_to_output(buffered_defs, buffered_outputs,
                        typ, tag, node, name, description,
                        post='', key=None):
        if typ in buffered_defs.keys():
            if description is None:
                description = tag

            code = buffered_defs[typ] \
                .replace('{NODE}', node) \
                .replace('{TAG}', tag) \
                .replace('{DESCRIPTION}', description) \
                .replace('{NAME}', name)

            if key is None:
                key = node

            buffered_outputs[key]['body'] += code + post
            if 'tail' in buffered_outputs[key].keys():
                hook_txt = ',XB,APPL' if buffered_outputs[key]['tail'] == '' else ''
                buffered_outputs[key]['tail'] += 'A,{},{};\nE{};\n'.format(typ, name, hook_txt)


def make_taco():
    return BlockGenerator()