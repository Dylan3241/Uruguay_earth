import yaml
import discord
from discord.ext import commands

CONFIG_PATH = "config.yaml"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()

TICKETS_CATEGORY_BANK_ID = int(cfg["tickets_category_bank_id"])
SUPPORT_ROLE_ID = int(cfg["support_role_id"])
BANK_PANEL_CHANNEL_ID = int(cfg["bank_panel_channel_id"])

class BancoTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir cuenta bancaria",
        emoji="🏦",
        style=discord.ButtonStyle.primary,
        custom_id="bank:open_account"
    )
    async def open_account(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        category = guild.get_channel(TICKETS_CATEGORY_BANK_ID)
        role = guild.get_role(SUPPORT_ROLE_ID)

        # Verificar si ya tiene ticket
        for ch in category.text_channels:
            if ch.topic == str(interaction.user.id):
                return await interaction.response.send_message(
                    "Ya tenés un trámite bancario abierto.",
                    ephemeral=True
                )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            role: discord.PermissionOverwrite(view_channel=True),
        }

        channel = await guild.create_text_channel(
            name=f"banco-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
            topic=str(interaction.user.id)
        )

        embed = discord.Embed(
            title="🏦 Registro de Cuenta Bancaria",
            description=(
                "Bienvenido al sistema bancario.\n\n"
                "Por favor complete:\n"
                "• Nombre IC\n"
                "• Número de ciudadano\n"
                "• Ocupación\n"
                "• Motivo de apertura"
            ),
            color=discord.Color.gold()
        )

        await channel.send(
            f"{interaction.user.mention} {role.mention}",
            embed=embed
        )

        await interaction.response.send_message(
            f"Cuenta en proceso: {channel.mention}",
            ephemeral=True
        )

class banco_tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def panelbanco(self, ctx):

        embed = discord.Embed(
            title="🏦 Registro Bancario",
            description=(
                "Panel oficial del Banco Nacional.\n\n"
                "Presiona el botón para iniciar el trámite de apertura de cuenta."
            ),
            color=discord.Color.gold()
        )

        await ctx.send(embed=embed, view=BancoTicketView())

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(BancoTicketView())

async def setup(bot):
    await bot.add_cog(banco_tickets(bot))
