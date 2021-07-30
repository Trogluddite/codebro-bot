#!/usr/bin/python 

#Pre-process some input text into a YAML list of unicode strings 
import yaml 

def file_to_words(): 
    fh = open("./codebro.txt", "r")
    fh.seek(0)
    lines = list(fh)

    #each line has an implicit <START>, <STOP>.  Scan tokens, 
    #work in reverse to add <START>, <STOP> to replace punctuation
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
    return words


words = file_to_words()

with open('codebro.yaml', 'w') as outfile: 
    outfile.write(yaml.dump(words, default_flow_style=True))






