from discord.ext import commands
import discord
import yaml
from datetime import datetime
from discord import app_commands

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

MAP_URL = config["map_url"]
MAP_CHANNEL_ID = config["map_channel_id"]

class Mapa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="mapa",
        description="Te manda el link del mapa del mundo."
    )

    async def mapa(self, interaction: discord.Interaction):

        embed_mapa = discord.Embed(
            title="🗺️ Mapa de todo el mundo (Dextrality Earth)",
            description=f"Abrí el mapa acá: {MAP_URL}",
            color=discord.color.blue()
        )
        embed_mapa.set_footer(text="Actualizado automáticamente • Uruguay Earth")
        embed_mapa.set_thumbnail(url="https://cdn.discordapp.com/attachments/1466266582362624033/1469892450779922656/descarga_2.png?ex=69894f85&is=6987fe05&hm=c9aaf357a20eaebfbf2fafb1f5a88a21fff022a405c947f18ca99ffaac0610ec&")
        embed_mapa.timestamp = datetime.utcnow()
    
        await interaction.response.send_message(embed=embed_mapa, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Mapa(bot))