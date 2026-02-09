import yaml
import discord
from discord.ext import commands
from discord import app_commands

CONFIG_PATH = "config.yaml"

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def chunk_text(text: str, limit: int = 3900) -> list[str]:
    text = text.strip()
    if len(text) <= limit:
        return [text]
    parts = []
    current = ""
    for line in text.splitlines():
        if len(current) + len(line) + 1 > limit:
            parts.append(current.rstrip())
            current = ""
        current += line + "\n"
    if current.strip():
        parts.append(current.rstrip())
    return parts

# ==========================
# REGLAS (texto hardcodeado)
# ==========================

RULES_HEADER = (
    "Leé todo antes de participar.\n"
    "Al permanecer en el servidor, aceptás estas reglas.\n"
    "El staff puede actuar para mantener el orden, incluso ante situaciones no contempladas."
)

DISCORD_RULES = (
    "**1)** Respeto ante todo: nada de insultos, acoso, discriminación o provocaciones.\n"
    "**2)** No spam/flood/caps excesivo. No saturar canales.\n"
    "**3)** No publicidad: nada de invitar a otros servidores o promocionar redes sin permiso.\n"
    "**4)** Usá los canales correctamente (no mezclar temas).\n"
    "**5)** No contenido ilegal o +18 explícito. Cuidá el ambiente.\n"
    "**6)** No doxxing: no compartas información personal tuya o de otros.\n"
    "**7)** No suplantación de identidad.\n"
    "**8)** Problemas o reportes: hacelo por ticket o avisá a staff.\n"
    "**9)** El staff tiene la última palabra para mantener la convivencia."
)

COUNTRY_RP_RULES = (
    "**1) Roleplay y coherencia:** respetá el ambiente RP del país.\n"
    "**2) Metagaming (prohibido):** no uses info fuera de rol para actuar en rol.\n"
    "**3) Powergaming (prohibido):** no fuerces acciones imposibles o sin chance de respuesta.\n"
    "**4) FailRP (prohibido):** no rompas la lógica del rol (comportamientos sin sentido IC).\n"
    "**5) Valor a la vida (si aplica):** evitá actuar como si nada tuviera consecuencias.\n"
    "**6) Respeto a jerarquías:** si hay autoridades (gobierno/fuerzas), respetá procedimientos.\n"
    "**7) Conflictos:** discusiones OOC se resuelven con staff, no en público."
)

MINECRAFT_GENERAL = (
    "**1)** No grief: no destruir construcciones ajenas sin permiso.\n"
    "**2)** No cheats/hacks/mods ventajosas (xray, fly, kill aura, etc.).\n"
    "**3)** Bugs/exploits: si encontrás uno, reportalo. Abusarlo = sanción.\n"
    "**4)** Robos/estafas: solo si están permitidos por la normativa del server y con pruebas.\n"
    "**5)** Respeto de propiedad: ciudades, parcelas o casas tienen dueño.\n"
    "**6)** Construcciones: no invadir zonas reclamadas o protegidas.\n"
    "**7)** Staff puede revertir daños si corresponde."
)

ECONOMY_BANK = (
    "**1)** El banco no crea dinero: saldo = depósitos reales o fondos estatales autorizados.\n"
    "**2)** Transferencias válidas solo si quedan registradas por el sistema bancario (si aplica).\n"
    "**3)** Fondos públicos son del Estado: se usan solo con autorización.\n"
    "**4)** Fraudes o abuso del sistema económico = sanción.\n"
    "**5)** Impuestos/multas: si existen, deben respetarse."
)

CRIMES_AND_LAWS = (
    "**1)** Delitos IC (robos, agresiones, amenazas, vandalismo) pueden tener consecuencias IC.\n"
    "**2)** Denuncias/reportes: aportá pruebas cuando sea posible (capturas/video).\n"
    "**3)** Investigaciones: policía/justicia pueden investigar y sancionar IC.\n"
    "**4)** Corrupción estatal: mover fondos públicos sin permiso o sin registro es grave."
)

SANCTIONS = (
    "Las sanciones dependen de gravedad, historial y pruebas:\n\n"
    "• Advertencia\n"
    "• Mute / Jail IC (si aplica)\n"
    "• Kick\n"
    "• Ban temporal\n"
    "• Ban permanente\n\n"
    "**Nota:** El staff puede actuar ante conductas que dañen el servidor aunque no estén listadas."
)

RULE_SECTIONS = [
    ("📜 Reglas de Discord", DISCORD_RULES, discord.Color.blue()),
    ("🇺🇾 Reglas del País (RP)", COUNTRY_RP_RULES, discord.Color.green()),
    ("⛏️ Reglas generales de Minecraft", MINECRAFT_GENERAL, discord.Color.dark_gold()),
    ("🏦 Economía, Banco y Fondos Públicos", ECONOMY_BANK, discord.Color.gold()),
    ("⚖️ Leyes, Delitos y Reportes", CRIMES_AND_LAWS, discord.Color.orange()),
    ("🛑 Sanciones", SANCTIONS, discord.Color.red()),
]

# ==========================
# COG
# ==========================

class reglas(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cfg = load_config()

    async def cog_load(self):
        await self.bot.tree.sync()

    def _reload_cfg(self):
        self.cfg = load_config()

    def _is_admin(self, member: discord.Member) -> bool:
        return member.guild_permissions.administrator

    @app_commands.command(name="reglas_publicar", description="Publica todas las reglas en el canal de reglas.")
    async def reglas_publicar(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("Esto solo funciona en un servidor.", ephemeral=True)

        member = interaction.user
        if not isinstance(member, discord.Member) or not self._is_admin(member):
            return await interaction.response.send_message("❌ No tenés permisos para usar esto.", ephemeral=True)

        self._reload_cfg()
        rules_channel_id = int(self.cfg.get("rules_channel_id", 0))
        channel = guild.get_channel(rules_channel_id)

        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ No encuentro el canal de reglas. Revisá `rules_channel_id` en config.yaml.",
                ephemeral=True
            )

        await interaction.response.send_message(f"✅ Publicando reglas en {channel.mention}...", ephemeral=True)

        header = discord.Embed(
            title="📌 Reglamento Oficial — Uruguay Earth",
            description=RULES_HEADER,
            color=discord.Color.blurple()
        )
        await channel.send(embed=header)

        for title, text, color in RULE_SECTIONS:
            parts = chunk_text(text)
            for i, part in enumerate(parts, start=1):
                t = title if len(parts) == 1 else f"{title} ({i}/{len(parts)})"
                embed = discord.Embed(title=t, description=part, color=color)
                await channel.send(embed=embed)

    @app_commands.command(name="reglas_borrar", description="Borra mensajes del canal de reglas (para republicar limpio).")
    @app_commands.describe(cantidad="Cantidad de mensajes a borrar (máx 100).")
    async def reglas_borrar(self, interaction: discord.Interaction, cantidad: int = 30):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("Esto solo funciona en un servidor.", ephemeral=True)

        member = interaction.user
        if not isinstance(member, discord.Member) or not self._is_admin(member):
            return await interaction.response.send_message("❌ No tenés permisos.", ephemeral=True)

        self._reload_cfg()
        rules_channel_id = int(self.cfg.get("rules_channel_id", 0))
        channel = guild.get_channel(rules_channel_id)

        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ No encuentro el canal de reglas. Revisá `rules_channel_id`.",
                ephemeral=True
            )

        if interaction.channel_id != rules_channel_id:
            return await interaction.response.send_message(
                f"❌ Usá este comando solo en {channel.mention}.",
                ephemeral=True
            )

        cantidad = max(1, min(100, int(cantidad)))

        await interaction.response.send_message("🧹 Limpiando canal de reglas...", ephemeral=True)
        try:
            await channel.purge(limit=cantidad)
        except discord.Forbidden:
            return await interaction.followup.send("❌ No tengo permisos para borrar mensajes en ese canal.", ephemeral=True)

        await interaction.followup.send(f"✅ Borrados {cantidad} mensajes.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(reglas(bot))
