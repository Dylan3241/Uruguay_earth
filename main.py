import discord
import os
import json
import yaml
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from datetime import datetime

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

MAP_URL = config["map_url"]
MAP_CHANNEL_ID = config["map_channel_id"]

STATE_PATH = "data/state.json"

def load_state():
    if not os.path.exists(STATE_PATH):
        return{}

    with open (STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

class UruguayEarth(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            application_id = 1323534255032238152
        )


    async def setup_hook(self):
        #from database.database import create_tables
        #create_tables()
        
        await bot.load_extension("cogs.leyes")
        await bot.load_extension("cogs.bienvenida")
        await bot.load_extension("cogs.banco_info")
        await bot.load_extension("cogs.banco_tickets")
        await self.load_extension("cogs.proyectos")
        await self.load_extension("cogs.tickets")
        await self.load_extension("cogs.alianzas")
        await self.load_extension("cogs.enemigos")
        await self.load_extension("cogs.mapa")

        state = load_state()
        msg_id = state.get("map_message_id")

        canal = self.get_channel(MAP_CHANNEL_ID)
        if canal is None:
            canal = await self.fetch_channel(MAP_CHANNEL_ID)

        embed_mapa = discord.Embed(
            
            title="🗺️ Mapa de todo el mundo (Dextrality Earth)",
            description=f"Abrí el mapa acá: {MAP_URL}",
            color=discord.Color.blue() 
        )
        embed_mapa.set_footer(text="Actualizado automáticamente • Uruguay Earth")
        embed_mapa.set_thumbnail(url="https://cdn.discordapp.com/attachments/1466266582362624033/1469892450779922656/descarga_2.png?ex=69894f85&is=6987fe05&hm=c9aaf357a20eaebfbf2fafb1f5a88a21fff022a405c947f18ca99ffaac0610ec&")
        embed_mapa.timestamp = datetime.utcnow()

        
        if msg_id:
            try:
                msg = await canal.fetch_message(msg_id)
                await msg.edit(embed=embed_mapa)
                return
            except discord.NotFound:
                pass  # se borró, crea uno nuevo

        msg = await canal.send(embed=embed_mapa)
        state["map_message_id"] = msg.id
        save_state(state)

        print("Bot cargado correctamente")

bot = UruguayEarth()

@bot.event
async def on_ready():
    print(f"Bot iniciado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands sincronizados: {len(synced)}")

    except Exception as e:
        print(f"Error al sincronizar: {e}")

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)

