def pretty(t, m):
    m = str(m)
    if t == "+":
        print("\x1b[32;1m[+]\x1b[0m\t" + m),
    elif t == "-":
        print("\x1b[31;1m[-]\x1b[0m\t" + m),
    elif t == "*":
        print("\x1b[34;1m[*]\x1b[0m\t" + m),
    elif t == "!":
        print("\x1b[33;1m[!]\x1b[0m\t" + m)
    elif t == "=":
        print("[" + t + "]" + m)
