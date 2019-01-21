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
        self.parent.root_window.title("Block Generator")
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

        deviations, _ = self.parent.interpret_file(self.deviations_file, ';', '"', buffermode='list')
        list_tags, count = self.parent.interpret_file(source_file, ';', '"')
        with open('relevant_blocks.txt', 'r') as f:
            relevant_blocks = [line.strip() for line in f]
        with open('relevant_nodes.txt', 'r') as f:
            relevant_nodes = [line.strip() for line in f]

        buffered_code_defs = self.buffer_structures(self.code_path, 'codedef')
        buffered_opc_defs = self.buffer_structures(self.opc_path, 'opcdef')

        buffered_code_outputs = {}
        buffered_opc_output = {'data': {'body': ''}}

        header = next(list_tags)
        idx_of_mkz = header.index('MKZ')
        idx_of_tag = header.index('TAG')
        idx_of_psrv = header.index('PSRV')
        idx_of_block = header.index('BLOCK')

        progress = IntVar()
        self.progressbar.configure(variable=progress, maximum=count)

        for index, data in enumerate(list_tags):
            if self.parent.components['STOP_COMMAND']:
                return
            failed = False
            block = data[idx_of_block].rstrip(' ').upper()
            if block in relevant_blocks:
                busnode, typ, name = data[idx_of_mkz].rstrip(' ').upper().split('_')
                bus, node = busnode.upper().split('X')
                if node in relevant_nodes:
                    asnode = 'AS' + bus
                    tag = data[idx_of_tag].rstrip(' ').upper()
                    mkz = data[idx_of_mkz].rstrip(' ').upper()
                    desc = data[idx_of_psrv].rstrip(' ').upper().replace('Æ', 'AE').replace('Ø', 'OE').replace('Å', 'AA')

                    if 16 < len(desc):  # Ensure max 16 chars
                        desc = desc[:15]

                    buffered_code_outputs.setdefault(asnode, {'body': '', 'tail': ''})
                    if typ in buffered_code_defs.keys():
                        self.write_to_output(buffered_code_defs, buffered_code_outputs,
                                             typ, tag, asnode, name, desc,
                                             post='\n')
                    else:
                        if not self.parent.override:
                            raise Exception('Tag {} is of type {}, but the block definition file was missing'.format(tag, typ))

                    if typ in buffered_opc_defs.keys():
                        self.write_to_output(buffered_opc_defs, buffered_opc_output,
                                             typ, tag, asnode, name, desc,
                                             key='data')
                    else:
                        pass  # allow this case

                    self.parent.write_to_log('tag: {}, \ttype: {}, \tmkz: {}'.format(tag, typ, mkz))
                else:
                    failed = True
                    self.parent.write_to_log('{} is not listed as a relevant node and was ignored'.format(node), 'muted')
            else:
                failed = True
                self.parent.write_to_log('{} is not listed as a relevant block and was ignored'.format(block), 'muted')
            progress.set(index+1)
            self.parent.update_progress(failed=failed)

        self.parent.update_progress(force=True)  # Remainder

        if not os.path.isdir('outputs'):
            os.makedirs('outputs')

        for key, buffer in buffered_code_outputs.items():
            with open('outputs/' + key + '.LSE', 'w+') as f:
                f.write(buffer['body'])
                f.write(buffer['tail'])

        with open('outputs/' + self.opc_file, 'w+') as f:
            f.write(buffered_opc_output['data']['body'])

        self.parent.write_to_log('Wrote results to outputs\\', 'good')

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
                        typ: str, tag: str, node: str, name: str, desc: str,
                        post='', key=None):

        if typ in buffered_defs.keys():
            if desc is None:
                desc = tag

            code = buffered_defs[typ] \
                .rstrip(' ') \
                .replace('{NODE}', node) \
                .replace('{TAG}', tag) \
                .replace('{DESCRIPTION}', desc) \
                .replace('{NAME}', name) \
                + '\n'

            if key is None:
                key = node

            buffered_outputs[key]['body'] += code + post
            if 'tail' in buffered_outputs[key].keys():
                if buffered_outputs[key]['tail'] == '':  # First line of tail
                    sub_head = 'ZYK,3;\n'
                    sub_tail = ',XB,APPL'
                else:
                    sub_head = ''
                    sub_tail = ''
                buffered_outputs[key]['tail'] += '{}A,{},{};\nE{};\n'\
                    .format(sub_head, typ, name, sub_tail)


def make_taco():
    return BlockGenerator()