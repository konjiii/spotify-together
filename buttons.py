import sys

from discord import Interaction
from discord.ui import Button

from user import User


class DeviceButton(Button):
    def __init__(self, num: int, device, user: User):
        label = f"{num + 1}. {device['name']} ({device['type']})"
        super().__init__(label=label, row=num)

        self.device_name = device["name"]
        self.device_id = device["id"]
        self.user = user

    # perform device change
    async def callback(self, interaction: Interaction):
        try:
            self.user.update_user(curr_device=self.device_id)
        except Exception as e:
            print(e, file=sys.stderr)
            await interaction.respond("device update failed", ephemeral=True)
            return
        await interaction.respond(
            f"device changed to {self.device_name}", ephemeral=True
        )
