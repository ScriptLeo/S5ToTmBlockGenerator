import os
from main import TacoShell

class BlockGenerator:

    def __init__(self):
        self.source_file = ''
        # TODO divide outputs into separate file sets for each node
        # TODO add xml output
        self.output_code = 'output_code.txt'
        self.output_opc = 'OpcProcessTags.xml'
        self.deviations_file = 'structures/deviations.csv'
        self.parent = None
        self.child_id = None

    def eat_taco(self, parent, child_id):
        self.child_id = child_id
        self.parent: TacoShell = parent
        self.parent.components['btn_generate'].config(
            command=lambda: self.generate_blocks(self.parent.components['entry_path'].get()))
        self.parent.root.title("Block Generator")

    def generate_blocks(self, source_file):
        self.parent.components['lbl_progress'].config(text='Processing')
        self.source_file = source_file

        deviations = self.parent.interpret_file(self.deviations_file, ';', '"')

        list_tags = self.parent.interpret_file(source_file, ';', '"')

        loop_count = 0

        buffered_defs = {}
        code_path = 'structures/code/'
        for file in os.listdir(code_path):
            name, ext = os.path.basename(file).split('.')
            if ext == 'def':
                f = open(code_path + file, 'r')
                buffered_defs[name] = f.read().rstrip('\n')
                f.close()

        buffered_code_output = ''
        buffered_opc_output = None

        header = next(list_tags)
        idx_of_mkz = header.index('Tag')
        idx_of_tag = header.index('From alarmlist')
        for index, data in enumerate(list_tags):
            tag = data[idx_of_tag]
            mkz = data[idx_of_mkz]
            typ = data[idx_of_mkz].split('_')[1]

            if typ in buffered_defs.keys():
                code = buffered_defs[typ].replace('{TAG}', tag).replace('{DESCRIPTION}', tag).replace('{NAME}', 'AUTO_' + str(index))
                buffered_code_output += code + '\n\n'

            else:
                if not self.parent.override:
                    raise Exception('Tag {} is of type {}, but the block definition file was missing'.format(tag, typ))

            self.parent.write_to_log('tag: {}, \ttype: {}, \tmkz: {}'.format(tag, typ, mkz))

            # Temporary limit
            loop_count += 1
            if loop_count == 10:
                break

        raw_output = open(self.output_code, 'w+')
        raw_output.write(buffered_code_output)
        raw_output.close()

        self.parent.components['lbl_progress'].config(text='Completed')


def make_taco():
    return BlockGenerator()