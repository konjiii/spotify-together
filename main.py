# for shutdown
import asyncio
import os
import sys
from contextlib import suppress

import discord
from discord.ui import Button, InputText, Modal, View
from dotenv import load_dotenv

from buttons import DeviceButton
from database import get_db_users, init_db, insert_db_user
from musicplayer import MusicPlayer
from user import User, get_users_dict

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


# this is for /login
# send modal (a from) to privately send your callbacklink
class CallbackModal(Modal):
    # The modal itself
    def __init__(self, user, ctx):
        super().__init__(title="Paste Spotify Callback URL")
        self.user = user
        self.ctx = ctx
        self.input = InputText(
            label="Callback URL",
            placeholder="Visit: the url, then paste the full redirected URL here.",
            style=discord.InputTextStyle.long,
        )
        self.add_item(self.input)

    # what happens after the modal
    async def callback(self, interaction: discord.Interaction):
        callback_url = (self.input.value or "").strip()

        if not self.user:
            await interaction.response.send_message(
                "You have not run /login yet!", ephemeral=True
            )
            return

        try:
            self.user.save_access_token(callback_url)
        except Exception as e:
            print(e, file=sys.stderr)
            await interaction.response.send_message(
                "❌ Login failed: invalid callback URL", ephemeral=True
            )
            return

        curr_device = self.user.get_current_device()
        try:
            self.user.update_user( curr_device=curr_device )
        except Exception as e:
            print(e, file=sys.stderr)
            await interaction.response.send_message(
                "❌ Failed to update user info.", ephemeral=True
            )
            return

        await interaction.response.send_message("✅ Login successful!", ephemeral=True)

        if curr_device is None:
            await interaction.followup.send(
                "🦍🦧 No active device found. Choose one below or run `/select_device` to pick one.",
                ephemeral=True,
            )
            await select_device(self.ctx)

# send modal after buttonpress
class CallbackView(View):
    def __init__(self, user, ctx):
        super().__init__(timeout=300)
        self.user = user
        self.ctx =ctx

    @discord.ui.button(label="Paste Callback URL", style=discord.ButtonStyle.primary)
    async def open_modal(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_modal(CallbackModal(self.user,self.ctx))


@bot.slash_command(
    name="login", description="Login with your client_id and client_secret"
)
async def login(
    ctx: discord.ApplicationContext,
    client_id: str | None = None,
    client_secret: str | None = None,
):
    username = ctx.author.name

    # Validate user setup
    if client_id is None or client_secret is None:
        user = users.get(username)
        if user is None or user.client_id is None or user.client_secret is None:
            await ctx.respond(
                "Please provide both client_id and client_secret.", ephemeral=True
            )
            return
    else:
        user = User(username, client_id, client_secret)
        users[username] = user

    # DB init if needed
    if get_db_users(username) == []:
        insert_db_user(username,client_id,client_secret)

    # Get Spotify URL
    url = user.get_authorize_url()

    # Send instruction + button
    view = CallbackView(user,ctx)
    await ctx.respond(
        f"1. To log in:\n1. [Click here to log in to Spotify]({url})\n"
        "2. After the page refreshes, **copy the full URL** from your browser.\n"
        "3. Click the button below and paste the into the form.",
        view=view,
        ephemeral=True,
    )


@bot.slash_command(
    name="select_device", description="select a device to use to control with the bot"
)
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

    user = users[username]

    # create device selection buttons
    device_view = discord.ui.View()
    for i, device in enumerate(available_devices):
        device_button = DeviceButton(num=i, device=device, user=user)
        device_view.add_item(device_button)

    await ctx.respond(
        "please select a device from below:", view=device_view, ephemeral=True
    )


@bot.slash_command(
    name="create_party",
    description="make a spotify listening party that users can join",
)
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
    if (
        username in user_to_party
    ):  # check if username is a key in the user_to_party_dict
        await leave_party(ctx)  # make the user leave the party

    try:
        parties[name].add_user(users[username])  # add user to music player party
        parties[name].add_ctx(username, ctx)
    except:  # make party if it doesn't exist yet
        await create_party(ctx, name)
        parties[name].add_user(users[username])  # add user to music player party
        parties[name].add_ctx(username, ctx)

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
            parties[party_name].remove_user(username)  # add user to music player party
            parties[party_name].remove_ctx(username)
            await ctx.respond(f"user {username} removed from party {party_name}")
        except Exception as e:
            print(e, file=sys.stderr)

        if party_name not in user_to_party.values():
            # party is empty so remove it
            del parties[party_name]
            await ctx.respond(f"party {party_name} is empty so was removed")
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


@bot.slash_command(
    name="choose_playlist", description="choose a playlist for your party"
)
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
            parties[party_name].choose_playlist(url)  # add user to music player party
        except Exception as e:
            print(e, file=sys.stderr)
            await ctx.respond("No playlist found")
        await ctx.respond(f"user {username} changed the playlist of {party_name}")
    else:  # make party if it doesn't exist yet
        await ctx.respond(f"user {username} is not in any party")


async def q_and_a(
    ctx: discord.ApplicationContext, question: str, timeout: float | None = None
) -> str:
    """
    equivalent of input() function but for the discord bot
    params:
        question: str
    """
    username = ctx.author.name
    await ctx.respond(question, ephemeral=True)
    # await response from user
    try:
        reply_message = await bot.wait_for(
            "message",
            check=(lambda message: message.author.name == username),
            timeout=timeout,
        )
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
        q = music_player.queue  # get queue variable
        mes = "\n"
        for i in range(len(q)):
            track_info = user.sp.track(q[i])
            # Extract name and artist
            song_name = track_info["name"]
            artist_name = track_info["artists"][0]["name"]
            mes += f"{i + 1}. {song_name} by {artist_name}\n"
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
            if query == "s":  # stop searching
                not_valid_answer = False
                searching = False
                dont_cancel_adding = False
            try:
                results = user.sp.search(query)
            except Exception as e:
                print(e, file=sys.stderr)
                await ctx.respond("login again", ephemeral=True)
                return
            if results is None:  # not track found
                await ctx.respond("track not found", ephemeral=True)
                continue
            tracks = results["tracks"]["items"]
            # show found results
            track_des = "#############\nSongs found:\n"
            for i, track in enumerate(tracks):
                track_des += f"{i}. {track['name']} from {track['album']['artists'][0]['name']}\n"
            await ctx.respond(track_des, ephemeral=True)
            # choose one of the results
            not_valid_answer = True
            while not_valid_answer:
                query = await q_and_a(
                    ctx,
                    f"################\n\nAdd: {tracks[0]['name']} from {tracks[0]['album']['artists'][0]['name']}, to queue?\n-----------------\n 'y': yes\ntype a number: the search result number\n'n': search again\n's': stop searching\n-----------------",
                )
                if query == "y":
                    idx = 0
                    not_valid_answer = False
                    searching = False
                else:
                    try:
                        idx = int(query) - 1
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
                            await ctx.respond(
                                f"{query} is not a valid answer", ephemeral=True
                            )
        if dont_cancel_adding:
            chosen_track = tracks[idx]["uri"]
            try:
                parties[party_name].add_to_queue_bot(chosen_track)
            except Exception as e:
                print(e, file=sys.stderr)
            await ctx.respond(
                f"{tracks[idx]['name']} from {tracks[idx]['album']['artists'][0]['name']} added to the queue."
            )
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


@bot.slash_command(name="skip", description="skip song for your party")
async def skip(ctx: discord.ApplicationContext) -> None:
    """
    skip song in the musicplayer of the party, or say that the user is not in any party

    """
    username = ctx.author.name
    if username in user_to_party:
        party_name = user_to_party[username]
        parties[party_name].skip()
        await ctx.respond("👍", ephemeral=True)
    else:
        await ctx.respond(f"user {username} is not in any party")


@bot.slash_command(name="back", description="back song for your party")
async def back(ctx: discord.ApplicationContext) -> None:
    """
    back song in the musicplayer of the party, or say that the user is not in any party

    """
    username = ctx.author.name
    if username in user_to_party:
        party_name = user_to_party[username]
        parties[party_name].previous_or_beginning()
        await ctx.respond("👍", ephemeral=True)
    else:
        await ctx.respond(f"user {username} is not in any party")


bot.run(os.getenv("DISCORD_TOKEN"))
