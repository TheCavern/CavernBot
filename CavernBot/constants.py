import re

from disco.types.application import InteractionCallbackType
from disco.types.message import component, MessageFlags
from disco.util.config import Config

from CavernBot.utils.rng import get_random_element

cfg = Config.from_file('./config/config.yaml')

messages = Config.from_file('./config/messages.yaml')

# Permission denied message :)
def send_you_dont_have_the_right(event, reason=None):
    permission_denied_component = component(messages.suggestions.shall_not_pass.to_dict())
    permission_denied_component.components[2].items.append(
        {"media": {"url": get_random_element(messages.suggestions.shall_not_pass_potential_gifs)}})
    if reason:
        permission_denied_component.components[-1].content = reason
    return event.reply(type=InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                       components=[permission_denied_component],
                       flags=(MessageFlags.EPHEMERAL ^ MessageFlags.IS_COMPONENTS_V2))

def get_category_from_value(category_value, return_string=False):

    for category in cfg.discord.suggestions.categories:
        if category["value"] == category_value:
            if return_string:
                return f"{category.get("emote") + ' '}{category["name"]}"
            else:
                return category

    return None

class SuggestionStatus(object):
    PENDING = 0
    DENIED = 1
    VOTING = 2
    APPROVED = 3
    COMMUNITY_DENIED = 4
    IMPLEMENTED = 5
    FORCED_DENIED = 6
    FORCED_APPROVED = 7
    NOT_IMPLEMENTING = 8
    WORK_IN_PROGRESS = 9

class Constants(object):
    VERSION = "1.1-Beta"

    LOGGING_CHANNEL = cfg.discord.logging_channel

    SUGGESTIONS_VOTE_CHANNEL = cfg.discord.suggestions.vote_channel
    SUGGESTIONS_PENDING_CHANNEL = cfg.discord.suggestions.pending_channel
    SUGGESTIONS_DENIED_CHANNEL = cfg.discord.suggestions.denied_channel
    SUGGESTIONS_APPROVED_CHANNEL = cfg.discord.suggestions.approved_channel
    SUGGESTIONS_SINFO_PERMISSIONS = cfg.discord.suggestions.sinfo_roles
    SUGGESTIONS_BANNED_ROLE = cfg.discord.suggestions.banned_role

    TICKETS_BASE_CHANNEL = cfg.discord.tickets.base_channel

    MEDIA_CHANNEL = cfg.discord.media_channel
    STAFF_ROLES = cfg.discord.staff_roles

    EMOJI_RE = re.compile(r"<(a?)?:(\w+):(\d{18})>?")
    MASKED_LINKS_RE = re.compile(r"\[.+\]\(.+\)")
