import os

import discord
from dotenv import load_dotenv

from database import init_db, insert_db_user
from user import User, get_users

load_dotenv()
bot = discord.Bot()

init_db()

# dict with all User() instances
users = get_users()


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

    insert_db_user(username, user.client_id, user.client_secret, curr_device)

    await ctx.respond("login successful")


bot.run(os.getenv("DISCORD_TOKEN"))
