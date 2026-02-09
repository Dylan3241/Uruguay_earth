import yaml
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

CONFIG_PATH = "config.yaml"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()

CITIZEN_ROLE_ID = int(cfg["citizen_role_id"])

MINISTRIES = [
    ("security","👮 Ministerio de seguridad","Ministro de Seguridad",discord.Color.red()),
    ("defense","💂 Ministerio de defensa","Ministro de Defensa",discord.Color.dark_red()),
    ("interior","🏢 Ministerio del Interior","Ministro del Interior",discord.Color.orange()),
    ("economy","💰 Ministerio de economia","Ministro de Economia",discord.Color.gold()),
    ("foreign_relations","🤝 Ministerio de relaciones exteriores","Ministro de Relaciones Exteriores",discord.Color.blue()),
    ("infrastructure","🧱 Ministerio de infraestructura","Ministro de Infraestructura",discord.Color.dark_grey()),
    ("agriculture","🌽 Ministerio agricola","Ministro de Agricultura",discord.Color.green()),
    ("housing","🏠 Ministerio de vivienda","Ministro de Vivienda",discord.Color.teal()),
    ("transport","🚚 Ministerio de transporte","Ministro de Transporte",discord.Color.purple()),
]

ROLE_IDS = {
    k: int(cfg[f"ministry_{k}_id"]) for k,_,_,_ in MINISTRIES
}

CHANNEL_IDS = {
    k: int(cfg[f"channel_{k}_id"]) for k,_,_,_ in MINISTRIES
}

CHOICES = [
    app_commands.Choice(name=name,value=k)
    for k,name,_,_ in MINISTRIES
]

def meta(key):
    for k,name,cargo,color in MINISTRIES:
        if k==key:
            return name,cargo,color
    return None,None,None


class departamentos(commands.Cog):
    def __init__(self,bot):
        self.bot=bot

    async def cog_load(self):
        await self.bot.tree.sync()

    @app_commands.command(name="anuncio",description="Publica un anuncio oficial del ministerio.")
    @app_commands.choices(ministerio=CHOICES)
    async def anuncio(self,interaction:discord.Interaction,ministerio:app_commands.Choice[str],contenido:str):

        guild=interaction.guild
        member=interaction.user

        key=ministerio.value
        name,cargo,color=meta(key)

        role=guild.get_role(ROLE_IDS[key])
        channel=guild.get_channel(CHANNEL_IDS[key])
        citizen=guild.get_role(CITIZEN_ROLE_ID)

        if not role or role not in member.roles and not member.guild_permissions.administrator:
            return await interaction.response.send_message("❌ No sos ministro de ese departamento.",ephemeral=True)

        if not isinstance(channel,discord.TextChannel):
            return await interaction.response.send_message("❌ Canal del ministerio no encontrado.",ephemeral=True)

        now=datetime.now().strftime("%H:%M")

        embed=discord.Embed(
            title=f"{name}",
            description=contenido,
            color=color
        )

        embed.set_footer(text=f"{now} • {member.name} • {cargo}")

        await channel.send(
            content=citizen.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

        await interaction.response.send_message(f"✅ Anuncio enviado en {channel.mention}",ephemeral=True)


async def setup(bot):
    await bot.add_cog(departamentos(bot))
