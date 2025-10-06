# CaverBot
Note that this readme is a WIP. Tired me needed to put stuff in here though. THANKS TIRED ME!

Sidenote: When this doesn't get updated in a week, yell at me. `@thatrandojustin` on discord.

## Features
* Suggestions
  * Allow for users to submit community suggestions for voting.
  * Configurable categories (including emotes :D)
  * GRAPHS!!! (with configurable watermarks!)
  * slash commands! (and components v2)
    * Is this even a feature anymore?

# Setup

## Development
1) Clone repo
2) `docker compose -f compose-dev.yaml up`
3) Profit.
    * If you're someone who likes to test their instance as they work, I've left a comment that lets you bind mount the entire project. You're welcome, or not, you decide.

## Production
1. You don't *need* to clone the repo, but it could help with updating the config folders when needed.
2. Edit ALL the configs to your liking. 
    * **YES**, all of them. Also ensure to update the example.env and config-example.yaml to .env and config.yaml so that the bot actually reads them :D
    * oh, and grab a discord bot token ig. Probably the important part...
3. `docker compose up -d` 

# Usage

## Commands

* `/suggestion create` - Opens a modal for users to fill in information about their suggestion.
  * The bot will filter out masked links, bc markdown is nice to look at!
* `/suggestion info [user:user] [suggestion:int]` - Lets you get stats about a suggestion (or a user)
  * `Note`: This is locked to either the suggestor, or the user running the command. To bypass, you need to allow the roles with the config option.

* `/approve [suggestion:int]` `/deny [suggestion:int] [reason:str]` - Commands to approve/deny suggestions in the pending queue. For people who dislike clicking buttons, or wish to supply a reason with the denial! Denials get told to the user.

## Process
1) User makes an initial suggestion with `/suggestion create`
2) User gets told it was submitted, and moderators get a new message with the suggestion!
3) Moderators can approve or deny it.
4) If denied, the user gets a DM saying it was denied (*with a possible reason*). If approved, it get shoved into the approved channel for your community to start throwing their opinions at it! *With a thread to REALLY let the canon fire...*
5) When ~~MATH~~ happens, the suggestion will either be moved to denied or community approved for final handling. Where it can be marked as implemented, WIP, not implementing, or simply stay as "Community Approved".
6) Did I mention there are graphs?