from rply import LexerGenerator
import sys

lg = LexerGenerator()

lg.add('FUNCTION', r'fun')
lg.add('RETURN', r'ret\s*(.*?);')
lg.add('EXPAND', r'expand\s*(.*?)\s*=\s*(.*?);')
lg.add('OUT', r'out\(.*?\)')
lg.add('FAIL', r'fail\(.*?\)')
lg.add('PREPRO', r'#.*')
lg.add("ID", r"[a-zA-Z_][a-zA-Z0-9_]*")
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

lg.ignore(r'[\s|\n|\t]+')
lg.ignore(r'//.*')

lexer = lg.build()


def compile(a, b):
    with open(a, "r") as f:
        test = f.read()
    with open("carg.h", "r") as f:
        out = f.read() + "\n"

    for token in lexer.lex(test):
        if token.name == "PREPRO":
            out += token.value + "\n"
        elif token.name == "FUNCTION":
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
        
        elif token.name == "SEMICOLON" or token.name == "LBRACE" or token.name == "RBRACE":
            out += token.value + "\n"
        else:
            out += token.value + " "

    with open(b, "w+") as f:
        f.write(out)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <file(s)>")
        print("Example: python main.py test.carg test2.carg -> test.c test2.c")
        exit(1)
    for i in range(1, len(sys.argv)):
        if not sys.argv[i].endswith(".carg"):
            print("Warning: file", sys.argv[i], "does not end with .carg, skipping")
            continue
        print("Compiling", sys.argv[i], "to", ".".join(sys.argv[i].split(".")[:-1]) + ".c")
        compile(sys.argv[i], ".".join(sys.argv[i].split(".")[:-1]) + ".c")

