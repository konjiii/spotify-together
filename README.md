[Read the code base saga here](./STORY.md)
# Spotify together bot guide

## How to Use the App (In Order):

1. **Invite the Discord bot to your server**  
   _For more info, see [To Use This App as a Host, You Additionally Need:](#to-use-this-app-as-a-host-you-additionally-need)_
   - Use commands to control the bot. Type `/` to see all available commands and their descriptions.
   - Use the **Tab** key to auto-complete commands.

2. **Everyone needs to log in:**
   - When the bot is active, log in using the command:  
     ```
     /login <client ID> <client secret>
     ```
   - Follow all instructions the bot provides.

3. **Join a party**  
   Use the command:
   ```
   /join
   ```
   You will only listen together with the people in your party.

4. **Choose a playlist**  
   Use the command:
   ```
   /choose_playlist
   ```
   (Or use the default playlist by not using this command.)  
   - This should be a spotify playlist you and your friends share and can edit while listening together.

5. **Listen to music**  
   Use other commands like:
   ```
   /play_or_pause
   ```
   to control the music player of _**your**_ party.

   - The **queue** has priority over the chosen playlist.

---

## To Use This App as a Normal User, You Need:

- A **Spotify Premium** account  (To obtain a client ID and secret)
- A **Discord** account

---

## To Use This App as a Host, You Additionally Need:

- The **source code** (this GitHub main branch)
- A **Discord bot**
  - Search online: _“how to get a Discord bot token”_
  - Create a bot via the Discord Developer Portal: https://discord.com/developers/applications
  - Store the bot token in a `.env` file:
    ```env
    DISCORD_TOKEN="your_bot_token_here"
    ```
  - Invite the bot to your server:
    - In the Developer Portal, go to **OAuth2 → URL Generator**
    - Under **Scopes**, select: `bot`
    - Under **Bot Permissions**, select: `Administrator`
    - Copy the generated URL, paste it into your browser, and follow the Discord instructions

---

## Getting the Client ID and Client Secret

1. Go to the spotify developer dashboard: https://developer.spotify.com/dashboard/create
2. Log in and create a new app
3. The app name and description can be filled in however you want
4. Set the redirect URI:
   ```
   http://127.0.0.1:9090/callback
   ```
   - Click **Add**

5. Select **Web API**
6. On the next screen, you’ll find your **Client ID** and **Client Secret**  
   _(You’ll need both to log in when using the bot, see [How to Use the App (In Order):](#how-to-use-the-app-in-order))_ 

---
