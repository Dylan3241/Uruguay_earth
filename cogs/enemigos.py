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

CHANNEL_ENEMY_ID = int(cfg["channel_enemy_id"])
CITIZEN_ROLE_ID = int(cfg["citizen_role_id"])

URUGUAY_ISO2 = "uy"

def flag_url(code: str) -> str:
    return f"https://flagcdn.com/w640/{code}.png"

def get_iso2(name: str) -> str | None:
    name = name.strip()
    try:
        return pycountry.countries.search_fuzzy(name)[0].alpha_2.lower()
    except Exception:
        return None

def _load_font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except Exception:
        try:
            return ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", size=size)
        except Exception:
            return ImageFont.load_default()

def combine_flags_with_title(left_code: str, right_code: str, title_text: str) -> BytesIO:
    r1 = requests.get(flag_url(left_code), timeout=15)
    r2 = requests.get(flag_url(right_code), timeout=15)
    r1.raise_for_status()
    r2.raise_for_status()

    img1 = Image.open(BytesIO(r1.content)).convert("RGBA")
    img2 = Image.open(BytesIO(r2.content)).convert("RGBA")

    h = min(img1.height, img2.height)
    img1 = img1.resize((int(img1.width * h / img1.height), h))
    img2 = img2.resize((int(img2.width * h / img2.height), h))

    combined_w = img1.width + img2.width
    combined_h = h

    banner_h = max(60, combined_h // 6)
    out = Image.new("RGBA", (combined_w, combined_h + banner_h), (0, 0, 0, 0))

    draw = ImageDraw.Draw(out)
    draw.rectangle([0, 0, combined_w, banner_h], fill=(0, 0, 0, 160))

    out.paste(img1, (0, banner_h))
    out.paste(img2, (img1.width, banner_h))

    font = _load_font(size=max(22, banner_h // 2))
    text = title_text

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (combined_w - tw) // 2
    ty = (banner_h - th) // 2

    draw.text((tx + 2, ty + 2), text, font=font, fill=(0, 0, 0, 220))
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))

    buf = BytesIO()
    out.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return buf

class RemoveEnemyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Quitar enemigo",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="enemy:remove"
    )
    async def remove_enemy(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user

        if not isinstance(member, discord.Member) or not (
            member.guild_permissions.administrator or member.guild_permissions.manage_guild
        ):
            return await interaction.response.send_message(
                "❌ No tenés permisos para quitar enemigos.",
                ephemeral=True
            )

        msg = interaction.message
        await interaction.response.send_message("🗑️ Enemigo eliminado.", ephemeral=True)

        try:
            await msg.delete()
        except:
            pass


class enemigos(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(RemoveEnemyView())
        await self.bot.tree.sync()

    @app_commands.command(name="enemigo", description="Publica un nuevo enemigo del país.")
    @app_commands.describe(pais="Nombre del país enemigo (ej: Argentina, Brasil, United States)")
    async def enemigo(self, interaction: discord.Interaction, pais: str):
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

        enemy_channel = guild.get_channel(CHANNEL_ENEMY_ID)
        if not isinstance(enemy_channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ No encuentro el canal de enemigos. Revisá `channel_enemy_id` en config.yaml.",
                ephemeral=True
            )

        citizen_role = guild.get_role(CITIZEN_ROLE_ID)
        if not citizen_role:
            return await interaction.response.send_message(
                "❌ No encuentro el rol ciudadano. Revisá `citizen_role_id` en config.yaml.",
                ephemeral=True
            )

        # Texto arriba (enemistad)
        title_text = f"Uruguay ⚔️ {pais.strip()}"
        img_buf = combine_flags_with_title(URUGUAY_ISO2, iso, title_text)

        now = datetime.now(timezone.utc)

        embed = discord.Embed(
            title="⚔️ Nuevo enemigo declarado",
            description=f"País enemigo actualmente: **{pais.strip()}**",
            color=discord.Color.red(),
            timestamp=now
        )
        embed.set_footer(text=f"UY ⚔️ {iso.upper()} • {now.strftime('%d/%m/%Y %H:%M')} UTC")

        file = discord.File(img_buf, filename="enemigo.png")
        embed.set_image(url="attachment://enemigo.png")

        await enemy_channel.send(
            content=citizen_role.mention,
            embed=embed,
            file=file,
            view=RemoveEnemyView(),
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

        await interaction.response.send_message(
            f"✅ Enemigo publicado en {enemy_channel.mention} y notificado a {citizen_role.mention}.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(enemigos(bot))
