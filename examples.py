from benchmark import Suite

def foo():
    x = 0
    for _ in range(10000):
        x+=1

def bar():
    x = 0
    for _ in range(1000):
        x+=2
        x-=1

def quux():
    x = ''
    for i in range(10000):
        x += chr(i%256)

def quuz():
    x = []
    for i in range(10000):
        x.append(i)

def argskwargs(*args, **kwargs):
    total = sum(args)
    for key, value in kwargs.items():
        total += value
    return total

from random import random
from time import sleep
def random_sleep():
    sleep(random()/1000)


suite = Suite()
suite.add(foo)
suite.add(bar)
suite.add(quux)
suite.add(quuz)
suite.add(argskwargs, 1, 2, 3, a=4, b=5, c=6)
suite.add(argskwargs, 1, 2, 3)
suite.add(argskwargs, a=4, b=5, c=6)
suite.add(argskwargs)
suite.add(random_sleep)

print(suite.get_suite())
suite.run(verbose=True)