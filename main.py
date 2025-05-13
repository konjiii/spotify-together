import os
import sys

import discord
from dotenv import load_dotenv

from database import get_db_users, init_db, insert_db_user
from user import User, get_users_dict
from musicplayer import MusicPlayer

# for shutdown
import asyncio
from contextlib import suppress

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


@bot.slash_command(name="shutdown", description="To close the bot")
async def shutdown(ctx):
    app_info = await bot.application_info()
    if ctx.author.id != app_info.owner.id:
        await ctx.respond("❌ Only the owner can shut me down.")
        return

    await ctx.respond("Shutting down... 👋")

    # Cancel the rest
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
    # afterwards close the bot
    await bot.close()


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
    user = User(username, client_id, client_secret)
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
        user.update_user(user.client_id, user.client_secret , curr_device)
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
        device_list += f"{i+1}. {device["name"]} ({device["type"]})\n"

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
    user = users[username]
    try:
        user.update_user(username, curr_device=device)
    except Exception as e:
        print(e, file=sys.stderr)
        await ctx.respond("device update failed", ephemeral=True)
        return
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
    , makes party when it doesn't exist yet
    params:
        name: str
    """
    username = ctx.author.name
    if username in user_to_party: # check if username is a key in the user_to_party_dict
        await leave_party(ctx) # make the user leave the party
    
    try:
        parties[name].add_user(users[username]) # add user to music player party
        parties[name].add_ctx(username,ctx)
    except: # make party if it doesn't exist yet 
        await create_party(ctx,name)
        parties[name].add_user(users[username]) # add user to music player party
        parties[name].add_ctx(username,ctx)

    user_to_party[username] = name
    await ctx.respond(f"user {username} added to party {name}")
    

@bot.slash_command(name="leave_party", description="remove user from party")
async def leave_party(ctx: discord.ApplicationContext) -> None:
    """
    remove user that calls this function from the party
    
    """
    username = ctx.author.name
    if username in user_to_party:
        party_name = user_to_party[username]
        user_to_party.pop(username)
        try:
            parties[party_name].remove_user(username) # add user to music player party
            parties[party_name].remove_ctx(username)
            await ctx.respond(f"user {username} removed from party {party_name}")
        except Exception as e:
            print(e, file=sys.stderr)
    else:
        await ctx.respond(f"user {username} is not in any party")
    
    
@bot.slash_command(name="current_party", description="show what party you are in")
async def current_party(ctx: discord.ApplicationContext) -> None:
    """
    let the bot say the users current party, or that the user is not in any party

    """
    username = ctx.author.name
    if username in user_to_party:
        party_name = user_to_party[username]
        await ctx.respond(f"user {username} is in party {party_name}")
    else:
        await ctx.respond(f"user {username} is not in any party")
    

@bot.slash_command(name="choose_playlist", description="choose a playlist for your party")
async def choose_playlist(ctx: discord.ApplicationContext, url: str) -> None:
    """
    remove user that calls this function from the party
    params:
        url: str
    """
    username = ctx.author.name
    if username in user_to_party:
        party_name = user_to_party[username]
        try:
            parties[party_name].choose_playlist(url) # add user to music player party
        except Exception as e:
            print(e, file=sys.stderr)
            await ctx.respond("No playlist found")
        await ctx.respond(f"user {username} changed the playlist of {party_name}")
    else: # make party if it doesn't exist yet 
        await ctx.respond(f"user {username} is not in any party")
   
async def q_and_a(ctx: discord.ApplicationContext ,question: str, timeout: float | None = None) -> str:
    """
    equivalent of input() function but for the discord bot
    params:
        question: str
    """
    username = ctx.author.name
    await ctx.respond(question, ephemeral=True)
    # await response from user
    try:
        reply_message = await bot.wait_for('message', check=(lambda message: message.author.name == username), timeout=timeout)
    except Exception as e:
        print(e, file=sys.stderr)
        await ctx.respond("response took too long", ephemeral=True)
        return
    # retrieve response message contents
    message = await ctx.fetch_message(reply_message.id)
    query = message.content
    return query

@bot.slash_command(name="current_queue", description="show what queue your party has")
async def current_queue(ctx: discord.ApplicationContext) -> None:
    """
    show the partys' current queue, or that the user is not in any party

    """
    username = ctx.author.name
    user = users[username]
    if username in user_to_party:
        party_name = user_to_party[username]
        music_player = parties[party_name]
        q = music_player.queue # get queue variable
        mes = "\n"
        for i in range(len(q)):
            track_info = user.sp.track(q[i])
            # Extract name and artist
            song_name = track_info["name"]
            artist_name = track_info["artists"][0]["name"]
            mes+=f"{i+1}. {song_name} by {artist_name}\n"
        await ctx.respond(f"The queue of party {party_name}:{mes}")
    else:
        await ctx.respond(f"user {username} is not in any party")
    

@bot.slash_command(name="add_to_queue", description="add a song to your partys queue")
async def add_to_queue(ctx: discord.ApplicationContext) -> None:
    """
    search song and add to queue
    """
    username = ctx.author.name
    user = users[username]
    if username in user_to_party:
        party_name = user_to_party[username]
        # add to queue function was previously in music player
        # is now translated to here:
        searching = True
        dont_cancel_adding = True
        while searching:
            query = await q_and_a(ctx, "What song would you like to add to the queue?")
            if query == "s": #stop searching
                not_valid_answer = False
                searching = False
                dont_cancel_adding = False
            try:
                results = user.sp.search(query)
            except Exception as e:
                print(e, file=sys.stderr)
                await ctx.respond("login again", ephemeral=True)
                return
            if results is None: # not track found
                await ctx.respond("track not found", ephemeral=True)
                continue
            tracks = results["tracks"]["items"]
            # show found results
            track_des = "#############\nSongs found:\n"
            for i,track in enumerate(tracks):
                track_des+= f"{i}. {track['name']} from {track['album']['artists'][0]['name']}\n"
            await ctx.respond(track_des, ephemeral=True)
            # choose one of the results
            not_valid_answer = True
            while not_valid_answer:
                query = await q_and_a(ctx, f"################\n\nAdd: {tracks[0]['name']} from {tracks[0]['album']['artists'][0]['name']}, to queue?\n-----------------\n 'y': yes\ntype a number: the search result number\n'n': search again\n's': stop searching\n-----------------")
                if query == "y":
                    idx = 0
                    not_valid_answer = False
                    searching = False
                else:
                    try:
                        idx = int(query)-1
                        if 0 <= idx < len(tracks):
                            not_valid_answer = False
                            searching = False
                    except:
                        if query == "n":
                            not_valid_answer = False
                        elif query == "s":
                            not_valid_answer = False
                            searching = False
                            dont_cancel_adding = False
                        else: 
                            await ctx.respond(f"{query} is not a valid answer", ephemeral=True)
        if dont_cancel_adding:
            chosen_track = tracks[idx]["uri"]
            try:
                parties[party_name].add_to_queue_bot(chosen_track)
            except Exception as e:
                print(e, file=sys.stderr)
            await ctx.respond(f"{tracks[idx]['name']} from {tracks[idx]['album']['artists'][0]['name']} added to the queue.")
    else:
        await ctx.respond(f"user {username} is not in any party")


@bot.slash_command(name="play_or_pause", description="press or pause for your party")
async def play_or_pause(ctx: discord.ApplicationContext) -> None:
    """
    pause or start playing the musicplayer of the party, or say that the user is not in any party

    """
    username = ctx.author.name
    if username in user_to_party:
        party_name = user_to_party[username]
        parties[party_name].play_or_pause()
        await ctx.respond("👍", ephemeral=True)
    else:
        await ctx.respond(f"user {username} is not in any party")

bot.run(os.getenv("DISCORD_TOKEN"))

