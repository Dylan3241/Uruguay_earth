import yaml
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

CONFIG_PATH = "config.yaml"

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()

# Canal poryecto
CHANNEL_PROJECTS_ID = int(cfg["channel_projects_id"])

# Rol ciudadano para ping
CITIZEN_ROLE_ID = int(cfg["citizen_role_id"])

# Roles de ministerios (desde tu config.yaml)
def cfg_int(key: str) -> int:
    if key not in cfg:
        raise KeyError(f"Falta la key en config.yaml: {key}")
    return int(cfg[key])

MINISTRY_ROLE_IDS = {
    "security": cfg_int("ministry_security_id"),
    "defense": cfg_int("ministry_defense_id"),
    "interior": cfg_int("ministry_interior_id"),
    "economy": cfg_int("ministry_economy_id"),
    "foreign_relations": cfg_int("ministry_foreign_relations_id"),
    "infrastructure": cfg_int("ministry_infrastructure_id"),
    "agriculture": cfg_int("ministry_agriculture_id"),
    "housing": cfg_int("ministry_housing_id"),
    "transport": cfg_int("ministry_transport_id"),
}

# Orden: más importante -> menos importante
# (key, display_ministry, embed_title, cargo, color)
MINISTRIES = [
    ("security", "👮 Ministerio de seguridad", "👮 Proyecto de seguridad", "Ministro de Seguridad", discord.Color.red()),
    ("defense", "💂 Ministerio de defensa", "💂 Proyecto de defensa", "Ministro de Defensa", discord.Color.dark_red()),
    ("interior", "🏢 Ministerio de Interior", "🏢 Proyecto de Interior", "Ministro del Interior", discord.Color.orange()),
    ("economy", "💰 Ministerio de economia", "💰 Proyecto de economia", "Ministro de Economía", discord.Color.gold()),
    ("foreign_relations", "🤝 Ministerio de relaciones exteriores", "🤝 Proyecto de relaciones exteriores", "Ministro de Relaciones Exteriores", discord.Color.blue()),
    ("infrastructure", "🧱 Ministerio de infraestructura", "🧱 Proyecto de infraestructura", "Ministro de Infraestructura", discord.Color.dark_grey()),
    ("agriculture", "🌽 Ministerio agricola", "🌽 Proyecto agricola", "Ministro de Agricultura", discord.Color.green()),
    ("housing", "🏠 Ministerio de vivienda", "🏠 Proyecto de vivienda", "Ministro de Vivienda", discord.Color.teal()),
    ("transport", "🚚 Ministerio de transporte", "🚚 Proyecto de transporte", "Ministro de Transporte", discord.Color.purple()),
]

MINISTRY_CHOICES = [
    app_commands.Choice(name=display_name, value=key)
    for (key, display_name, _title, _cargo, _color) in MINISTRIES
]

def get_ministry_meta(key: str):
    for k, display_name, title, cargo, color in MINISTRIES:
        if k == key:
            return display_name, title, cargo, color
    return None, None, None, None


class proyectos(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        await self.bot.tree.sync()

    @app_commands.command(name="proyecto", description="Publica un proyecto/anuncio oficial de un ministerio.")
    @app_commands.choices(ministerio=MINISTRY_CHOICES)
    @app_commands.describe(
        ministerio="Elegí el ministerio que publica el proyecto",
        contenido="Texto del proyecto/anuncio"
    )
    async def proyecto(
        self,
        interaction: discord.Interaction,
        ministerio: app_commands.Choice[str],
        contenido: str
    ):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("Esto solo funciona en un servidor.", ephemeral=True)
        
        if interaction.channel_id != CHANNEL_PROJECTS_ID:
            return await interaction.response.send_message(
                "❌ Este comando solo se puede usar en el canal de proyectos.",
                ephemeral=True
            )
        
        member = interaction.user
        if not isinstance(member, discord.Member):
            return await interaction.response.send_message("No pude obtener tu miembro del servidor.", ephemeral=True)

        ministry_key = ministerio.value
        _display_name, title, cargo, color = get_ministry_meta(ministry_key)

        if not title:
            return await interaction.response.send_message("Ministerio inválido.", ephemeral=True)

        ministry_role_id = MINISTRY_ROLE_IDS[ministry_key]
        ministry_role = guild.get_role(ministry_role_id)

        # Permisos: admin o tener el rol del ministerio correspondiente
        is_admin = member.guild_permissions.administrator
        has_ministry_role = bool(ministry_role and ministry_role in member.roles)

        if not (is_admin or has_ministry_role):
            return await interaction.response.send_message(
                "❌ No tenés permisos para publicar proyectos con ese ministerio.",
                ephemeral=True
            )

        citizen_role = guild.get_role(CITIZEN_ROLE_ID)
        if not citizen_role:
            return await interaction.response.send_message(
                "❌ No encuentro el rol ciudadano. Revisá `citizen_role_id` en config.yaml.",
                ephemeral=True
            )

        # Hora local del bot (si querés Uruguay fijo, decime y lo pongo con pytz/zoneinfo)
        now = datetime.now()
        hhmm = now.strftime("%H:%M")

        embed = discord.Embed(
            title=title,
            description=contenido,
            color=color
        )

        # Footer: hora + user + cargo
        embed.set_footer(text=f"{hhmm} • {member.name} • {cargo}")

        # Publica con ping al ciudadano
        await interaction.response.send_message(
            content=citizen_role.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(proyectos(bot))
