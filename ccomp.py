from distutils.ccompiler import new_compiler
import os

compiler = new_compiler()


def cmp(cfile):
    compiler.compile([cfile])

def link(cfiles, outfile):
    compiler.link_executable(compiler.object_filenames(cfiles, strip_dir=0), outfile)
    for f in compiler.object_filenames(cfiles, strip_dir=0):
        os.remove(f)
    
