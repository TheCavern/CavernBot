import io

import numpy as np
from matplotlib import image as mpimg, pyplot as plt
import matplotlib.patheffects as path_effects
from peewee import fn

from CavernBot.constants import SuggestionStatus, cfg
from CavernBot.models.Suggestions import SuggestionVote, Suggestion


def suggestion_stats(suggestion_id=None, user_id=None):
    positive = None
    negative = None

    if suggestion_id:
        positive = len(
            SuggestionVote.select().where(SuggestionVote.vote == 1, SuggestionVote.suggestion_id == suggestion_id))
        negative = len(
            SuggestionVote.select().where(SuggestionVote.vote == -1,
                                          SuggestionVote.suggestion_id == suggestion_id))
    elif user_id:
        positive = len(
            SuggestionVote.select().where(SuggestionVote.vote == 1, SuggestionVote.user_id == user_id))
        negative = len(
            SuggestionVote.select().where(SuggestionVote.vote == -1,
                                          SuggestionVote.user_id == user_id))

    y = np.array([positive, negative])
    labels = ["Upvotes", "Downvotes"]
    colors = ["#4c9c43", "#f02222"]

    # Load background image
    img = mpimg.imread(f"./assets/{cfg.graphs.pie_chart_asset}")

    # Create figure and axis
    fig, ax = plt.subplots()

    fig.patch.set_facecolor('black')  # A color to see the transparency
    fig.patch.set_alpha(0.01)  # Example: 50% transparency

    # Show background image
    ax.imshow(img, extent=[-0.8, 0.8, -0.8, 0.8], aspect='auto', alpha=0.6)

    # Create pie chart with transparency
    wedges, texts = ax.pie(
        y,
        labels=labels,
        colors=colors,
        startangle=90,
        wedgeprops={'alpha': 0.60, 'linewidth': 1, 'edgecolor': 'black'},
        labeldistance=0.3,  # move labels closer to the center
    )

    for text in texts:
        text.set_color("#ffffff")

    # Equal aspect ratio so pie is circular
    ax.set_aspect("equal")

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()

    return buffer


def suggestion_user_stats(user_id):

    latest_suggestions = list(Suggestion.select().where(
        (Suggestion.user_id == user_id) & (Suggestion.status.not_in([SuggestionStatus.DENIED, SuggestionStatus.PENDING]))
    ).order_by(-Suggestion.id).limit(10))

    ids = [s.id for s in latest_suggestions]

    # Sample data
    colors = ["#4c9c43", "#f02222"]
    suggestion_ids = [str(_id) for _id in ids]

    raw_upvotes = list(SuggestionVote.select(SuggestionVote.suggestion_id, fn.COUNT(SuggestionVote.vote).alias('votes')).where(
        (SuggestionVote.vote == 1) & (SuggestionVote.suggestion_id << suggestion_ids)).group_by(SuggestionVote.suggestion_id).order_by(-SuggestionVote.suggestion_id))

    upvotes = [sv.votes for sv in raw_upvotes]

    raw_downvotes = list(SuggestionVote.select(SuggestionVote.suggestion_id, fn.COUNT(SuggestionVote.vote).alias('votes')).where(
        (SuggestionVote.vote == -1) & (SuggestionVote.suggestion_id << suggestion_ids)).group_by(
        SuggestionVote.suggestion_id).order_by(-SuggestionVote.suggestion_id))

    downvotes = [sv.votes for sv in raw_downvotes]


    if not len(suggestion_ids):
        suggestion_ids = ["No Suggestions"]
    if not len(upvotes):
        upvotes = [0]
    if not len(downvotes):
        downvotes = [0]

    x = np.arange(len(suggestion_ids))  # the label locations
    width = 0.35  # width of the bars

    # Load background image
    img = mpimg.imread(f"./assets/{cfg.graphs.bar_graph_asset}")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_facecolor('none')  # makes axes transparent
    ax.set_alpha(0.01)  # Example: 50% transparency
    fig.patch.set_facecolor('#8f8888')  # makes figure transparent
    fig.patch.set_alpha(0.01)  # Example: 50% transparency

    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')

    ax.tick_params(axis='x', colors='white')  # x-axis ticks
    ax.tick_params(axis='y', colors='white')  # y-axis ticks

    # # Add background image
    ax.imshow(img,
              extent=[-0.5, len(suggestion_ids)-0.5, 0, max(np.array(upvotes)+np.array(downvotes))*1.2],
              aspect='auto',
              alpha=0.4,
              zorder=1)  # fully opaque

    # Plot stacked bars
    bars1 = ax.bar(x, upvotes, width, label='Upvotes', color=colors[1], alpha=0.7, zorder=1, edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x, downvotes, width, bottom=upvotes, label='Downvotes', color=colors[0], alpha=0.7, zorder=1, edgecolor='black', linewidth=1.5)

    # Function to add outlined text
    def add_label(ax, x_pos, y_pos, text, color):
        txt = ax.text(x_pos, y_pos, text, ha='center', va='center', color=color, weight='bold')
        # Add black outline
        txt.set_path_effects([path_effects.Stroke(linewidth=2, foreground='black'),
                              path_effects.Normal()])

    for i in range(len(suggestion_ids)):
        # Bottom segment
        add_label(ax, x[i], upvotes[i] / 2, str(upvotes[i]), color='#f24024')
        # Top segment
        add_label(ax, x[i], upvotes[i] + downvotes[i] / 2, str(downvotes[i]), color='#1df086')

    # Labels, title, legend
    ax.set_xticks(x)
    ax.set_xticklabels(suggestion_ids)
    ax.set_ylabel("Total Votes", color="white")
    ax.set_xlabel("Suggestion", color="white")
    # ax.set_title("")
    leg = ax.legend()
    leg.get_frame().set_facecolor('#6b6969')
    leg.get_frame().set_edgecolor('none')  # border color
    leg.get_frame().set_linewidth(2)  # border thickness

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()

    return buffer
