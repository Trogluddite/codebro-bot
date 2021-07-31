#!/usr/bin/env python

import yaml
from argparse import ArgumentParser


def file_to_words(garbage_in: str, garbage_out: str):
    fh = open(garbage_in, "r")
    fh.seek(0)
    lines = list(fh)

    # each line has an implicit <START>, <STOP>.  Scan tokens,
    # work in reverse to add <START>, <STOP> to replace punctuation
    words = []
    for line in lines:
        tokens = line.split()
        tokens[len(tokens) - 1] = tokens[len(tokens) - 1].strip(".?!")
        tokens = ["<START>"] + tokens + ["<STOP>"]
        indexes_with_stops = [tokens.index(x) for x in tokens if x.strip(".?!") != x]
        for i in indexes_with_stops[::-1]:
            tokens[i] = tokens[i].strip(".?!")
            tokens.insert(i + 1, "<STOP>")
            tokens.insert(i + 2, "<START>")
        words += tokens

    with open(garbage_out, 'w') as outfile:
        outfile.write(yaml.dump(words, default_flow_style=True))


if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument('--garbage-in', '-i', type=str, default='codebro.txt', help="""Text file to build yaml from""")
    argparser.add_argument('--garbage-out', '-o', type=str, default='codebro.yaml', help="""Yaml file to write to""")
    args = argparser.parse_args()

    file_to_words(args.garbage_in, args.garbage_out)
