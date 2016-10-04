def juju(s):
    print('juju:', s)

def clean(p):
    print('clean:', p)

def bootstrap(p):
    print('bootstrap:', p)

def wait(forever=False):
    if forever:
        print('wait forever')
    else:
        print('wait...')
