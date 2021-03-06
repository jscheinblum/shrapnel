# $Header: //prod/main/ap/shrapnel/setup.py#17 $
#!/usr/bin/env python

from distutils.core import setup
from Cython.Distutils import build_ext
from Cython.Distutils.extension import Extension

#from Cython.Distutils import build_ext
#from Cython.Distutils.extension import Extension

import glob
import os

if os.getenv('IPROOT'):
    include_dir = os.path.join( os.getenv('IPROOT'), 'ap', 'aplib')
else:
    include_dir = os.path.join( os.getcwd(), '..', 'aplib')

def newer(x, y):
    x_mtime = os.path.getmtime(x)
    try:
        y_mtime = os.path.getmtime(y)
    except OSError:
        return True
    return x_mtime > y_mtime

def exit_ok(status):
    return os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

def check_lio():
    if os.getenv('BUILDING') is not None:
        # Doing this in a build environment.
        # This is a terrible hack.  However, there is no easy way to add
        # arbitrary options to distutils.
        return True
    if newer('test/build/test_lio.c', 'test/build/test_lio'):
        status = os.system('gcc -o test/build/test_lio test/build/test_lio.c')
        if not exit_ok(status):
            return False
    status = os.system('test/build/test_lio')
    return exit_ok(status)

setup (
    name='coro',
    version='1.0.0-000',
    description='IronPort Coroutine/Threading Library',
    author='Sam Rushing',
    author_email='srushing-coro@ironport.com',
    ext_modules = [
        Extension (
            'coro._coro',
            ['coro/_coro.pyx', 'coro/swap.c', 'coro/event_queue.cc'],
            extra_compile_args = ['-Wno-unused-function'],
            depends=(glob.glob('coro/*.pyx') +
                     glob.glob('coro/*.pxi') +
                     glob.glob('coro/*.pxd') +
                     [os.path.join(include_dir, 'pyrex', 'python.pxi'),
                      os.path.join(include_dir, 'pyrex', 'pyrex_helpers.pyx'),
                      os.path.join(include_dir, 'include', 'pyrex_helpers.h'),
                      os.path.join(include_dir, 'pyrex',
                                   'tsc_time_include.pyx'),
                      os.path.join(include_dir, 'include', 'tsc_time.h'),
                      os.path.join(include_dir, 'pyrex', 'libc.pxd'),
                     ]
                    ),
            pyrex_include_dirs=[os.path.join(include_dir, 'pyrex')],
            #include_dirs=[os.path.join(include_dir, 'pyrex')],
            include_dirs=[os.path.join(include_dir, 'include')],
            #pyrex_compile_time_env={'COMPILE_LIO': check_lio(),
            #                        'CORO_DEBUG': True,
            #                       },
            ),
        ],
    #packages=find_packages(),
    packages=['coro'],
    package_dir = {'': 'coroutine', 'coro': 'coro'},
    py_modules = ['backdoor', 'coro_process', 'coro_unittest'],
    cmdclass={'build_ext': build_ext},
)
