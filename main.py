import os

import discord
from dotenv import load_dotenv

from database import execute_insert, init_db
from user import User

load_dotenv()
bot = discord.Bot()

init_db()

# list with all User() instances
users = dict()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(
    name="login", description="login with your client_id and client_secret"
)
async def login(
    ctx: discord.ApplicationContext, client_id: str, client_secret: str
) -> None:
    user = User(client_id, client_secret)
    users[ctx.author.name] = user

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

    # add user to database
    insert_query = """
        INSERT INTO users
        (id, client_id, client_secret, current_device)
        VALUES
        (?, ?, ?, ?)
    """

    username = ctx.author.name

    execute_insert(insert_query, (username, user.client_id, user.client_secret, ""))

    await ctx.respond("login successful")


bot.run(os.getenv("DISCORD_TOKEN"))
