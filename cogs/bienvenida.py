import yaml
import discord
from discord.ext import commands

CONFIG_PATH = "config.yaml"

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()

WELCOME_CHANNEL_ID = int(cfg["welcome_channel_id"])
FAREWELL_CHANNEL_ID = int(cfg["farewell_channel_id"])
RULES_CHANNEL_ID = int(cfg["rules_channel_id"])
AUTO_ROLE_IDS = cfg.get("auto_roles_on_join", [])  # lista

class bienvenida(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        # No asignar roles a bots (opcional, pero recomendado)
        if member.bot:
            channel = guild.get_channel(WELCOME_CHANNEL_ID)
            if isinstance(channel, discord.TextChannel):
                await channel.send(f"🤖 {member.mention} (bot) se unió al servidor.")
            return

        # 1) Autoroles
        roles_added = []
        for role_id in AUTO_ROLE_IDS:
            role = guild.get_role(int(role_id))
            if role:
                try:
                    await member.add_roles(role, reason="Autoroles al ingresar")
                    roles_added.append(role)
                except:
                    pass

        # 2) Mensaje de bienvenida
        channel = guild.get_channel(WELCOME_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            embed = discord.Embed(             
                title="🇺🇾 ¡Bienvenido a Uruguay Earth!",
                description=(
                    f"{member.mention} llegó al país.\n\n"
                    "**Primeros pasos:**\n"
                    f"• Leé las reglas en {RULES_CHANNEL_ID} 📜\n"
                    "• Registrate como ciudadano 🪪\n"
                    "• Abrí una cuenta en el banco 🏦\n\n"
                    "¡Disfrutá el roleplay!"
                ),
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Ciudadanos en el servidor: {guild.member_count}")

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        channel = guild.get_channel(FAREWELL_CHANNEL_ID)

        if isinstance(channel, discord.TextChannel):
            embed = discord.Embed(
                title="👋 Un ciudadano abandonó el país",
                description=f"**{member.name}** ya no forma parte del servidor.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Ciudadanos restantes: {guild.member_count}")
            await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(bienvenida(bot))
