import datetime
import json
import logging
import os
import random

import asyncio
from discord import Intents
from discord import utils as discord_utils
from discord.ext import commands, tasks
from dotenv import load_dotenv

log = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
CHANNEL = os.getenv("WEEKLY_CONCERT_CHANNEL")

intents = Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

try:
    with open("/data/user_to_json.json", "r") as f:
        user_to_json = json.load(f)
        log.info("Imported existing user_to_json.json file for mappings")
except FileNotFoundError:
    log.warning("No user_to_json file found, starting an empty dict for mappings")
    user_to_json = {}

# Command to add a user and their JSON file


@bot.command(name="concerts")
async def concerts(ctx, subcommand, user_name=None, json_file_name=None):
    if subcommand == "add":
        # Add or update the user-to-JSON mapping

        # We need to add a new user to the file mappings
        if user_name not in list(user_to_json.keys()):
            user_to_json[user_name] = []

        # We can check if the user is already linked to that json file
        if f"/data/{json_file_name}" in user_to_json[user_name]:
            await ctx.send(f"/data/{json_file_name} already linked to {user_name}")
            return

        user_to_json[user_name].append(f"/data/{json_file_name}")
        with open("/data/user_to_json.json", "w") as f:
            log.info(
                f"Adding user {user_name} to concert json file /data/{json_file_name}"
            )
            json.dump(user_to_json, f, indent=2)
        await ctx.send(f"Linked {user_name} to {json_file_name}.")

    elif subcommand == "list":
        # Check if the user is linked to a JSON file
        if user_name in user_to_json:
            # Load the data from the JSON file
            log.info(f"Fetching concert json data for user {user_name}")
            try:
                # For every json file linked to the user, we send them every event's artist, date, and venue
                for file_name in user_to_json[user_name]:
                    log.info(f"Reading file {file_name}")
                    message = f"## Upcoming concerts for user @{user_name} from file {file_name}:\n"
                    num_events = 0
                    with open(file_name, "r") as file:
                        log.debug(f"Loaded file with name {file_name}")
                        data = json.load(file)
                        # Process and send concert data
                        for artist in data["artists"]:
                            if len(data["artists"][artist]["events"]) == 0:
                                continue
                            log.info(f"Artist {artist} has events...")
                            message += f"**{artist}**: \n"
                            for event in data["artists"][artist]["events"]:
                                num_events += 1
                                concert_datetime = datetime.datetime.strptime(
                                    event["datetime_local"].split("T")[0], "%Y-%m-%d"
                                )
                                formatted_date = datetime.datetime.strftime(
                                    concert_datetime, "%A %B %d, %Y"
                                )
                                message += f"> *{formatted_date}* in {event['venue']['city']} at {event['venue']['name']}\n"
                            if len(message) > 1000 and num_events != 0:
                                await ctx.send(message)
                                message = ""
                    if num_events != 0 and message != "":
                        await ctx.send(message)
            except FileNotFoundError:
                await ctx.send("Error: JSON file not found.")
        else:
            await ctx.send(f"No file linked for {user_name}.")
    elif subcommand == "files":
        message = "The following files are available to watch:"
        for f in os.listdir("/data/"):
            if "concert" not in f:
                continue
            message += f"\n{f}"
        if message != "The following files are available to watch:":
            await ctx.send(message)


@bot.command(name="artists", help="Get all artists from a concert json file")
async def get_artists(ctx, filename: str):
    try:
        log.info(f"Fetching artists from file {filename}")
        message = f"Here are all of the artists in the file {filename}:\n"
        all_artists = []
        with open(filename, "r") as file:
            data = json.load(file)
            for artist in data["artists"]:
                all_artists.append(artist)
        message = message + "\n".join(all_artists)
        await ctx.send(message)
    except Exception as error:
        log.error(f"Error when trying to get artists from file: {error}")
        await ctx.send("Sorry, I had trouble getting the info for that!")


@bot.command(
    name="sources", help="Provides links to the github repos for the server's bots"
)
async def get_sources(ctx):
    await ctx.send(
        "Here is a link to Jarvis' source code: https://github.com/aday913/aday-discord-bot\nAnd here is alink to GeminiBot's source code: https://github.com/aday913/gemini-discord-bot"
    )


@bot.command(name="create-channel")
@commands.has_role("admin")
async def create_channel(ctx, channel_name="real-python"):
    guild = ctx.guild
    existing_channel = discord_utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        print(f"Creating a new channel: {channel_name}")
        await guild.create_text_channel(channel_name)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send("You do not have the correct role for this command.")


# Start the loop when the bot is ready
@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user.name}")
    # weekly_concerts.start()  # Start the scheduled task


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    log = logging.getLogger(__name__)

    try:
        bot.run(TOKEN)
    except Exception as error:
        print(error)
        TOKEN = os.environ.get("DISCORD_TOKEN")
        bot.run(TOKEN)
