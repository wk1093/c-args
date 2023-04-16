from rply import LexerGenerator
import sys
from preproc import preproc
import re
import ccomp
import os
import time

fancy = True
preprocess = False

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

lg.add('OUT', r'out\(.*?\)')
lg.add('FAIL', r'fail\(.*?\)')

lg.add("ID", r"[a-zA-Z_][a-zA-Z0-9_]*")

lg.ignore(r'[\s|\n|\t]+')
lg.ignore(r'//.*')

lexer = lg.build()


def compile(a, b):
    files = [] # additional files that need to be deleted after compilation

    with open(a, "r") as f:
        test = f.read()
    with open("carg.h", "r") as f:
        out = f.read() + "\n"

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
            out += "__c_fail(" + token.value[5:-1] + f", {lineno}, \"{a}\")"
        elif token.name == "RETURN":
            vals = token.value[4:-1].split(",")
            for i, v in enumerate(vals):
                out += f"__c_ret(({v}), {i});"
            out += "return 0;"
        elif token.name == "RETURNN":
            out += "return 0;"
        elif token.name == "EXPAND":
            variables = [a.strip() for a in token.value[7:].split("=")[0].strip().split(",")]
            callnoend = token.value[7:].split("=")[1].strip()[:-2]
            lineno = token.getsourcepos().lineno
            fname = callnoend.split("(")[0].strip()
            out += f"__c_expand(\"{fname}\", {lineno}, \"{a}\", {callnoend},"
            for v in variables:
                name = v.split(" ")[1]
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
            f = compile(fname, fname + ".h")
            files += f
            files += [fname + ".h"]
        else:
            out += token.value + " "
    if preprocess:
        out = preproc(out)

    out = re.sub(r"#line.*\n", "", out)
    out = re.sub(r";;", ";", out)

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

        
        exit(1)
    compiled = []
    dbg = False
    translateOnly = False
    skip = False
    files = []
    for i in range(1, len(sys.argv)):
        if skip:
            skip = False
            continue
        if sys.argv[i] == "-g":
            dbg = True
            continue
        elif sys.argv[i] == "-t":
            translateOnly = True
            continue
        elif sys.argv[i] == "-o":
            skip = True
            if i == len(sys.argv) - 1:
                print("Error: -o requires an argument")
                exit(1)
            if not translateOnly:
                outfile = sys.argv[i+1]
            else:
                print("Warning: -o is ignored when translating only")
            continue
        elif not sys.argv[i].endswith(".carg"):
            print("Warning: file", sys.argv[i], "does not end with .carg, skipping")
            continue
        print("Translating", sys.argv[i])
        f = compile(sys.argv[i], ".".join(sys.argv[i].split(".")[:-1]) + ".c")
        for l in f:
            if l not in files:
                files.append(l)
        compiled.append(".".join(sys.argv[i].split(".")[:-1]) + ".c")
        if fancy:
            ccomp.format(".".join(sys.argv[i].split(".")[:-1]) + ".c")
    
    if not translateOnly:
        for i in compiled:
            print("Compiling", i+"arg")
            ccomp.cmp(i)
            time.sleep(0.1)
    
    if not dbg and not translateOnly:
        for i in compiled:
            os.remove(i)
        for i in files:
            os.remove(i)
    if not translateOnly:
        print("Linking", str([a+'arg' for a in compiled])[1:-1], "to", outfile)
        ccomp.link(compiled, outfile)

