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

CHANNEL_BANK_INFO_ID = int(cfg["channel_bank_info_id"])
CHANNEL_BANK_LOGS_ID = int(cfg["channel_bank_logs_id"])
CHANNEL_BANK_PUBLIC_FUNDS_ID = int(cfg["channel_bank_public_funds_id"])
CHANNEL_BANK_MECHANICS_ID = int(cfg["channel_bank_mechanics_id"])

BANK_STAFF_ROLE_ID = int(cfg["bank_staff_role_id"])

class banco_info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        await self.bot.tree.sync()

    @app_commands.command(name="banco_info", description="Publica la información oficial del banco (en sus canales).")
    async def banco_info_cmd(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("Esto solo funciona en un servidor.", ephemeral=True)

        member = interaction.user
        if not isinstance(member, discord.Member):
            return await interaction.response.send_message("No pude obtener tu miembro del servidor.", ephemeral=True)

        bank_staff_role = guild.get_role(BANK_STAFF_ROLE_ID)
        is_staff = bool(bank_staff_role and bank_staff_role in member.roles)
        is_admin = member.guild_permissions.administrator

        if not (is_staff or is_admin):
            return await interaction.response.send_message("❌ No tenés permisos para usar esto.", ephemeral=True)

        ch_info = guild.get_channel(CHANNEL_BANK_INFO_ID)
        ch_public = guild.get_channel(CHANNEL_BANK_PUBLIC_FUNDS_ID)
        ch_mech = guild.get_channel(CHANNEL_BANK_MECHANICS_ID)
        ch_logs = guild.get_channel(CHANNEL_BANK_LOGS_ID)

        if not isinstance(ch_info, discord.TextChannel):
            return await interaction.response.send_message("❌ No encuentro channel_bank_info_id.", ephemeral=True)
        if not isinstance(ch_public, discord.TextChannel):
            return await interaction.response.send_message("❌ No encuentro channel_bank_public_funds_id.", ephemeral=True)
        if not isinstance(ch_mech, discord.TextChannel):
            return await interaction.response.send_message("❌ No encuentro channel_bank_mechanics_id.", ephemeral=True)
        if not isinstance(ch_logs, discord.TextChannel):
            ch_logs = None  # no cortamos si logs no existe

        now = datetime.now()
        hhmm = now.strftime("%H:%M")

        # 1) INFO (canal info)
        e_info = discord.Embed(
            title="🏦 Banco Nacional — Información oficial",
            description=(
                "El Banco Nacional administra el sistema financiero del país dentro del servidor y garantiza un orden económico.\n\n"
                "**Funciones principales:**\n"
                "• Apertura y administración de **cuentas bancarias**\n"
                "• Registro de **depósitos, retiros y transferencias**\n"
                "• Protección de ahorros (evita pérdidas por robos/muerte en juego)\n"
                "• Control de **fondos públicos** y pagos del Estado\n"
                "• Transparencia: toda operación queda registrada por el banco\n\n"
                "**Regla base:** El banco **no inventa dinero**. El saldo solo existe si hay depósitos reales o fondos estatales autorizados."
            ),
            color=discord.Color.gold()
        )
        e_info.set_footer(text=f"{hhmm} • Banco Nacional")

        # 2) PROCEDIMIENTO (lo incluimos en el canal info también para que quede junto)
        e_proc = discord.Embed(
            title="📋 Procedimiento Bancario — Cómo se hacen los trámites",
            description=(
                "Para mantener el rol y la transparencia, todos los trámites se realizan por ticket en **Registro Bancario**.\n\n"
                "**✅ Apertura de cuenta (obligatorio)**\n"
                "1. Abrir ticket\n"
                "2. Completar datos\n"
                "3. Verificación del banco\n"
                "4. Entrega de número de cuenta\n\n"
                "**💸 Depósitos**\n"
                "Entrega de dinero físico → registro → saldo acreditado.\n\n"
                "**💵 Retiros**\n"
                "Solicitud → verificación de saldo → entrega de efectivo.\n\n"
                "**🔁 Transferencias**\n"
                "Origen + destino + monto → registro → confirmación.\n\n"
                "**🧾 Registros**\n"
                "Toda operación se registra con fecha/hora, monto, motivo y firma del banco (staff)."
            ),
            color=discord.Color.orange()
        )
        e_proc.set_footer(text=f"{hhmm} • Banco Nacional")

        # 3) FONDOS PÚBLICOS (canal fondos públicos)
        e_public = discord.Embed(
            title="💰 Fondos Públicos del Estado",
            description=(
                "Los Fondos Públicos pertenecen al Estado y se utilizan para:\n\n"
                "• Sueldos estatales\n"
                "• Obras públicas\n"
                "• Seguridad y defensa\n"
                "• Proyectos del gobierno\n"
                "• Materiales y ayudas por emergencia\n\n"
                "**Reglas:**\n"
                "• Solo Gobierno/Tesorería autoriza movimientos.\n"
                "• Todo gasto debe tener motivo + aprobación + registro.\n\n"
                "**Abuso/corrupción:** retirar sin autorización o sin registro = sanción RP/administrativa."
            ),
            color=discord.Color.green()
        )
        e_public.set_footer(text=f"{hhmm} • Banco Nacional")

        # 4) MECÁNICAS (canal mecánicas)
        e_mech = discord.Embed(
            title="⚙️ Mecánicas del Banco (para jugadores)",
            description=(
                "• **Cuenta bancaria:** registro oficial del saldo.\n"
                "• **Saldo seguro:** no se pierde por robo/muerte.\n"
                "• **Dinero físico:** puede perderse (según reglas del server).\n"
                "• **Transferencias:** válidas solo si están registradas.\n"
                "• **Impuestos/multas:** pueden pasar por el banco.\n\n"
                "**Recomendación:** guardá grandes cantidades en el banco."
            ),
            color=discord.Color.blurple()
        )
        e_mech.set_footer(text=f"{hhmm} • Banco Nacional")

        await interaction.response.send_message("✅ Publicando información del banco en sus canales...", ephemeral=True)

        # Envíos por canal
        await ch_info.send(embed=e_info)
        await ch_info.send(embed=e_proc)
        await ch_public.send(embed=e_public)
        await ch_mech.send(embed=e_mech)

        # Log opcional
        if ch_logs:
            log = discord.Embed(
                title="🧾 Banco: información publicada",
                description=(
                    f"Publicado por: {member.mention}\n"
                    f"• Info/Procedimiento → {ch_info.mention}\n"
                    f"• Fondos públicos → {ch_public.mention}\n"
                    f"• Mecánicas → {ch_mech.mention}"
                ),
                color=discord.Color.greyple()
            )
            await ch_logs.send(embed=log)

async def setup(bot: commands.Bot):
    await bot.add_cog(banco_info(bot))
