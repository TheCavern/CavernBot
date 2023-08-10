import yaml

with open('config.yaml', 'r') as f:
    loaded = yaml.load(f.read(), Loader=yaml.FullLoader)
    locals().update(loaded.get('constants', {}))


class Constants(object):
    VERSION = "1.1-Beta"

    LOGGING_CHANNEL = loaded['discord']['logging_channel']

    SUGGESTIONS_VOTE_CHANNEL = loaded['discord']['suggestions']['vote_channel']
    SUGGESTIONS_PENDING_CHANNEL = loaded['discord']['suggestions']['pending_channel']
    SUGGESTIONS_DENIED_CHANNEL = loaded['discord']['suggestions']['denied_channel']
    SUGGESTIONS_APPROVED_CHANNEL = loaded['discord']['suggestions']['approved_channel']
    SUGGESTIONS_SINFO_PERMISSIONS = loaded['discord']['suggestions']['sinfo_roles']
    SUGGESTIONS_BANNED_ROLE = loaded['discord']['suggestions']['banned_role']

    TICKETS_BASE_CHANNEL = loaded['discord']['tickets']['base_channel']

    MEDIA_CHANNEL = loaded['discord']['media_channel']
    STAFF_ROLES = loaded['discord']['staff_roles']
