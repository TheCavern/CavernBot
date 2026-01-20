from datetime import datetime, timezone

from disco.types.message import SectionComponent, TextDisplayComponent, ThumbnailComponent, ContainerComponent, \
    SeparatorComponent, SeparatorSpacingSize, ActionRow, MediaGalleryComponent, MediaGalleryItem, ButtonComponent, \
    ButtonStyles, SelectOption, SelectMenuComponent, LabelComponent, TextInputComponent, TextInputStyles, MessageModal
from peewee import fn

from CavernBot.constants import SuggestionStatus, messages, Constants, cfg, get_category_from_value
from CavernBot.models import iso_to_datetime
from CavernBot.models.Suggestions import Suggestion, SuggestionVote

separator_small = SeparatorComponent(spacing=SeparatorSpacingSize.SMALL)
separator_large = SeparatorComponent(spacing=SeparatorSpacingSize.LARGE)
separator_none = SeparatorComponent(spacing=SeparatorSpacingSize.SMALL, divider=False)

status_to_string = {
    SuggestionStatus.APPROVED: "Approved",
    SuggestionStatus.FORCED_APPROVED: "Force Approved",
    SuggestionStatus.VOTING: "Voting",
    SuggestionStatus.IMPLEMENTED: "Implemented",
    SuggestionStatus.WORK_IN_PROGRESS: "Work in Progress",
    SuggestionStatus.NOT_IMPLEMENTING: "Will not Implement",
}

def suggestion_info_ui_suggestion(event, suggestion, suggesting_user):

    vote_stats = list(
        SuggestionVote.select(SuggestionVote.vote, fn.count(SuggestionVote.vote).alias("vote_totals")).where(
            SuggestionVote.suggestion_id == suggestion.id).group_by(SuggestionVote.vote).order_by(SuggestionVote.vote)
    )

    vote_totals = {

    }

    for v in vote_stats:
        vote_totals[v.vote] = v.vote_totals

    total = sum(vote_totals.values())


    header = SectionComponent(
        components=[
            TextDisplayComponent(
                content=f"# `{suggestion.id}` {get_category_from_value(suggestion.category, return_string=True)} \n-# by <@{suggesting_user.id}> (`{suggesting_user.username}`)")
        ],
        accessory=ThumbnailComponent(media={"url": suggesting_user.avatar_url})
    )

    section = SectionComponent(
        components=[
            TextDisplayComponent(
                content=f"## Vote Stats\n* Positive: **{vote_totals.get(1, 0)}** (`{round(vote_totals.get(1, 0) / total * 100)}%`)\n* Negative: **{vote_totals.get(-1, 0)}** (`{round(vote_totals.get(-1, 0) / total * 100)}%`)")
        ],
        accessory=ThumbnailComponent(media={"url": f"attachment://stats_{suggestion.id}.png"})
    )

    container_component = ContainerComponent()

    container_component.components = [
        separator_large,
        TextDisplayComponent(
            content=suggestion.description),
        separator_small,
        section,
        separator_small,
        TextDisplayComponent(
            content=f"-# Suggested on <t:{int(iso_to_datetime(suggestion.created_at).timestamp())}:F> (<t:{int(iso_to_datetime(suggestion.created_at).timestamp())}:R>)")
    ]

    components = [
        header,
        container_component,
    ]

    return components

def suggestion_info_ui_user(event, user):

    stats = {}

    total_suggestion_stats = list(
        Suggestion.select(Suggestion.status, fn.count(Suggestion.status).alias("status_totals")).where(Suggestion.user_id == user.id).group_by(Suggestion.status)
    )

    for status in total_suggestion_stats:
        stats[status.status] = status.status_totals

    vote_totals = {}

    vote_stats = list(
        SuggestionVote.select(SuggestionVote.vote, fn.count(SuggestionVote.vote).alias("vote_totals")).where(
            SuggestionVote.user_id == user.id).group_by(SuggestionVote.vote).order_by(SuggestionVote.vote)
    )

    for v in vote_stats:
        vote_totals[v.vote] = v.vote_totals

    total = sum(vote_totals.values())



    section = SectionComponent(
        components=[
            TextDisplayComponent(
                content=f"# <@{user.id}> (`{user.username}`) Suggestion Stats\n-# **Total Suggestions**: `{sum(stats.values())}` | **Approved**: `{stats.get(SuggestionStatus.APPROVED, 0)}` | **Denied**: `{stats.get(SuggestionStatus.COMMUNITY_DENIED, 0)}` | **Implemented**: `{stats.get(SuggestionStatus.IMPLEMENTED, 0)}`")
        ],
        accessory=ThumbnailComponent(media={"url": user.avatar_url})
    )

    container_component = ContainerComponent()

    items = [
        MediaGalleryItem(media={"url": f"attachment://suggestion_stats_{user.id}.png"})
    ]

    stats_graph = MediaGalleryComponent()

    stats_graph.items = items

    container_component.components = [
        SectionComponent(
            components=[
                TextDisplayComponent(content=f"## Vote Stats\n* Positive: **{vote_totals.get(1, 0)}** (`{round(vote_totals.get(1, 0) / total * 100)}%`)\n* Negative: **{vote_totals.get(-1, 0)}** (`{round(vote_totals.get(-1, 0) / total * 100)}%`)")
            ],
            accessory=ThumbnailComponent(media={"url": f"attachment://vote_stats_{user.id}.png"})
        ),
        separator_small,
        TextDisplayComponent(content="## Latest Suggestion Stats\n-# Using latest 10 suggestions"),
        stats_graph
    ]

    components = [
        section,
        container_component,
    ]

    return components

def community_voting_suggestion(event, suggestion, suggesting_user, media=None):
    header = TextDisplayComponent(content=f"# {get_category_from_value(suggestion.category, return_string=True)} Suggestion")

    container_component = ContainerComponent()

    # media_test = MediaGalleryComponent()
    # media_test.items = [
    #     MediaGalleryItem(media={"url": "https://fatyoshi.dev/yoshis/AllYoshi.png"}, description="Sev's Yoshi"),
    #     MediaGalleryItem(media={"url": "https://fatyoshi.dev/yoshis/NewYorkshi.png"}),
    #     MediaGalleryItem(media={"url": "https://fatyoshi.dev/yoshis/Ronshi.png"}),
    #     MediaGalleryItem(media={"url": "https://fatyoshi.dev/yoshis/Solshi.png"}),
    # ]

    container_component.components = [
        separator_large,
        TextDisplayComponent(
            content=f"{suggestion.description}"),
        # separator_small,
        # media_test,
        separator_large,
        ActionRow(
            components=[
                ButtonComponent(style=ButtonStyles.SUCCESS, label="Upvote", custom_id=f"upvote_{suggestion.id}"),
                ButtonComponent(style=ButtonStyles.DANGER, label="Downvote", custom_id=f"downvote_{suggestion.id}"),
            ]
        ),
        separator_none,
        TextDisplayComponent(content=f"-# Suggestion `{suggestion.id}` by <@{suggestion.user_id}> (`{suggesting_user.username}`) (<t:{int(iso_to_datetime(suggestion.created_at).timestamp())}:R>)"),
    ]

    components = [
        header,
        container_component,
    ]

    return components

def pending_suggestion(event, suggestion, media=None):
    section = SectionComponent(
        components=[
            TextDisplayComponent(
                content=f"# `{suggestion.id}` {get_category_from_value(suggestion.category, return_string=True)}\nSubmitted by <@{event.member.id}> (<t:{int(datetime.now(timezone.utc).timestamp())}:R>)") # \n-# Total Suggestions: 10 | Approved: 1 | Denied: 3 | Implemented: 0
        ],
        accessory=ThumbnailComponent(media={"url": event.member.user.avatar_url})
    )

    container_component = ContainerComponent()

    # media_test = MediaGalleryComponent()
    # media_test.items = [
    #     MediaGalleryItem(media={"url": "https://fatyoshi.dev/yoshis/AllYoshi.png"}, description="Sev's Yoshi"),
    #     MediaGalleryItem(media={"url": "https://fatyoshi.dev/yoshis/NewYorkshi.png"}),
    # ]

    select_options = [
        SelectOption(label="Pending", description="Leave suggestion pending.", value="pending", default=True),
        SelectOption(label="Approve", description="Approve this suggestion.", value="approve"),
        SelectOption(label="Deny", description="Deny this suggestion.", value="deny"),
    ]

    sm = SelectMenuComponent(custom_id=f"update_pending_{suggestion.id}")
    sm.options = select_options

    container_component.components = [
        separator_large,
        TextDisplayComponent(
            content=suggestion.description),
        # separator_small,
        # media_test,
        separator_large,
        ActionRow(
            components=[
                sm
            ]
        ),
        separator_none,
    ]

    components = [
        section,
        container_component,
    ]

    return components

def suggestion_community_voting_complete(suggestion, user, outcome="Approved", old_status=None, event=None):
    vote_stats = list(
        SuggestionVote.select(SuggestionVote.vote, fn.count(SuggestionVote.vote).alias("vote_totals")).where(
            SuggestionVote.suggestion_id == suggestion.id).group_by(SuggestionVote.vote).order_by(SuggestionVote.vote)
    )

    vote_totals = {

    }

    for v in vote_stats:
        vote_totals[v.vote] = v.vote_totals

    total = sum(vote_totals.values())

    header = TextDisplayComponent(content=f"# `{suggestion.id}` {get_category_from_value(suggestion.category, return_string=True)} Community {outcome} \n-# by <@{user.id}> (`{user.username}`)")

    section = SectionComponent(
        components=[
            TextDisplayComponent(
                content=f"## Vote Stats\n* Positive: **{vote_totals.get(1, 0)}** (`{round(vote_totals.get(1, 0) / total * 100)}%`)\n* Negative: **{vote_totals.get(-1, 0)}** (`{round(vote_totals.get(-1, 0) / total * 100)}%`)")
        ],
        accessory=ThumbnailComponent(media={"url": f"attachment://final_graph_{suggestion.id}.png"})
    )

    container_component = ContainerComponent()

    select_options = [
        SelectOption(label="Community Approved", description="The suggestion has been approved by the community", value=SuggestionStatus.APPROVED,
                     default=(suggestion.status in [SuggestionStatus.APPROVED, SuggestionStatus.FORCED_APPROVED])),
        SelectOption(label="Will not Implement", description="This suggestion will not be implemented.", value=SuggestionStatus.NOT_IMPLEMENTING,
                     default=(suggestion.status == SuggestionStatus.NOT_IMPLEMENTING)),
        SelectOption(label="Implemented", description="Suggestion has been implemented!", value=SuggestionStatus.IMPLEMENTED,
                     default=(suggestion.status == SuggestionStatus.IMPLEMENTED)),
        SelectOption(label="Work In Progress", description="Working on it, but not implemented yet.", value=SuggestionStatus.WORK_IN_PROGRESS,
                     default=(suggestion.status == SuggestionStatus.WORK_IN_PROGRESS)),
    ]

    sm = SelectMenuComponent(custom_id=f"update_approved_{suggestion.id}", disabled=(suggestion.status in [SuggestionStatus.IMPLEMENTED, SuggestionStatus.NOT_IMPLEMENTING]))
    sm.options = select_options

    container_component.components = [
        separator_large,
        TextDisplayComponent(
            content=suggestion.description),
        separator_small,
        section,
        separator_small,
        TextDisplayComponent(
            content=f"-# Suggested on <t:{int(iso_to_datetime(suggestion.created_at).timestamp())}:F> (<t:{int(iso_to_datetime(suggestion.created_at).timestamp())}:R>)")
    ]

    if outcome == "Approved":
        container_component.components.append(separator_small)
        container_component.components.append(
            ActionRow(
                components=[
                    sm
                ]
            )
        )

    if suggestion.updated_by is not None:
        container_component.components.append(separator_none)
        container_component.components.append(TextDisplayComponent(
            content=f"-# Last updated by <@{suggestion.updated_by}> (`{event.member.user.username}`)\n-# [<t:{int(iso_to_datetime(suggestion.updated_at).timestamp())}:F> (<t:{int(iso_to_datetime(suggestion.updated_at).timestamp())}:R>)] {status_to_string.get(old_status)} → {status_to_string.get(suggestion.status)}")
        )


    components = [
        header,
        container_component,
    ]

    return components

def suggestion_create_modal(event, body=None, selected_category=None):
    categories = cfg.discord.suggestions.categories

    select_options = []

    for category in categories:
        option = SelectOption(label=category.get("name"), value=category.get("value"), default=(selected_category==category.get("value")))
        if category.get("emote"):
            matches = Constants.EMOJI_RE.match(category.get("emote"))
            if matches:
                option.emoji = {
                    "id": matches.group(3),
                    "name": matches.group(2),
                    "animated": matches.group(1)
                }
            else:
                option.emoji = {
                    "name": category.get("emote")
                }
        select_options.append(option)

    category_menu = SelectMenuComponent(custom_id="category_menu", required=True)
    category_menu.options = select_options

    modal = MessageModal(title="Submit New Suggestion", custom_id="suggestion_modal")

    modal.add_component(TextDisplayComponent(content=messages.suggestions.modal.header_text_display))

    modal.add_component(LabelComponent(
        label="Select Category",
        description="What type of suggestion are you making?",
        component=category_menu
    ))

    modal.add_component(LabelComponent(
        label="Suggestion", description="Describe your suggestion! Be as descriptive as possible!",
        component=TextInputComponent(custom_id="suggestion_body", style=TextInputStyles.PARAGRAPH,
                                     placeholder="Suggestion Body *with markdown support*!\n**MASKED LINKS WILL BE FILTERED!!**", value=body or "", max_length=3000),
        required=True))

    # TODO: Enable this when discord releases it out of alpha jail... ~Justin...
    # modal.add_component(TextDisplayComponent(
    #     content=f"Upload a picture or two to help express your suggestion!\n-# As this is reviewed by a moderator, ensure that any and all files you upload should still follow the community rules, along with the platform Terms of Service and Community Guidelines."))
    # file_upload = FileUploadComponent(custom_id="suggestion_files", min_values=0, max_values=4,
    #                                   required=False)
    #
    # file_label = LabelComponent(label="Supplementary Images",
    #                             description="Fancy images to help you explain your suggestion!",
    #                             component=file_upload)

    # modal.add_component(file_label)

    return modal

def suggestion_deny(event, suggestion, user, reason=None):
    rstring = f"\n> {reason}"

    section = SectionComponent(
        components=[
            TextDisplayComponent(
                content=f"# `{suggestion.id}` {get_category_from_value(suggestion.category, return_string=True)}\nSubmitted by <@{user.id}> (`{user.username}`) (<t:{int(iso_to_datetime(suggestion.created_at).timestamp())}:R>)")
            # \n-# Total Suggestions: 10 | Approved: 1 | Denied: 3 | Implemented: 0
        ],
        accessory=ThumbnailComponent(media={"url": user.avatar_url})
    )

    container_component = ContainerComponent()

    # media_test = MediaGalleryComponent()
    # media_test.items = [
    #     MediaGalleryItem(media={"url": "https://fatyoshi.dev/yoshis/AllYoshi.png"}, description="Sev's Yoshi"),
    #     MediaGalleryItem(media={"url": "https://fatyoshi.dev/yoshis/NewYorkshi.png"}),
    # ]

    container_component.components = [
        separator_large,
        TextDisplayComponent(
            content=suggestion.description),
        # separator_small,
        # media_test,
        separator_large,
        TextDisplayComponent(content=f"Denied by <@{event.member.id}> (`{event.member.user.username}`) <t:{int(datetime.now(timezone.utc).timestamp())}:R\n>{rstring if reason else ''}"),
        separator_none,
    ]

    components = [
        section,
        container_component,
    ]

    return components

def suggestion_denied_user_message(suggestion, reason=None):

    rstring = f"\n**Reason**:\n> {reason}"

    header = TextDisplayComponent(content=f"# Update on Suggestion `{suggestion.id}`")

    container = ContainerComponent()

    container.components = [
        TextDisplayComponent(content=f"## Your suggestion has been denied.{rstring if reason else ''}",),
        separator_large,
        TextDisplayComponent(
            content=suggestion.description),
    ]

    components = [
        header,
        container,
    ]

    return components

def force_update_suggestion(suggestion):

    select_options = [
        SelectOption(label="Force Approved", description="Move the suggestion to community approved.",
                     value=SuggestionStatus.FORCED_APPROVED,
                     default=(suggestion.status == SuggestionStatus.FORCED_APPROVED)),
        SelectOption(label="Will not Implement", description="This suggestion will not be implemented.",
                     value=SuggestionStatus.NOT_IMPLEMENTING,
                     default=(suggestion.status == SuggestionStatus.NOT_IMPLEMENTING)),
        SelectOption(label="Implemented", description="Suggestion has been implemented!",
                     value=SuggestionStatus.IMPLEMENTED,
                     default=(suggestion.status == SuggestionStatus.IMPLEMENTED)),
        SelectOption(label="Work In Progress", description="Working on it, but not implemented yet.",
                     value=SuggestionStatus.WORK_IN_PROGRESS,
                     default=(suggestion.status == SuggestionStatus.WORK_IN_PROGRESS)),
    ]

    sm = SelectMenuComponent(custom_id=f"update_suggestion_{suggestion.id}")
    sm.options = select_options

    modal = MessageModal(title=f"Update Suggestion {suggestion.id}", custom_id=f"force_update_suggestion_{suggestion.id}")

    modal.add_component(LabelComponent(
        label=f"Select New Status (Currently {status_to_string.get(suggestion.status)})",
        description="Set the new status for the suggestion.",
        component=sm
    ))

    return modal
