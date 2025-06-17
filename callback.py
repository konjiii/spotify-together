import sys

import discord
from discord.ui import Button, InputText, Modal, View


# send modal (a from) to privately send your callbacklink
class CallbackModal(Modal):
    # The modal itself
    def __init__(self, user):
        super().__init__(title="Paste Spotify Callback URL")
        self.user = user
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
            self.user.update_user(
                self.user.client_id, self.user.client_secret, curr_device
            )
        except Exception as e:
            print(e, file=sys.stderr)
            await interaction.response.send_message(
                "❌ Failed to update user info.", ephemeral=True
            )
            return

        await interaction.response.send_message("✅ Login successful!", ephemeral=True)

        if curr_device is None:
            await interaction.followup.send(
                "⚠️ No active device found. Run `/select_device` to pick one.",
                ephemeral=True,
            )


# send modal after buttonpress
class CallbackView(View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.user = user

    @discord.ui.button(label="Paste Callback URL", style=discord.ButtonStyle.primary)
    async def open_modal(self, button: Button, interaction: discord.Interaction):
        await interaction.response.send_modal(CallbackModal(self.user))
