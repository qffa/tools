# -*- coding: utf-8 -*-

# generate random string

import random
import string

for i in range(1000):
    s = "".join(random.sample(string.ascii_lowercase, random.randint(4, 12)))
    print(s)
