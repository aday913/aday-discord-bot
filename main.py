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

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = os.getenv('WEEKLY_CONCERT_CHANNEL')

intents = Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

user_to_json = {}

# Command to add a user and their JSON file
@bot.command(name='concerts')
async def concerts(ctx, subcommand, user_name=None, json_file_name=None):
    if subcommand == "add":
        # Add or update the user-to-JSON mapping
        user_to_json[user_name] = f'/data/{json_file_name}'
        with open('/data/user_to_json.json', 'w') as f:
            log.info(f'Adding user {user_name} to concert json file /data/{json_file_name}')
            json.dump(user_to_json, f, indent=2)
        await ctx.send(f"Linked {user_name} to {json_file_name}.")

    elif subcommand == "list":
        # Check if the user is linked to a JSON file
        if user_name in user_to_json:
            # Load the data from the JSON file
            log.info(f'Fetching concert json data for user {user_name}')
            try:
                with open(user_to_json[user_name], 'r') as file:
                    data = json.load(file)
                    # Process and send concert data
                    # This is a placeholder, you need to format the data according to your JSON structure
                    message = "Upcoming concerts:\n"
                    for event in data["artists"]["The Smashing Pumpkins"]["events"]:
                        message += f"{event['datetime_utc']} in {event['venue']['city']}\n"
                    await ctx.send(message)
            except FileNotFoundError:
                await ctx.send("Error: JSON file not found.")
        else:
            await ctx.send(f"No file linked for {user_name}.")

@bot.command(name='99')
async def nine_nine(ctx):
    log.info(f'Someone is asking for a 99 quote...')
    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
    ]

    response = random.choice(brooklyn_99_quotes)
    await ctx.send(response)

@bot.command(name='roll_dice', help='Simulates rolling dice.')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    log.info(f'Someone rolled {number_of_dice} dice with {number_of_sides} sides, got the following dice values: {dice}')
    await ctx.send(', '.join(dice))

@bot.command(name='create-channel')
@commands.has_role('admin')
async def create_channel(ctx, channel_name='real-python'):
    guild = ctx.guild
    existing_channel = discord_utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        print(f'Creating a new channel: {channel_name}')
        await guild.create_text_channel(channel_name)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

# Background task for sending weekly messages
@tasks.loop(hours=168)  # 168 hours in a week
async def weekly_concerts():
    channel_id = CHANNEL 
    channel = bot.get_channel(channel_id)
    if channel is not None:
        for user_name, json_file in user_to_json.items():
            try:
                with open(json_file, 'r') as file:
                    data = json.load(file)
                    message = f"Weekly update for {user_name}:\n"
                    # Modify this part to suit your JSON structure and desired message format
                    for event in data["artists"]["The Smashing Pumpkins"]["events"]:
                        message += f"{event['datetime_utc']} in {event['venue']['city']}\n"
                    await channel.send(message)
            except FileNotFoundError:
                await channel.send(f"Error: JSON file not found for {user_name}.")
    else:
        print("Channel not found.")

# Start the loop when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    weekly_concerts.start()  # Start the scheduled task


if __name__ == '__main__':

    logging.basicConfig(level=logging.info)

    log = logging.getLogger(__name__)

    try:
        bot.run(TOKEN)
    except Exception as error:
        TOKEN = os.environ.get('DISCORD_TOKEN')
        bot.run(TOKEN)