#undef __c_fail_msg
#undef __c_fail_exp
#undef __c_fun
#undef __c_out
#undef __c_ret
#undef __c_expand
#undef __c_fail

#define __c_fail_msg(file, lineno, msg) "%s: line %d: %s\n", file, lineno, msg
#define __c_fail_exp(file, lineno, fname) "From %s: line %d: Expanding %s", file, lineno, fname

#define __c_fun int
#define __c_out(t, n) t* __ret_##n
#define __c_ret(v, n) *__ret_##n = v;
#define __c_expand(fname, lineno, file, call, ...) __VA_ARGS__; if (call) { printf(__c_fail_exp(file, lineno, fname)); return 1;};
#define __c_fail(msg, lineno, file) printf(__c_fail_msg(file, lineno, msg)); return 1;