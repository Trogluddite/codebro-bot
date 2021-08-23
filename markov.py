import yaml
import random
from secrets import SystemRandom
from multiprocess import Lock, Manager, Process


# instantiate a Markov object with the source file
class Markov:
    def __init__(self, brain_file: str, ignore_words, skip_mp=False):
        self.brain_file = brain_file
        self.ignore_words = ignore_words
        self.skip_mp = skip_mp
        if not self.skip_mp:
            self.manager = Manager()
            self.words = self.manager.list(self.load_corpus(brain_file))
            self.cache = self.manager.dict(self.database(self.words, {}))
        else:
            self.words = list(self.load_corpus(brain_file))
            self.cache = dict(self.database(self.words, {}))

    @classmethod
    def load_corpus(cls, source_file: str):
        with open(source_file, 'r') as infile:
            return yaml.load(infile.read(), Loader=yaml.Loader)

    @classmethod
    def generate_markov_text(cls, words: list, cache: dict, seed_phrase=None):
        w1, w2 = "<START>", ""
        if seed_phrase:
            w1, w2 = seed_phrase[0], seed_phrase[1]
        else:
            urandom = SystemRandom()
            valid_starts = [(x[0], x[1]) for x in cache.keys() if x[0] == "<START>"]
            w1, w2 = valid_starts[urandom.randint(0, len(valid_starts) - 1)]

        gen_words = []
        while True:
            if w2 == "<STOP>":
                break
            w1, w2 = w2, random.choice(cache[(w1, w2)])
            gen_words.append(w1)

        message = ' '.join(gen_words)
        return message

    @classmethod
    def triples(cls, words):
        if len(words) < 3:
            return
        for i in range(len(words) - 2):
            yield (words[i], words[i+1], words[i+2])

    def database(self, words: list, cache: dict):
        for w1, w2, w3 in self.triples(words):
            key = (w1, w2)
            if key in cache:
                if not (w3 in cache[key]):
                    cache[key].append(w3)
            else:
                cache[key] = [w3]
        return cache

    def learn(self, sentence: str):
        tokens = sentence.split()

        # strip, uppercase, and check for inclusion in IGNORE_WORDS list
        is_ignored = lambda x: x.strip("\'\"!@#$%^&*().,/\\+=<>?:;").upper() in self.ignore_words
        tokens = [x for x in tokens if not is_ignored(x)]
        if len(tokens) == 0:
            return  # nothing to learn here!

        tokens[len(tokens) - 1] = tokens[len(tokens) - 1].strip(".?!")
        tokens = [u"<START>"] + tokens + [u"<STOP>"]
        indexes_with_stops = [tokens.index(x) for x in tokens if x.strip(".?!") != x]
        for i in indexes_with_stops[::-1]:
            tokens[i] = tokens[i].strip(".?!")
            tokens.insert(i + 1, u"<STOP>")
            tokens.insert(i + 2, u"<START>")

        self.words += tokens
        self.cache = self.database(self.words, {})
        lk = None
        if not self.skip_mp:
            lk = Lock()
        # there must be a better way to serialize from the proxy ..
        local_words = [word for word in self.words]
        with open(self.brain_file, 'w') as outfile:
            if not self.skip_mp:
                lk.acquire()
            outfile.write(yaml.dump(local_words, default_flow_style=True))
            if not self.skip_mp:
                lk.release()

    def create_response(self, prompt="", learn=False):
        prompt_tokens = prompt.split()

        # set seedword from somewhere in words if there's no prompt
        if len(prompt_tokens) < 1:
            seed = random.randint(0, len(self.words)-1)
            prompt_tokens.append(self.words[seed])

        # create a set of lookups for phrases that start with words
        # contained in prompt phrase
        seed_tuples = []
        for i in range(0, len(prompt_tokens)-2):
            seed_phrase = ("<START>", prompt_tokens[i])
            seed_tuples.append(seed_phrase)

        # lookup seeds in cache; compile a list of 'hits'
        seed_phrase = None
        valid_seeds = []
        for seed in seed_tuples:
            if seed in self.cache:
                valid_seeds.append(seed)

        # either seed the lookup with a randomly selected valid seed,
        # or if there were no 'hits' generate with no seedphrase
        if len(valid_seeds) > 0:
            seed_phrase = valid_seeds[random.randrange(0, len(valid_seeds), 1)]
            response = self.generate_markov_text(self.words, self.cache, seed_phrase)
        else:
            response = self.generate_markov_text(self.words, self.cache)

        if learn:
            if not self.skip_mp:
                p = Process(target=self.learn, args=(prompt,))
                p.start()
            else:
                self.learn(prompt)
        return response
