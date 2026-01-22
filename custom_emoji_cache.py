import datetime
from typing import Dict, Tuple, Optional

import discord

import discord_helpers
from emoji_config import EmojiMapping


class CustomEmojiCache:
    def __init__(self, cache_lifetime: Optional[datetime.timedelta] = None):
        self.cache_lifetime = cache_lifetime if cache_lifetime is not None else datetime.timedelta(days=1)
        self.__cached_guild_emoji: Dict[int, Tuple[datetime.datetime, Dict[str, discord.Emoji]]] = dict()

    async def get_or_fetch_custom_emojis(
            self,
            guild: discord.Guild,
            force_refresh_emoji: bool = False
    ) -> Dict[str, discord.Emoji]:
        """Grab from cache or build a lookup table of sanitized emoji name => discord.Emoji objects for a given guild"""
        fetch_emoji = force_refresh_emoji
        now = datetime.datetime.utcnow()
        if not fetch_emoji:
            if guild.id not in self.__cached_guild_emoji:
                # Don't have any cached emoji for this guild
                fetch_emoji = True
            else:
                # Have cached emoji, but it might be too old
                cache_expiry, emoji_dict = self.__cached_guild_emoji[guild.id]
                if now > cache_expiry:
                    fetch_emoji = True

        if fetch_emoji:
            emojis = await guild.fetch_emojis()
            emoji_dict = dict()
            for emoji in emojis:
                emoji_name_sanitized = discord_helpers.sanitize_emoji_str(emoji.name)
                emoji_dict[emoji_name_sanitized] = emoji

            expiry_time = now + self.cache_lifetime
            self.__cached_guild_emoji[guild.id] = (expiry_time, emoji_dict)

        cached_at, emoji_dict = self.__cached_guild_emoji[guild.id]
        return emoji_dict

    async def find_custom_emoji_with_name(self, guild: discord.guild, emoji_name: str, force_refresh_emoji: bool = False):
        emoji_lookup = await self.get_or_fetch_custom_emojis(guild, force_refresh_emoji)

        discord_emoji_format_match = discord_helpers.try_parse_discord_emoji_format(emoji_name)
        if discord_emoji_format_match is not None:
            # Emoji str is a custom emoji used literally. Replace emoji_str with just the name for consistency
            emoji_name = discord_emoji_format_match.emoji_name

        sanitized_emoji_name = discord_helpers.sanitize_emoji_str(emoji_name)
        return emoji_lookup[sanitized_emoji_name] if sanitized_emoji_name in emoji_lookup else None

