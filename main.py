import datetime
import json
import logging
import os

from discord import Intents
from discord import utils as discord_utils
from discord.ext import commands
from dotenv import load_dotenv

log = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
CHANNEL = os.getenv("WEEKLY_CONCERT_CHANNEL")

BOARD_GAME_JSON = "/data/board_games_data.json"

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
        log.info(f"Fetching artists from file /data/{filename}")
        message = f"Here are all of the artists in the file {filename}:\n"
        all_artists = []
        with open(f"/data/{filename}", "r") as file:
            data = json.load(file)
            for artist in data["artists"]:
                all_artists.append(artist)
        all_artists.sort()
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
        "Here is a link to Jarvis' source code: https://github.com/aday913/aday-discord-bot\nHere is alink to GeminiBot's source code: https://github.com/aday913/gemini-discord-bot\nHere is a link to GPT_Bot's source code: https://github.com/aday913/gpt-discord-bot"
    )


@bot.command(name="games", help="Get information about board games")
async def games(ctx, *, args):
    log.info(f"Provided the following args: {args}")
    subcommand = args.split(" ")[0].strip().lower()
    game_name = " ".join(args.split(" ")[1:])
    log.info(f"Games command called with subcommand {subcommand}")
    games_data = get_game_info()
    if str(subcommand) == "list":
        message = "## Here are the available games:\n"
        for game in games_data:
            message += f"**{game}**: \n"
            message += f"> **Tags**: {games_data[game]['Tags']}\n"
            message += (
                f"> **Ideal Number of Players**: {games_data[game]['BestNumPlayer']}\n"
            )
            message += f"> **Play Time**: {games_data[game_name].get('Time (min)')}\n"
            if len(message) > 1000:
                log.info(
                    f"Attempting to send message with length {len(message)}:\n{message}"
                )
                await ctx.send(message)
                message = ""
        await ctx.send(message)
    elif subcommand == "info":
        if game_name is None:
            await ctx.send("Please provide a game name.")
            return
        game_name = game_name.strip().lower()
        if games_data.get(game_name):
            message = f"## Here is the information for {game_name}:\n"
            message += f"**Board Game Geek Rating** (out of 10): {games_data[game_name].get('BGG Rating')}\n"
            message += f"**Complexity** (out of 5): {games_data[game_name].get('Complexity')}\n"
            message += f"**Tags**: {games_data[game_name].get('Tags')}\n"
            message += f"**Minmum Age**: {games_data[game_name].get('Ages')}\n"
            message += f"**Possible Player Counts**: {games_data[game_name].get('NumPlayers')}\n"
            message += f"**Ideal Number of Players**: {games_data[game_name].get('BestNumPlayer')}\n"
            message += f"**Play Time**: {games_data[game_name].get('Time (min)')}\n"
            message += f"**Description**: {games_data[game_name].get('Summary')}\n"
            message += (
                f"**Link to Board Game Geek**: {games_data[game_name].get('URL')}\n"
            )
            log.info(
                f"Attempting to send the following message with length {len(message)}:\n{message}"
            )
            await ctx.send(message)
        else:
            await ctx.send(f"Sorry, I don't have information for {game_name}.")
    elif subcommand == "players":
        if game_name is None:
            await ctx.send("Please provide a player count.")
            return
        try:
            _ = int(game_name)
        except ValueError:
            await ctx.send("Please provide a valid number of players.")
            return
        if int(game_name) < 1:
            await ctx.send("Please provide a valid number of players.")
            return
        num_players = game_name
        message = f"## Here are the games that support {num_players} players:\n"
        if int(num_players) >= 6:
            num_players = "6+"
        for game in games_data:
            if num_players in games_data[game]["NumPlayers"]:
                message += f"**{game}**: \n"
                message += f"> **Tags**: {games_data[game]['Tags']}\n"
                message += f"> **Ideal Number of Players**: {games_data[game]['BestNumPlayers']}\n"
                if len(message) > 1000:
                    log.info(
                        f"Attempting to send the following message with length {len(message)}:\n{message}"
                    )
                    await ctx.send(message)
                    message = ""
        log.info(
            f"Attempting to send the following message with length {len(message)}:\n{message}"
        )
        await ctx.send(message)

    else:
        await ctx.send(
            "Sorry, I don't know that command. Try using !games list to see the available games."
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


def get_game_info() -> dict:
    """
    Get all the board game data from the Notion database json file and return it as a dictionary
    """
    log.info("Calling get_game_info function")
    data = {}
    try:
        with open(BOARD_GAME_JSON, "r") as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        log.error(f"File {BOARD_GAME_JSON} not found")
        return data

    for game in raw_data["results"]:
        try:
            name = game["properties"]["Name"]["title"][0]["plain_text"].lower()
        except Exception as error:
            log.error(f"Error when trying to get game name: {error}")
            continue
        data[name] = {}
        for property in game["properties"]:
            try:
                if property == "Name":
                    continue
                if game["properties"][property]["type"] == "select":
                    data[name][property] = game["properties"][property]["select"][
                        "name"
                    ]
                elif game["properties"][property]["type"] == "multi_select":
                    data[name][property] = ", ".join(
                        [
                            tag["name"]
                            for tag in game["properties"][property]["multi_select"]
                        ]
                    )
                elif game["properties"][property]["type"] == "number":
                    data[name][property] = game["properties"][property]["number"]
                elif game["properties"][property]["type"] == "url":
                    data[name][property] = game["properties"][property]["url"]
                elif game["properties"][property]["type"] == "rich_text":
                    data[name][property] = "".join(
                        [
                            text["plain_text"]
                            for text in game["properties"][property]["rich_text"]
                        ]
                    )
                else:
                    log.warning(
                        f"Unknown property type: {game['properties'][property]}"
                    )
                    continue
            except Exception as error:
                log.error(f"Error when trying to get property {property}: {error}")
                continue
    log.info(f"Found the following game names: {', '.join([i for i in data.keys()])}")
    props = []
    for name in data:
        for property in data[name]:
            if property not in props:
                props.append(property)
    log.info(f"Found the following properties: {', '.join([i for i in props])}")
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    log = logging.getLogger(__name__)

    try:
        bot.run(TOKEN)
    except Exception as error:
        print(error)
        TOKEN = os.environ.get("DISCORD_TOKEN")
        bot.run(TOKEN)
