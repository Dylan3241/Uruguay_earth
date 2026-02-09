import yaml
import discord
import asyncio
from discord.ext import commands

CONFIG_PATH = "config.yaml"

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()

TICKETS_CATEGORY_ID = int(cfg["tickets_category_id"])
SUPPORT_ROLE_ID = int(cfg["support_role_id"])
TICKETS_LOG_CHANNEL_ID = int(cfg["tickets_log_channel_id"])
MAX_OPEN_TICKETS_PER_USER = int(cfg.get("max_open_tickets_per_user", 1))

# ================
# Botones fijos 
# ================
TICKET_TYPES = {
    "ciudadania": {
        "label": "Ciudadanía",
        "emoji": "🏛️",
        "prefix": "ciudadania",
        "panel_desc": "Trámites de ciudadanía, requisitos, pasos y verificación.",
        "ticket_prompt": (
            "Completá esto para ayudarte más rápido:\n"
            "• **Nick/IGN:**\n"
            "• **País/ciudad en el server:**\n"
            "• **¿Qué querés hacer? (ciudadanía/renovación/etc):**\n"
            "• **Capturas o info extra (si aplica):**"
        ),
    },
    "postulaciones": {
        "label": "Postulaciones",
        "emoji": "📄",
        "prefix": "postulaciones",
        "panel_desc": "Postularse a staff, trabajos, rangos, facciones o roles.",
        "ticket_prompt": (
            "Completá esto:\n"
            "• **Nick/IGN:**\n"
            "• **Edad:**\n"
            "• **¿A qué te postulás? (staff/facción/rol):**\n"
            "• **Experiencia (si tenés):**\n"
            "• **Disponibilidad horaria:**\n"
            "• **Por qué te gustaría entrar:**"
        ),
    },
    "alianzas": {
        "label": "Alianzas",
        "emoji": "🤝",
        "prefix": "alianzas",
        "panel_desc": "Alianzas con otros servers, comunidades o creadores.",
        "ticket_prompt": (
            "Para alianzas, pasá:\n"
            "• **Nombre del proyecto/server:**\n"
            "• **Redes/Discord invite:**\n"
            "• **Qué proponés (beneficios / intercambio):**\n"
            "• **Tu contacto (Discord/IG):**\n"
            "• **Detalles extra (si hay):**"
        ),
    },
    "reportar": {
        "label": "Reportar",
        "emoji": "🚨",
        "prefix": "reportar",
        "panel_desc": "Reportes de jugadores, bugs, hacks o conductas.",
        "ticket_prompt": (
            "Reporte — completá lo más posible:\n"
            "• **Nick del reportado:**\n"
            "• **Tu nick/IGN:**\n"
            "• **Motivo del reporte:**\n"
            "• **Fecha y hora aprox:**\n"
            "• **Pruebas (capturas/video/links):**\n"
            "• **Lugar (coords / zona / ciudad):**"
        ),
    },
    "dudas": {
        "label": "Dudas",
        "emoji": "❓",
        "prefix": "dudas",
        "panel_desc": "Consultas generales sobre el server, reglas o sistemas.",
        "ticket_prompt": (
            "Contanos tu duda:\n"
            "• **Nick/IGN:**\n"
            "• **Pregunta / problema:**\n"
            "• **Qué intentaste (si aplica):**\n"
            "• **Captura o contexto (si ayuda):**"
        ),
    },
}

def make_channel_name(ticket_key: str, user: discord.Member) -> str:
    prefix = TICKET_TYPES[ticket_key]["prefix"]
    base = f"{prefix}-{user.name}".lower().replace(" ", "-")
    return base[:90]

async def count_open_tickets(category: discord.CategoryChannel, user: discord.Member) -> int:

    # Cuenta tickets por topic guardando user_id=
    count = 0
    for ch in category.text_channels:
        if ch.topic and f"user_id={user.id}" in ch.topic:
            count += 1
    return count

# =============================
# Views
# =============================
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Cerrar",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket:close"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        guild = interaction.guild

        if not guild or not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Esto solo funciona dentro de un ticket.",
                ephemeral=True
            )

        support_role = guild.get_role(SUPPORT_ROLE_ID)
        is_support = bool(
            support_role
            and isinstance(interaction.user, discord.Member)
            and support_role in interaction.user.roles
        )
        is_owner = bool(channel.topic and f"user_id={interaction.user.id}" in channel.topic)

        if not (is_support or is_owner or interaction.user.guild_permissions.manage_channels):
            return await interaction.response.send_message(
                "No tenés permiso para cerrar este ticket.",
                ephemeral=True
            )

        await interaction.response.send_message("🗑️ Cerrando ticket en 5 segundos...", ephemeral=True)
        await asyncio.sleep(5)

        # OJO: el bot necesita permiso Manage Channels para borrar
        await channel.delete(reason="Ticket cerrado")


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        for key, data in TICKET_TYPES.items():
            self.add_item(discord.ui.Button(
                label=data["label"],
                emoji=data["emoji"],
                style=discord.ButtonStyle.primary,
                custom_id=f"ticket:create:{key}"
            ))

# =============================
# Cog
# =============================
class tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):

        # Persist views para que los botones sigan funcionando tras reinicio
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(TicketCloseView())

    @commands.command(name="paneltickets")
    @commands.has_permissions(administrator=True)
    async def paneltickets(self, ctx: commands.Context):

        # Embed con descripciones de cada botón
        desc_lines = []
        for key, data in TICKET_TYPES.items():
            desc_lines.append(f"{data['emoji']} **{data['label']}** — {data['panel_desc']}")

        embed = discord.Embed(
            title="🎫 Sistema de Tickets — Uruguay Earth",
            description="Abrí un ticket según lo que necesites:\n\n" + "\n".join(desc_lines),
            color=discord.Color.green()
        )
        embed.set_footer(text="⚠️ Un ticket a la vez. Adjuntá pruebas si corresponde.")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1466266582362624033/1469892450779922656/descarga_2.png?ex=69894f85&is=6987fe05&hm=c9aaf357a20eaebfbf2fafb1f5a88a21fff022a405c947f18ca99ffaac0610ec&")

        await ctx.send(embed=embed, view=TicketPanelView())

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component or not interaction.data:
            return

        custom_id = interaction.data.get("custom_id")
        if not custom_id or not custom_id.startswith("ticket:create:"):
            return

        ticket_key = custom_id.split("ticket:create:", 1)[1]
        if ticket_key not in TICKET_TYPES:
            return await interaction.response.send_message("Tipo de ticket inválido.", ephemeral=True)

        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("No guild.", ephemeral=True)

        category = guild.get_channel(TICKETS_CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message("La categoría de tickets no existe.", ephemeral=True)

        support_role = guild.get_role(SUPPORT_ROLE_ID)
        if not support_role:
            return await interaction.response.send_message("No encuentro el rol de soporte.", ephemeral=True)

        log_channel = guild.get_channel(TICKETS_LOG_CHANNEL_ID)
        if not isinstance(log_channel, discord.TextChannel):
            log_channel = None 

        # Límite por usuario
        opened = await count_open_tickets(category, interaction.user)
        if opened >= MAX_OPEN_TICKETS_PER_USER:
            return await interaction.response.send_message(
                f"⚠️ Ya tenés {opened} ticket(s) abierto(s). Cerrá el anterior para abrir otro.",
                ephemeral=True
            )

        # Permisos
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),
            support_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                read_message_history=True
            ),
        }

        channel_name = make_channel_name(ticket_key, interaction.user)
        topic = f"ticket={ticket_key} | user_id={interaction.user.id}"

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=topic
        )

        # Mensaje inicial dentro del ticket (según categoría)
        data = TICKET_TYPES[ticket_key]
        embed = discord.Embed(
            title=f"{data['emoji']} {data['label']}",
            description=data["ticket_prompt"]
        )
        embed.set_footer(text="Por favor, respondé en este canal. Staff te atiende apenas pueda.")

        await ticket_channel.send(
            content=f"{interaction.user.mention} | {support_role.mention}",
            embed=embed,
            view=TicketCloseView()
        )

        # Log
        if log_channel:
            log_embed = discord.Embed(
                title="🧾 Ticket creado",
                description=(
                    f"**Tipo:** {data['label']}\n"
                    f"**Usuario:** {interaction.user.mention}\n"
                    f"**Canal:** {ticket_channel.mention}"
                )
            )
            await log_channel.send(embed=log_embed)

        await interaction.response.send_message(
            f"✅ Ticket creado: {ticket_channel.mention}",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(tickets(bot))
