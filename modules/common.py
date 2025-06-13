import sys

def prompt_choice(prompt, choices):
    while True:
        ans = input(prompt).strip().lower()
        if ans in choices:
            return ans

def rmdup_list(lst):
    seen = set()
    return [x for x in lst if not (x in seen or seen.add(x))]

def init(msg):
    print(msg)
    sys.exit()

