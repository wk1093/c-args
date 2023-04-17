from rply import LexerGenerator
import sys
from preproc import preproc
import re
import ccomp
import os
import time
import ply


ply.lex
fancy = True
preprocess = True

cargh = """
#undef __c_fail_msg
#undef __c_fail_exp
#undef __c_fun
#undef __c_out
#undef __c_ret
#undef __c_expand
#undef __c_fail

#define __c_fail_msg(file, lineno, msg) "%s: line %d: %s\\n", file, lineno, msg
#define __c_fail_exp(file, lineno, fname) "From %s: line %d: Expanding %s", file, lineno, fname

#define __c_fun int
#define __c_out(t, n) t* __ret_##n
#define __c_ret(v, n) *__ret_##n = v;
#define __c_expand(fname, lineno, file, call, ...) __VA_ARGS__; if (call) { printf(__c_fail_exp(file, lineno, fname)); return 1;};
#define __c_fail(msg, lineno, file) printf(__c_fail_msg(file, lineno, msg)); return 1;
"""

lg = LexerGenerator()

lg.add('PREPRO', r'#.*')
lg.add("NUMBER", r"\d+")
lg.add("DOUBLE", r"\d+\.\d+")
lg.add("FLOAT", r"\d+\.\d+f")
lg.add("STRING", r"\".*?\"")
lg.add("CHAR", r"\'(\\.|[^\\'])\'")

lg.add("EQUALS", r"==")
lg.add("NOTEQUALS", r"!=")
lg.add("GREATER", r">")
lg.add("LESS", r"<")
lg.add("GREATEREQUAL", r">=")
lg.add("LESSEQUAL", r"<=")
lg.add("AND", r"&&")
lg.add("OR", r"\|\|")
lg.add("NOT", r"!")
lg.add("BITWISEAND", r"&")
lg.add("BITWISEOR", r"\|")
lg.add("BITWISEXOR", r"\^")
lg.add("BITWISENOT", r"~")
lg.add("BITWISELEFT", r"<<")
lg.add("BITWISERIGHT", r">>")
lg.add("INCREMENT", r"\+\+")
lg.add("DECREMENT", r"--")
lg.add("PLUSASSIGN", r"\+=")
lg.add("MINUSASSIGN", r"-=")
lg.add("TIMESASSIGN", r"\*=")
lg.add("DIVIDEASSIGN", r"/=")
lg.add("MODULOASSIGN", r"%=")
lg.add("BITWISEANDASSIGN", r"&=")
lg.add("BITWISEORASSIGN", r"\|=")
lg.add("BITWISEXORASSIGN", r"\^=")
lg.add("BITWISELEFTASSIGN", r"<<=")
lg.add("BITWISERIGHTASSIGN", r">>=")
lg.add("QUESTION", r"\?")
lg.add("ARROW", r"->")
lg.add("ELLIPSIS", r"\.\.\.")
lg.add("LPAREN", r"\(")
lg.add("RPAREN", r"\)")
lg.add("LBRACE", r"\{")
lg.add("RBRACE", r"\}")
lg.add("LBRACKET", r"\[")
lg.add("RBRACKET", r"\]")
lg.add("COMMA", r",")
lg.add("SEMICOLON", r";")
lg.add("COLON", r":")
lg.add("DOT", r"\.")
lg.add("PLUS", r"\+")
lg.add("MINUS", r"-")
lg.add("TIMES", r"\*")
lg.add("DIVIDE", r"/")
lg.add("MODULO", r"%")
lg.add("ASSIGN", r"=")


# 'import "test.harg";'
lg.add('IMPORT', r'import\s*".*?";')
lg.add('FUNCTION', r'safe')
lg.add('RETURNN', r'ret\s*;')
lg.add('RETURN', r'ret(\s)+(.*?);')
# EXPAND: expand int a, int b = integertuple(5, 2);
lg.add('EXPAND', r'expand\s*(.*?)\s*=\s*(.*?);')

# EXPANDT: expand call(2); // call is a function that returns nothing
lg.add('EXPANDT', r'expand\s*(.*?);')

lg.add('OUT', r'out\(.*?\)')
lg.add('FAIL', r'fail\(.*?\)')

lg.add("ID", r"[a-zA-Z_][a-zA-Z0-9_]*")

lg.ignore(r'[\s|\n|\t]+')
lg.ignore(r'//.*')

lexer = lg.build()

def find(filen, fromf):
    # example find("test.harg", "src/test.carg") # test.harg could be in src/ or current directory

    # find in same directory
    if os.path.exists(os.path.join(os.path.dirname(fromf), filen)):
        return os.path.join(os.path.dirname(fromf), filen)
    
    # find in current directory
    if os.path.exists(filen):
        return filen
    
    print(f"[ERROR]: Could not find {filen} from {fromf}")
    exit(1)
    


def compile(a, b):
    files = [] # additional files that need to be deleted after compilation

    with open(a, "r") as f:
        test = f.read()

    out = cargh + "\n"

    for token in lexer.lex(test):
        if token.name == "FUNCTION":
            out += "__c_fun "
        elif token.name == "OUT":
            types = [a.strip() for a in token.value[4:-1].split(",")]
            for i, t in enumerate(types):
                out += f"__c_out({t}, {i}) "
                if i != len(types) - 1:
                    out += ", "
        elif token.name == "FAIL":
            lineno = token.getsourcepos().lineno
            f = a.replace('\\','/')
            out += "__c_fail(" + token.value[5:-1] + f", {lineno}, \"{f}\")"
        elif token.name == "RETURN":
            vals = token.value[4:-1].split(",")
            for i, v in enumerate(vals):
                out += f"__c_ret(({v}), {i});"
            out += "return 0;"
        elif token.name == "RETURNN":
            out += "return 0;"
        elif token.name == "EXPAND":
            variables = [a.strip() for a in token.value[7:].split("=")[0].strip().split(",")]
            for v in variables:
                if v == "" or v == " ":
                    variables.remove(v)
            callnoend = token.value[7:].split("=")[1].strip()[:-2]
            lineno = token.getsourcepos().lineno
            fname = callnoend.split("(")[0].strip()
            f = a.replace('\\','/')
            out += f"__c_expand(\"{fname}\", {lineno}, \"{f}\", {callnoend},"
            for v in variables:
                name = v.split(" ")[-1]
                out += f" &{name},"
            out = out[:-1] + "),"
            for v in variables:
                out += v + ";"
            out += ");"
        elif token.name == "PREPRO":
            out += token.value + "\n"
        elif token.name == "IMPORT":
            start = token.value.find('"')
            end = token.value.find('"', start + 1)
            fname = token.value[start + 1:end]
            out += f"#include \"{fname}.h\"\n"
            fname = find(fname, a)
            print(f"[INFO]: Found header '{fname}' for '{a}'")
            f = compile(fname, fname + ".h")
            files += f
            files += [fname + ".h"]
        elif token.name == "EXPANDT":
            callnoend = token.value[7:-1]
            lineno = token.getsourcepos().lineno
            fname = callnoend.split("(")[0].strip()
            f = a.replace('\\','/')
            out += f"__c_expand(\"{fname}\", {lineno}, \"{f}\", {callnoend}, );"
        else:
            out += token.value + " "
    if preprocess:
        out = preproc(out)

    out = re.sub(r"#line.*\n", "", out)
    out = re.sub(r";(\s|\n|\r)*;", ";", out)

    with open(b, "w+") as f:
        f.write(out)
    return files

if __name__ == "__main__":
    outfile = "main"
    if len(sys.argv) < 2:
        print(f"Usage: { sys.argv[0] } <file(s)> [-g] [-t] [-o <output>]")
        print(f"Example: { sys.argv[0] } test.carg test2.carg -o main.exe")
        print("Options: -g: debug mode (doesnt delete temporary files")
        print("         -t: translate only (creates .c file with same name as .carg file)")
        print("         -o: output file (default: main)")
        print("         -I: include directory (not supported yet)")

        
        exit(1)
    compiled = []
    dbg = False
    translateOnly = False
    skip = False
    files = []
    for i in range(1, len(sys.argv)):
        time.sleep(0.1)
        if skip:
            skip = False
            continue
        if sys.argv[i] == "-g":
            dbg = True
            continue
        elif sys.argv[i] == "-I":
            print("[ERROR]: Include directory is not supported yet")
            exit(1) # TODO
        elif sys.argv[i] == "-t":
            translateOnly = True
            continue
        elif sys.argv[i] == "-o":
            skip = True
            if i == len(sys.argv) - 1:
                print("[ERROR]: -o requires an argument")
                exit(1)
            if not translateOnly:
                outfile = sys.argv[i+1]
            else:
                print("[WARNING]: -o is ignored when translating only")
            continue
        elif not sys.argv[i].endswith(".carg"):
            print("[WARNING]: file", sys.argv[i], "does not end with .carg, skipping")
            continue
        print("[INFO]: Translating", sys.argv[i])
        f = compile(sys.argv[i], sys.argv[i] + ".c")
        for l in f:
            if l not in files:
                files.append(l)
        compiled.append(sys.argv[i] + ".c")
        if fancy:
            ccomp.format(sys.argv[i] + ".c")
    
    if not translateOnly:
        for i in compiled:
            time.sleep(0.1)
            print("[INFO]: Compiling", i[:-2])
            ccomp.cmp(i)
    
    if not dbg and not translateOnly:
        for i in compiled:
            os.remove(i)
        for i in files:
            os.remove(i)
    if not translateOnly:
        print("[INFO]: Linking", str([a[:-2] for a in compiled])[1:-1], "to", outfile)
        ccomp.link(compiled, outfile)

