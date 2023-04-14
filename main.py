import datetime
import json
import os
import random

from discord import Intents
from discord import utils as discord_utils
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = Intents.all()

concert_time = datetime.time(hour=15, minute=30, tzinfo=datetime.timezone.utc)

bot = commands.Bot(command_prefix='!', intents=intents)

@tasks.loop(hours=24)
async def auto_report_concerts():
    print('Would run now')
    pass

@auto_report_concerts.before_loop

@bot.command(name='concert')
async def concert_command(ctx):
    concerts = []
    with open('concerts.json', 'r') as f:
        data = json.load(f)
        for key in data['artists']:
            if data['artists'][key]['meta']['total'] > 0:
                artist = key
                date = data['artists'][key]['events'][0]['datetime_az']
                venue = data['artists'][key]['events'][0]['venue']['name']
                price = data['artists'][key]['events'][0]['stats']['lowest_price_good_deals']
                info = f'{artist} is playing on {date} at {venue} with a good deal price of {price}'
                concerts.append(info)
    message = 'The following concerts are available:'
    for i in concerts:
        message = message + '\n' + i
    await ctx.send(message)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='99')
async def nine_nine(ctx):
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

try:
    bot.run(TOKEN)
except Exception as error:
    TOKEN = os.environ.get('DISCORD_TOKEN')
    bot.run(TOKEN)

auto_report_concerts.start()