class BlockGenerator:
    """

    """

    def __init__(self):
        self.source_file: str = ''
        self.output_file: str = 'output.txt'
        self.deviations_file: str = 'blockdefs/@deviations.csv'
        self.parent = None
        self.child_id = None

    def eat_taco(self, parent, child_id):
        self.child_id = child_id
        self.parent = parent
        self.parent.components['btn_generate'].config(
            command=lambda: self.generate_blocks(self.parent.components['entry_path'].get()))
        self.parent.root.title("Block Generator")

    def generate_blocks(self, source_file):
        """

        :param source_file:
        :return:
        """
        self.parent.components['lbl_progress'].config(text='Processing')
        self.source_file = source_file

        raw_output = open(self.output_file, 'w+')
        deviations = self.parent.interpret_file(self.deviations_file, ';', '"')
        list_tags = [] if self.parent.DEBUG_MODE else self.parent.interpret_file(source_file, ';', '"')

        for line in deviations:
            self.parent.components['txt_log'].config(state='normal')
            self.parent.components['txt_log'].insert('end', ''.join(line) + '\n')
            # self.gui_handle.txt_log.tag_add('red', )  # TODO add colored text support
            self.parent.components['txt_log'].config(state='disabled')

        # idx_of_MKZ = list_tags[0].index('Type')
        # for line_data in list_tags[1:]:
        #     pass

        self.parent.components['lbl_progress'].config(text='Idle')


def make_taco():
    return BlockGenerator()