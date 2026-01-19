import random
import yaml
from itertools import chain, groupby

START_TOK = "<START>"
STOP_TOK = "<STOP>"

STOP = object()
START = object()


# instantiate a Markov object with the source file
class Markov:
    def __init__(self, input_file: str, output_file: str, user_map, ignore_words):
        if input_file == output_file:
            raise ValueError("input and output files must be different")
        self.user_map = self._init_user_map(user_map)
        self.ignore_words = set(w.upper() for w in ignore_words)
        self.output_file = output_file
        self.update_graph_and_corpus(self.corpus_iter(input_file), init=True)

    def corpus_iter(self, source_file: str):
        """
        Emit the contents of the source_file as an iterable of token sequences
        """
        with open(source_file, 'r', encoding='utf8') as infile:
            # this is dumb
            if source_file.endswith(".yml") or source_file.endswith(".yaml"):
                words = yaml.load(infile.read(), Loader=yaml.Loader)
                for is_delim, phrase in groupby(words, lambda w: w in (START_TOK, STOP_TOK)):
                    if not is_delim:
                        yield list(phrase)
            else:
                for line in infile:
                    yield from self.tokenize(line)

    @classmethod
    def triples_and_stop(cls, words):
        """
        Emit 3-grams from the sequence of words, the last one ending with the
        special STOP token
        """
        words = chain(words, [STOP])
        try:
            w1 = next(words)
            w2 = next(words)
            w3 = next(words)
            while True:
                yield (w1, w2, w3)
                w1, w2, w3 = w2, w3, next(words)
        except StopIteration:
            return

    def _ignore(self, word: str):
        return word.strip("\'\"!@#$%^&*().,/\\+=<>?:;").upper() in self.ignore_words

    def tokenize(self, sentence: str):
        """
        Emit a sequence of token lists from the string, ignoring ignore_words.
        A word ending in certain puntuation ends a given token sequence.
        """
        cur = []
        for w in sentence.split():
            if self._ignore(w):
                pass

            elif any(w.endswith(c) for c in ('.', '?', '!')):
                w = w.strip(".?!")
                if w:
                    cur.append(w)
                yield(cur)
                cur = []
            else:
                cur.append(w)
        if cur:
            yield cur

    def _update_graph_and_emit_changes(self, token_seqs, init=False):
        """
        self.graph stores the graph of n-gram trasitions.
        The keys are single tokens or pairs and the values possible next words in the n-gram.
        Initial tokens are also specially added to the list at the key START.

        _update_graph_and_emit_changes returns a generator that when run will
        update the graph with the ngrams taken from each element of token_seqs.

        Yields the token sequence that result in updates so they can be further
        acted on.

        if init is True reinitialize from an empty graph
        """
        if init:
            self.graph = {START: []}

        for seq in token_seqs:
            first = True
            learned = False
            for w1, w2, w3 in self.triples_and_stop(seq):
                if first:
                    if w1 not in self.graph[START]:
                        self.graph[START].append(w1)
                        learned = True
                    next_words = self.graph.setdefault(w1, [])
                    if w2 not in next_words:
                        next_words.append(w2)
                        learned = True
                    first = False
                next_words = self.graph.setdefault((w1, w2), [])
                if w3 not in next_words:
                    next_words.append(w3)
                    learned = True
            if learned:
                yield seq

    def _init_user_map(self, mapfile):
        if mapfile:
            with open(mapfile, 'r', encoding='utf8') as infile:
                mapfile = yaml.load(infile.read(), Loader=yaml.Loader)
        return mapfile

    def update_graph_and_corpus(self, token_seqs, init=False):
        changes = self._update_graph_and_emit_changes(token_seqs, init=init)
        self.update_corpus(changes, init=init)

    def update_corpus(self, token_seqs, init=False):
        mode = 'w' if init else 'a'
        with open(self.output_file, mode, encoding='utf8') as f:
            for seq in token_seqs:
                f.write(" ".join(seq))
                f.write("\n")

    def generate_markov_text(self, seed=None):
        if seed and seed in self.graph:
            w1 = seed
        else:
            w1 = random.choice(self.graph[START])
        w2 = random.choice(self.graph[w1])

        gen_words = [w1]
        while True:
            if w2 == STOP:
                break
            w1, w2 = w2, random.choice(self.graph[(w1, w2)])
            gen_words.append(w1)

        message = ' '.join(gen_words)
        return message

    def _map_users(self, response, slack):
        if self.user_map is None:
            return response
        elif slack:
            for k, v in self.user_map.items():
                response.replace('@!', '@')  # discord allows exclamation points after the @ in their user ids??
                response = response.replace(v, k)
        else:
            for k, v in self.user_map.items():
                response = response.replace(k, v)
        return response

    def create_response(self, prompt="", learn=False, slack=False):
        # set seedword from somewhere in words if there's no prompt
        prompt_tokens = prompt.split()
        valid_seeds = [tok for tok in prompt_tokens[:-2] if tok in self.graph]
        seed_word = random.choice(valid_seeds) if valid_seeds else None
        response = self.generate_markov_text(seed_word)
        if learn:
            self.update_graph_and_corpus(self.tokenize(prompt))
        return self._map_users(response, slack)
