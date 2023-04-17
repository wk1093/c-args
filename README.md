# Carg: C with better arguments

basically C but you can return multiple values from a function, and there is *better* runtime errors.

# Basic Usage
- Run `python src/main.py examples/different/types.carg` to "compile" the .carg to main.exe
- If you run main.exe it should say the following:
```
1 2.000000 Hello World!
examples/different/types.carg: line 5: a is 0
From examples/different/types.carg: line 14: Expanding test
```
because there is an error on line 14, when expanding test, that leads to an error on line 5

TODO:

vscode ext.