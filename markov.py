import random
import struct
from typing import List, Dict, Tuple, Optional
import array
import yaml
from itertools import chain, groupby


START_TOKEN = "<START>"
STOP_TOKEN = "<STOP>"

START_INDEX = -1
STOP_INDEX = -2


# instantiate a Markov object with the source file
class Markov:

    # Signed short
    COMPRESSED_NUMBER_FORMAT: str = 'i'
    # Two little-endian signed shorts
    COMPRESSED_COMBO_NUMBER_FORMAT: str = f'>{COMPRESSED_NUMBER_FORMAT}{COMPRESSED_NUMBER_FORMAT}'
    SIGNED_INT_MAX_VALUE: int = 2147483648

    def __init__(self, input_file: str, output_file: str, user_map, ignore_words):
        if input_file == output_file:
            raise ValueError("input and output files must be different")
        self.user_map = self._init_user_map(user_map)
        self.ignore_words = set(w.upper() for w in ignore_words)
        self.output_file = output_file

        # Map of n-gram transitions
        self.graph: Dict[bytes, array.array] = dict()

        # Word -> Word Index map
        self.word_index_map: Dict[str, bytes] = dict()

        # List of all unique words. word_index_map maps to indices in this list
        self.words: List[str] = list()

        self.update_graph_and_corpus(self.corpus_iter(input_file), init=True)
        print(f'Found {len(self.words)} unique words')

    def to_graph_key(self, word_index: int | Tuple[int, int]) -> bytes:
        """Convert 1 or 2 integers into a primitive bytes key, compressed to 4 bytes.
        If a single int is passed, it will be in the 0 spot
        If a tuple is passed, it will fill both spots"""
        if isinstance(word_index, int):
            return struct.pack(Markov.COMPRESSED_COMBO_NUMBER_FORMAT, word_index, -1)
        elif isinstance(word_index, tuple):
            return struct.pack(Markov.COMPRESSED_COMBO_NUMBER_FORMAT, word_index[0], word_index[1])
        else:
            raise Exception(f'word index must be int or tuple but was \"{word_index}\"')

    def unpack_graph_key(self, key: bytes) -> Tuple[int, int]:
        """Convert a key bytes object back into a tuple of two ints. If the original key had one int value, it will be
        at index 0"""
        return struct.unpack(Markov.COMPRESSED_COMBO_NUMBER_FORMAT, key)

    def get_word_index(self, word: str) -> int:
        """Get the index for the provided word. If we don't know it, it's a new word and it'll be inserted"""
        if word in self.word_index_map:
            word_index, _ = self.unpack_graph_key(self.word_index_map[word])
            return word_index

        if word == START_TOKEN:
            return START_INDEX

        if word == STOP_TOKEN:
            return STOP_INDEX

        self.words.append(word)
        index = len(self.words) - 1
        self.word_index_map[word] = self.to_graph_key(index)
        return index

    def get_candidate_indices_for_graph_key(self, graph_key: int | Tuple[int, int]) -> array.array:
        """Get the indices for the next transition at the given word_index"""
        array_at_index:array.array = self.graph[self.to_graph_key(graph_key)]
        return array_at_index

    def try_append_at_graph_key(self, graph_key: int | Tuple[int, int], value_to_append: int) -> Tuple[bool, array.array]:
        """Try to insert the given integer value to the array at graph_key in the graph. If it's already there, no-op.

        Returns true if the array was modified, false otherwise"""
        key = self.to_graph_key(graph_key)
        array_at_word_index = self.graph.setdefault(key, array.array(Markov.COMPRESSED_NUMBER_FORMAT))
        if value_to_append not in array_at_word_index:
            array_at_word_index.extend((value_to_append,))
            return True, array_at_word_index
        return False, array_at_word_index

    def corpus_iter(self, source_file: str):
        """
        Emit the contents of the source_file as an iterable of token sequences
        """
        with open(source_file, 'r', encoding='utf8') as infile:
            # this is dumb
            if source_file.endswith(".yml") or source_file.endswith(".yaml"):
                words = yaml.load(infile.read(), Loader=yaml.Loader)
                for is_delim, phrase in groupby(words, lambda w: w in (START_TOKEN, STOP_TOKEN)):
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
        words = chain(words, [STOP_TOKEN])
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

    def _update_graph_and_emit_changes(self, token_seqs:List[List[str]], init=False):
        """
        self.graph stores the graph of n-gram transitions.
        The keys are single tokens or pairs and the values possible next words in the n-gram.
        Initial tokens are also specially added to the list at the key START.

        _update_graph_and_emit_changes returns a generator that when run will
        update the graph with the ngrams taken from each element of token_seqs.

        Yields the token sequence that result in updates so they can be further
        acted on.

        if init is True reinitialize from an empty graph
        """
        if init:
            self.graph.clear()
            self.graph[self.to_graph_key(START_INDEX)] = array.array('h')

        for seq in token_seqs:
            first = True
            learned = False
            for w1, w2, w3 in self.triples_and_stop(seq):

                w1_index = self.get_word_index(w1)
                w2_index = self.get_word_index(w2)
                w3_index = self.get_word_index(w3)

                if first:
                    added_to_start, new_start = self.try_append_at_graph_key(START_INDEX, w1_index)
                    learned |= added_to_start

                    added_to_w1, new_w1 = self.try_append_at_graph_key(w1_index, w2_index)
                    learned |= added_to_w1
                    first = False

                combined_key = (w1_index, w2_index)
                added_to_combined, new_combined = self.try_append_at_graph_key(combined_key, w3_index)
                learned |= added_to_combined
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

    def generate_markov_text(self, seed: Optional[str]=None):

        w1_index = None
        if seed is not None:
            seed_index = self.get_word_index(seed)
            if seed_index in self.graph:
                w1_index = seed_index

        if w1_index is None:
            choices = self.get_candidate_indices_for_graph_key(START_INDEX)
            w1_index = random.choice(choices)

        choices = self.get_candidate_indices_for_graph_key(w1_index)
        w2_index = random.choice(choices)

        generated_index_list = [w1_index]
        while True:
            if w2_index == STOP_INDEX:
                break
            next_key = (w1_index, w2_index)
            choices = self.get_candidate_indices_for_graph_key(next_key)
            w1_index, w2_index = w2_index, random.choice(choices)
            generated_index_list.append(w1_index)

        message = ' '.join(map(lambda idx: self.words[idx], generated_index_list))
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
        prompt_indices = list(map(lambda t: self.get_word_index(t), prompt_tokens))
        valid_seed_indices = [tok for tok in prompt_indices[:-2] if tok in self.graph]
        seed_word_index = random.choice(valid_seed_indices) if valid_seed_indices else None
        seed_word = self.words[seed_word_index] if seed_word_index is not None else None
        response = self.generate_markov_text(seed_word)
        if learn:
            self.update_graph_and_corpus(self.tokenize(prompt))
        return self._map_users(response, slack)
