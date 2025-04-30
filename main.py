import os
import sys

import discord
from dotenv import load_dotenv

from database import get_db_users, init_db, insert_db_user, update_db_user
from user import User, get_users_dict

load_dotenv()
bot = discord.Bot()

init_db()

# dict with all User() instances
users = get_users_dict()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(
    name="login", description="login with your client_id and client_secret"
)
async def login(
    ctx: discord.ApplicationContext, client_id: str, client_secret: str
) -> None:
    username = ctx.author.name
    user = User(client_id, client_secret, username)
    users[username] = user

    # create new database entry if user is not in database yet
    if get_db_users(username) == []:
        insert_db_user(username)

    # login in browser
    url = user.get_authorize_url()
    await ctx.respond(f"go to: {url}, then run /callback callback_url")


@bot.slash_command(name="callback", description="finish authentication")
async def callback(ctx: discord.ApplicationContext, callback_url: str) -> None:
    user = users.get(ctx.author.name)

    if user is None:
        await ctx.respond("you have not ran /login yet!")
        return

    # save access token in cache
    user.save_access_token(callback_url)

    username = ctx.author.name

    curr_device = user.get_current_device()

    try:
        update_db_user(username, user.client_id, user.client_secret, curr_device)
    except Exception as e:
        print(e, file=sys.stderr)
        await ctx.respond("login failed")
        return

    await ctx.respond("login successful")

    if curr_device is None:
        await ctx.send(
            "did not find active device\nplease run /select_device to choose a device"
        )


bot.run(os.getenv("DISCORD_TOKEN"))
