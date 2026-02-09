import yaml
import pycountry
import discord
import requests

from io import BytesIO
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
from discord import app_commands
from discord.ext import commands

CONFIG_PATH = "config.yaml"

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()

CHANNEL_ALLIANCE_ID = int(cfg["channel_alliance_id"])
CITIZEN_ROLE_ID = int(cfg["citizen_role_id"])

URUGUAY_ISO2 = "uy"

def flag_url(code: str) -> str:
    # w640 (bandera decente para armar la imagen)
    return f"https://flagcdn.com/w640/{code}.png"

def get_iso2(name: str) -> str | None:
    name = name.strip()
    try:
        return pycountry.countries.search_fuzzy(name)[0].alpha_2.lower()
    except Exception:
        return None

def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Intentamos Arial (Windows). Si falla, usamos la default.
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except Exception:
        try:
            return ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", size=size)
        except Exception:
            return ImageFont.load_default()

def combine_flags_with_title(left_code: str, right_code: str, title_text: str) -> BytesIO:
    # Descargar
    r1 = requests.get(flag_url(left_code), timeout=15)
    r2 = requests.get(flag_url(right_code), timeout=15)
    r1.raise_for_status()
    r2.raise_for_status()

    img1 = Image.open(BytesIO(r1.content)).convert("RGBA")
    img2 = Image.open(BytesIO(r2.content)).convert("RGBA")

    # Igualar altura
    h = min(img1.height, img2.height)
    img1 = img1.resize((int(img1.width * h / img1.height), h))
    img2 = img2.resize((int(img2.width * h / img2.height), h))

    # Armar lado a lado
    combined_w = img1.width + img2.width
    combined_h = h

    # Agregamos un banner arriba para el texto
    banner_h = max(60, combined_h // 6)  # se adapta al tamaño
    out = Image.new("RGBA", (combined_w, combined_h + banner_h), (0, 0, 0, 0))

    # Fondo banner (semi transparente)
    draw = ImageDraw.Draw(out)
    draw.rectangle([0, 0, combined_w, banner_h], fill=(0, 0, 0, 140))

    # Pegamos banderas abajo del banner
    out.paste(img1, (0, banner_h))
    out.paste(img2, (img1.width, banner_h))

    # Texto centrado
    font = _load_font(size=max(22, banner_h // 2))
    text = title_text

    # Medir texto (compatible)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (combined_w - tw) // 2
    ty = (banner_h - th) // 2

    # Sombra + texto
    draw.text((tx + 2, ty + 2), text, font=font, fill=(0, 0, 0, 220))
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))

    # Export PNG
    buf = BytesIO()
    out.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return buf


class BreakAllianceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Romper alianza",
        emoji="💔",
        style=discord.ButtonStyle.danger,
        custom_id="alliance:break"
    )
    async def break_alliance(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.user

        # Solo admins o manage_guild
        if not isinstance(member, discord.Member) or not (
            member.guild_permissions.administrator
            or member.guild_permissions.manage_guild
        ):
            return await interaction.response.send_message(
                "❌ No tenés permisos para romper alianzas.",
                ephemeral=True
            )

        msg = interaction.message

        await interaction.response.send_message("💔 Alianza eliminada.", ephemeral=True)

        try:
            await msg.delete()
        except:
            pass

class alianzas(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Persistencia del botón “Romper alianza”
        self.bot.add_view(BreakAllianceView())
        await self.bot.tree.sync()

    @app_commands.command(name="alianza", description="Publica una nueva alianza con un país.")
    @app_commands.describe(pais="Nombre del país aliado (ej: Argentina, Brasil, United States)")
    async def alianza(self, interaction: discord.Interaction, pais: str):
        iso = get_iso2(pais)
        if not iso:
            return await interaction.response.send_message(
                "❌ No pude reconocer ese país.\n"
                "Probá con el nombre oficial (ej: `Argentina`, `Brazil`, `United States`).",
                ephemeral=True
            )

        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("Esto solo funciona en un servidor.", ephemeral=True)

        alliance_channel = guild.get_channel(CHANNEL_ALLIANCE_ID)
        if not isinstance(alliance_channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ No encuentro el canal de alianzas. Revisá `channel_alliance_id` en config.yaml.",
                ephemeral=True
            )

        citizen_role = guild.get_role(CITIZEN_ROLE_ID)
        if not citizen_role:
            return await interaction.response.send_message(
                "❌ No encuentro el rol ciudadano. Revisá `citizen_role_id` en config.yaml.",
                ephemeral=True
            )

        # Imagen combinada con texto arriba
        title_text = f"Uruguay 🤝 {pais.strip()}"
        img_buf = combine_flags_with_title(URUGUAY_ISO2, iso, title_text)

        # Fecha automática
        now = datetime.now(timezone.utc)

        embed = discord.Embed(
            title="🤝 Nueva alianza hecha",
            description=f"País aliado actualmente: **{pais.strip()}**",
            color=discord.Color.green(),
            timestamp=now
        )
        embed.set_footer(text=f"UY + {iso.upper()} • {now.strftime('%d/%m/%Y %H:%M')} UTC")

        file = discord.File(img_buf, filename="alianza.png")
        embed.set_image(url="attachment://alianza.png")

        # Publicar en canal de alianzas + ping rol ciudadano
        await alliance_channel.send(
            content=citizen_role.mention,
            embed=embed,
            file=file,
            view=BreakAllianceView(),
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

        # Confirmación al que ejecuta
        await interaction.response.send_message(
            f"✅ Alianza publicada en {alliance_channel.mention} y notificada a {citizen_role.mention}.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(alianzas(bot))
