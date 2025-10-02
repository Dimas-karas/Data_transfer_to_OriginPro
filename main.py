import originpro as op
from tkinter import filedialog
from time import time
from parsers import CorrtestData


def interact_with_origin(func):
    """Decorator for correct work with originpro lib"""

    def wrapper(*args, **kwargs):
        # Ensures that the Origin instance gets shut down properly.
        import sys

        print('Connecting to Origin, please wait')

        def origin_shutdown_exception_hook(exctype, value, traceback):
            op.exit()
            sys.__excepthook__(exctype, value, traceback)

        if op and op.oext:
            sys.excepthook = origin_shutdown_exception_hook

        # Set Origin instance visibility.
        if op.oext:
            op.set_show(True)

        func(*args, **kwargs)

        # Exit running instance of Origin.
        if op.oext:
            op.exit()

    return wrapper


@interact_with_origin
def move_data_to_origin(path_to_files):

    print("Creating a Origin project")
    op.new()
    book = op.find_book(name='Book1')
    book.name = 'Data'

    for path_to_file in path_to_files:
        filename = path_to_file.split('/')[-1]
        print(f"Processing {filename}", end=', ')
        start_time = time()
        wks = book.add_sheet(name=filename.rsplit('.', maxsplit=1)[0])
        data = CorrtestData(path_to_file)
        wks.cols = len(data.cols)
        for idx, col in enumerate(data.cols):
            wks.from_list(col=idx,
                          data=col['values'],
                          lname=col['name'],
                          axis=col.get('type', 'Y'),
                          comments=col.get('comment', ''))
        print(f'total time = {time() - start_time:.2} s')

    path_to_save = filedialog.asksaveasfilename(filetypes=[('Project format (*.opju)', '.opju'),
                                                           ('Project (*.opju)', '.opju')],
                                                initialfile='Data.opju',
                                                title='Choose a save name',
                                                defaultextension='.opju')

    print(f"Project saved to {path_to_save}")
    op.save(path_to_save.replace('/', '\\'))


files_to_process = filedialog.askopenfilenames(filetypes=[('Corrtest files (*.cor)', '*.cor'),
                                                          ('All files', '*.*')],
                                               title='Choose files to process')

assert len(files_to_process) > 0, "There are no selected files to process"

move_data_to_origin(files_to_process)
