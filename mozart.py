import traceback
from functools import wraps
import logging
from importlib import import_module, reload


def cvar(key: str, *args):
    """
    Create variable:
    Creates variable that will be interpreted and potentially initialized by TacoShell,
    and will be forwarded to the function decorated by @taco_wrap().

    :param key: A key that can be referenced and used in the settings: dict.
    :param args: If empty, the parameter intrinsic to TacoShell will be selected and passed to the decorated function.
                If args contains 'typ' and 'val', TacoShell object will create variable with name, type and value and
                pass to the decorated function. The key must not exist in TacoShell.variables, else it will be
                overridden by its intrinsic variable with the same key.
    :return: Variable in expected format for TacoShell. Variables should be passed in as a list of cvars.
    """
    if len(args) == 0:
        return {'key': key}
    elif len(args) == 2:
        return {'key': key, 'type': args[0], 'value': args[1]}


def taco_wrap(variables=None, settings=None):
        """
        Decorator function for 'one-line initialization.

        :param variables: Optional
        :param settings: Optional
        """

        # https://www.saltycrane.com/blog/2010/03/simple-python-decorator-examples/
        def decorator(func):
            @wraps(func)
            def wrapped():
                conductor = Mozart(variables, settings)
                conductor.symphony.components['btn_generate'].configure(state='normal')  # This should be default behavior
                conductor.symphony.components['btn_generate'].configure(state='normal')  # This should be default behavior
                conductor.symphony.components['btn_generate_command'] = lambda: func(**conductor.symphony.variables['user_variables'])
                conductor.start()

            return wrapped

        return decorator


class Mozart:
    symphony = None
    influence = None
    mod = None

    def __init__(self, *args, **kwargs):
        self.symphony = self.influence = self.load(*args, **kwargs)

    def load(self, *args, **kwargs):
        self.mod = import_module('tacoshell')
        symphony = self.mod.TacoShell(*args, **kwargs, conductor=self)
        return symphony

    def start(self):
        self.symphony.start()

    def mreload(self):
        self.mod = reload(self.mod)
        self.influence = self.mod.TacoShell(**{'init': False})
        print('symphony was influenced')


def main():
    try:
        composer = Mozart()
        composer.start()

    except:
        traceback.print_exc()
        logging.basicConfig(filename='log.txt',
                            level=logging.DEBUG,
                            format='%(asctime)s',
                            datefmt='%m-%d %H:%M')
        logging.exception("message")


if __name__ == '__main__':
    main()
