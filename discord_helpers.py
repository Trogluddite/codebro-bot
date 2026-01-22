import re
from typing import Optional, Tuple, NamedTuple

EMOJI_PARSE_REGEX = re.compile('<:(?P<emoji_name>.+):(?P<emoji_id>[0-9]+)>', re.IGNORECASE)


class ParsedEmojiString(NamedTuple):
    emoji_id: int = -1
    emoji_name: str = None


def try_parse_discord_emoji_format(input_str: str) -> Optional[ParsedEmojiString]:
    """Try to parse an input string as a discord emoji representation, which looks like <:emoji_name:01234>"""
    if input_str is None:
        return None

    match = EMOJI_PARSE_REGEX.match(input_str)
    if match is None:
        return None

    emoji_name = sanitize_emoji_str(match.group('emoji_name'))
    emoji_id = int(match.group('emoji_id'))
    return ParsedEmojiString(emoji_id, emoji_name)


def sanitize_emoji_str(emoji_str: str):
    """Sanitize an emoji string into lowercase so lookups work everywhere"""
    return emoji_str.lower() if emoji_str is not None else None
