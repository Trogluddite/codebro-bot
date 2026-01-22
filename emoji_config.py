import re
from typing import Optional, List, Tuple

import yaml

import discord_helpers


class EmojiMapping:
    """Representation of a single regex pattern => emoji string. Regex patterns are case insensitive"""
    def __init__(self, regex_str: str, emoji_str: str, guild_id: int):
        # sanitize regex str for lookups later
        self.regex_str = EmojiMapping.sanitize_regex_str(regex_str)
        self.regex_pattern = re.compile(regex_str, re.IGNORECASE)

        #sanitize the emoji string for lookups later
        self.emoji_str = discord_helpers.sanitize_emoji_str(emoji_str)

        self.guild_id = guild_id

    @staticmethod
    def sanitize_regex_str(regex_str: str):
        return regex_str.upper() if regex_str is not None else None


class EmojiConfig:
    def __init__(self, emoji_config_list: List[EmojiMapping]):
        self.emoji_config_list = emoji_config_list

    def find_mapping_via_regex_str(self, regex_str: str, guild_id: int) -> Optional[EmojiMapping]:
        """Try to find an existing emoji mapping with the same guild id and regex"""
        regex_str = EmojiMapping.sanitize_regex_str(regex_str)

        for emoji_mapping in self.emoji_config_list:
            if emoji_mapping.guild_id != guild_id:
                continue

            if emoji_mapping.regex_str == regex_str.upper():
                return emoji_mapping
        return None

    def find_emoji_for_message_token(self, token_str: str, guild_id: int) -> Optional[EmojiMapping]:
        """Try to find the first emoji mapping for the provided guild whose regex matches the token_str"""
        for emoji_mapping in self.emoji_config_list:
            if emoji_mapping.guild_id != guild_id:
                continue

            if emoji_mapping.regex_pattern.match(token_str) is not None:
                return emoji_mapping
        return None

    def add_mapping(self, new_emoji_mapping: EmojiMapping):
        """Add a new mapping"""
        self.emoji_config_list.append(new_emoji_mapping)

    def remove_mappings_for_regex(self, regex_str: str, guild_id: int) -> int:
        """Remove all mappings for a given guild which have the same regex string"""
        removed = 0
        mapping = self.find_mapping_via_regex_str(regex_str, guild_id)
        while mapping is not None:
            self.emoji_config_list.remove(mapping)
            removed += 1
            mapping = self.find_mapping_via_regex_str(regex_str, guild_id)
        return removed

    def get_mappings_for_guild(self, guild_id: int) -> List[EmojiMapping]:
        """Get all mappings for a given guild id"""
        matching_mappings = list(filter(lambda c: c.guild_id == guild_id, self.emoji_config_list))
        return matching_mappings


def write_emoji_config(filename: str, new_emoji_config: EmojiConfig):
    yaml_dict = dict()
    entry_list = list()
    yaml_dict['EmojiMappings'] = entry_list
    for t in new_emoji_config.emoji_config_list:
        entry_dict = dict()
        entry_dict['regex'] = t.regex_str
        entry_dict['emoji_str'] = t.emoji_str
        entry_dict['guild_id'] = t.guild_id
        entry_list.append(entry_dict)

    yaml_content = yaml.dump(yaml_dict)
    with open(filename, 'w', encoding='utf8') as outfile:
        outfile.write(yaml_content)


def read_emoji_config(file_name: Optional[str]) -> EmojiConfig:
    config_list: List[EmojiMapping] = list()
    try:
        if file_name is not None and file_name != '':
            with open(file_name, 'r', encoding='utf8') as infile:
                yaml_dict = yaml.load(infile.read(), Loader=yaml.Loader)
                emoji_mappings = yaml_dict['EmojiMappings'] if 'EmojiMappings' in yaml_dict else list()
                for mapping in emoji_mappings:
                    emoji_str = mapping['emoji_str']
                    regex_str = mapping['regex']
                    guild_id_str = mapping['guild_id']
                    try:
                        guild_id = int(guild_id_str)
                        config_list.append(EmojiMapping(regex_str, emoji_str, guild_id))
                    except:
                        continue

    except:
        print('Error reading emoji config')
    return EmojiConfig(config_list)
