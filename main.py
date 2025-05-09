import os
import sys

import discord
from dotenv import load_dotenv

from database import get_db_users, init_db, insert_db_user, update_db_user
from user import User, get_users_dict
from musicplayer import MusicPlayer

load_dotenv()
bot = discord.Bot()

init_db()

# dict with all User() instances
users = get_users_dict()

# dict with username -> party name
user_to_party = dict()
# dict with party name -> musicplayer instance
parties = dict()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(
    name="login", description="login with your client_id and client_secret"
)
async def login(
    ctx: discord.ApplicationContext, client_id: str, client_secret: str
) -> None:
    """
    return a login link the user can use to login

    params:
        client_id: str,
        client_secret: str,
    """
    username = ctx.author.name
    user = User(client_id, client_secret, username)
    users[username] = user

    # create new database entry if user is not in database yet
    if get_db_users(username) == []:
        insert_db_user(username)

    # login in browser
    url = user.get_authorize_url()
    await ctx.respond(f"go to: {url}, then run /callback callback_url", ephemeral=True)


@bot.slash_command(name="callback", description="finish authentication")
async def callback(ctx: discord.ApplicationContext, callback_url: str) -> None:
    """
    get and save access token using the callback url the user gives

    params:
        callback_url: str
    """
    user = users.get(ctx.author.name)

    if user is None:
        await ctx.respond("you have not ran /login yet!", ephemeral=True)
        return

    try:
        # save access token in cache
        user.save_access_token(callback_url)
    except Exception as e:
        print(e, file=sys.stderr)
        await ctx.respond("login failed: invalid callback link", ephemeral=True)
        return

    username = ctx.author.name

    curr_device = user.get_current_device()

    try:
        update_db_user(username, user.client_id, user.client_secret, curr_device)
    except Exception as e:
        print(e, file=sys.stderr)
        await ctx.respond("login failed", ephemeral=True)
        return

    await ctx.respond("login successful", ephemeral=True)

    if curr_device is None:
        await ctx.respond(
            "did not find active device\nplease run /select_device to choose a device",
            ephemeral=True
        )

@bot.slash_command(name="select_device", description="select a device to use to control with the bot")
async def select_device(ctx: discord.ApplicationContext) -> None:
    """
    choose a device to control with the bot
    if device_id is given select that device to control, show available devices otherwise
    
    params:
        device_id: Opt<str>
    """
    username = ctx.author.name
    available_devices = users[username].sp.devices()["devices"]
    if len(available_devices) == 0:
        await ctx.respond("no available devices found", ephemeral=True)
        return
    
    # create device selection prompt
    device_list = "please select a device from below (send the number in chat):\n"
    for i, device in enumerate(available_devices):
        device_list += f"{i+1}. {device['name']} ({device['type']})\n"

    await ctx.respond(device_list)

    # await response from user
    try:
        reply_message = await bot.wait_for('message', check=(lambda message: message.author.name == username), timeout=10.0)
    except Exception as e:
        print(e, file=sys.stderr)
        await ctx.respond("response took too long", ephemeral=True)
        return
    
    # retrieve response message contents
    message = await ctx.fetch_message(reply_message.id)
    content = message.content

    # incorrect input handling
    if not content.isnumeric():
        print(f"response not numeric: {content}", sys.stderr)
        await ctx.send("invalid response", reference=reply_message)
        return

    device_num = int(content) - 1
    if not 0 <= device_num < len(available_devices):
        print(f"response index out of range: {device_num}", sys.stderr)
        await ctx.send("invalid response", reference=reply_message)
        return
    
    # perform device change
    device = available_devices[device_num]["id"]
    update_db_user(username, curr_device=device)
    await ctx.send(f"device changed to {available_devices[device_num]["name"]}", reference=reply_message)


@bot.slash_command(name="create_party", description="make a spotify listening party that users can join")
async def create_party(ctx: discord.ApplicationContext, name: str) -> None:
    """
    make a spotify listening party that users can join

    params:
        name: str
    """
    party = MusicPlayer()
    parties[name] = party

    await ctx.respond(f"created party: {name}")

@bot.slash_command(name="join_party", description="add user to party")
async def join_party(ctx: discord.ApplicationContext, name: str) -> None:
    """
    add user that calls this function to a party with name 'name'
    
    params:
        name: str
    """
    username = ctx.author.name
    parties[name].add_user(username, users[username])
    user_to_party[username] = name

    await ctx.respond(f"user {username} added to party {name}")


bot.run(os.getenv("DISCORD_TOKEN"))
