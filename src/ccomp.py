from distutils.ccompiler import new_compiler
from distutils.errors import DistutilsExecError, CompileError
import os

compiler = new_compiler()
print("[INFO] Using compiler", compiler.compiler_type)
if compiler.compiler_type == "msvc":
    print("[WARNING]: MSVC is not recommended, errors may occur, trying to find a better compiler")
   

def cmp(cfile):
    try:
        compiler.compile([cfile])
    except (DistutilsExecError, CompileError) as e:
        print("[ERROR]: compilation failed")
        print(e)
        print("[ERROR]: Failed to compile", cfile)
        exit(1)

def link(cfiles, outfile):
    try:
        compiler.link_executable(compiler.object_filenames(cfiles, strip_dir=0), outfile)
    except (DistutilsExecError, CompileError) as e:
        print("[ERROR]: linking failed")
        print(e)
        print("[ERROR]: Failed to link", str([a[:-2] for a in cfiles])[1:-1], "to", outfile)
        exit(1)

    for f in compiler.object_filenames(cfiles, strip_dir=0):
        os.remove(f)

def format(filename):
    # clang-format
    os.system("clang-format -i " + filename)
    
