#!/usr/bin/python3
import sys

for line in sys.stdin:

    line = line.strip()
    words = line.split()
    if len(words) == 2 and words[0] != '#': # discards comments/text and only considers nodes
        print(words[0],words[1], sep = "\t")
