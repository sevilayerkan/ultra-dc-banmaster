import discord
from discord.ext import commands
from datetime import datetime
import json

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
SERVER_ID = YOUR_SERVER_ID
BLACKLIST_CHANNEL_ID = YOUR_LOG_CHANNEL_ID
BOT_COMMAND_CHANNEL_ID = YOUR_BOT_COMMAND_CHANNEL_ID
DB_FILE = 'user_db.json'  # JSON file to store user data

blacklist = set()

# Load existing user data from the JSON file
try:
    with open(DB_FILE, 'r') as file:
        user_data = json.load(file)
except FileNotFoundError:
    user_data = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

async def send_dm(member, message):
    try:
        await member.send(message)
    except discord.Forbidden:
        print(f"Failed to send DM to {member.display_name}. They might have DMs disabled.")

async def log_to_channel(channel, message):
    log_channel = bot.get_channel(channel)
    if log_channel:
        await log_channel.send(message)

@bot.event
async def on_member_remove(member):
    if member.guild.id == SERVER_ID:
        leave_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{member.display_name} left the server at {leave_datetime}')

        blacklist.add(member.id)

        await send_dm(member, "Joining the server after leaving is prohibited. Please contact an admin.")

        await log_to_channel(BLACKLIST_CHANNEL_ID, f'{member.display_name} left the server at {leave_datetime}')

        # Update user_data with leave date
        user_data[member.id]['leave_date'] = leave_datetime

        # Save user_data to the JSON file
        with open(DB_FILE, 'w') as file:
            json.dump(user_data, file, indent=4)

        await member.ban(reason="Left the server and attempted to rejoin.")

@bot.event
async def on_member_join(member):
    if member.id in blacklist:
        await send_dm(member, "Joining the server after leaving is prohibited. Please contact an admin.")
        await member.ban(reason="Left the server and attempted to rejoin.")
    else:
        join_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'{member.display_name} joined the server at {join_datetime}')

        await log_to_channel(BLACKLIST_CHANNEL_ID, f'{member.display_name} joined the server at {join_datetime}')

        # Update user_data with join date
        user_data[member.id] = {'join_date': join_datetime}

        # Save user_data to the JSON file
        with open(DB_FILE, 'w') as file:
            json.dump(user_data, file, indent=4)

@bot.command(name='ban')
async def ban_user(ctx, username):
    if ctx.channel.id == BOT_COMMAND_CHANNEL_ID:
        member = discord.utils.get(ctx.guild.members, name=username)

        if member:
            print(f'{ctx.author.display_name} banned {member.display_name}')

            blacklist.add(member.id)

            await send_dm(member, "You have been banned from the server. Please contact an admin for more information.")

            await log_to_channel(BLACKLIST_CHANNEL_ID, f'{ctx.author.display_name} banned {member.display_name}')

            # Update user_data with ban date
            user_data[member.id]['ban_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save user_data to the JSON file
            with open(DB_FILE, 'w') as file:
                json.dump(user_data, file, indent=4)

            await member.ban(reason="Banned by command.")

            await ctx.send(f'{member.display_name} has been banned.')
        else:
            await ctx.send("User not found.")
    else:
        await ctx.send("This command can only be used in the specified command channel.")

bot.run('YOUR_BOT_TOKEN')
