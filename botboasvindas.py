"""
Bot de Boas-Vindas — Discord
Avisa quando alguém entra ou sai do servidor.
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN_WELCOME")
ARQUIVO_CONFIG = "config_welcome.json"

MSG_ENTRADA_PADRAO = "🎉 Bem-vindo(a)!\n\n👋 Olá {usuario}, seja muito bem-vindo(a) ao **{servidor}**!\n\n✨ Esperamos que aproveite sua estadia e faça parte da nossa comunidade.\n\n📋 Não se esqueça de ler as regras e interagir com os membros!"
MSG_SAIDA_PADRAO = "**{usuario}** saiu do servidor. Até mais! 👋"


def carregar_config() -> dict:
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_config(config: dict) -> None:
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"[INFO] on_ready disparado como {bot.user} | Servidores: {len(bot.guilds)}")
    try:
        # Sincroniza globalmente
        synced = await bot.tree.sync()
        print(f"[OK] {len(synced)} comando(s) sincronizados globalmente.")
    except Exception as e:
        print(f"[ERRO] Falha ao sincronizar commands: {e}")


async def enviar_log(guild: discord.Guild, guild_cfg: dict, embed: discord.Embed):
    canal_log_id = guild_cfg.get("canal_log_id")
    if not canal_log_id:
        return
    canal_log = guild.get_channel(canal_log_id)
    if canal_log:
        await canal_log.send(embed=embed)


@bot.event
async def on_member_join(member: discord.Member):
    config = carregar_config()
    guild_cfg = config.get(str(member.guild.id), {})

    # Mensagem de boas-vindas
    canal_id = guild_cfg.get("canal_entrada_id")
    if canal_id:
        canal = member.guild.get_channel(canal_id)
        if canal:
            texto = (
                f"Seja muito Bem-vindo(a)!\n\n"
                f"👋 Olá {member.mention}, seja muito bem-vindo(a) ao servidor da(o) **{member.guild.name}**\n\n"
                f"🔹 Esperamos que aproveite sua estadia!\n\n"
                f"📋 Não se esqueça de ler as regras e interagir com os membros!"
            )
            embed = discord.Embed(description=texto, color=0x2b2d31)
            embed.set_thumbnail(url=member.display_avatar.url)
            imagem = guild_cfg.get("imagem_entrada")
            if imagem:
                embed.set_image(url=imagem)
            await canal.send(embed=embed)

    # Log de entrada
    criado_em = discord.utils.format_dt(member.created_at, style="F")
    embed_log = discord.Embed(
        title="📥 Membro entrou",
        color=0x57f287,
        timestamp=member.joined_at,
    )
    embed_log.set_thumbnail(url=member.display_avatar.url)
    embed_log.add_field(name="Usuário", value=f"{member} ({member.mention})", inline=False)
    embed_log.add_field(name="ID", value=member.id, inline=True)
    embed_log.add_field(name="Conta criada em", value=criado_em, inline=False)
    embed_log.add_field(name="Total de membros", value=member.guild.member_count, inline=True)
    embed_log.set_footer(text=f"ID: {member.id}")
    await enviar_log(member.guild, guild_cfg, embed_log)


@bot.event
async def on_member_remove(member: discord.Member):
    config = carregar_config()
    guild_cfg = config.get(str(member.guild.id), {})

    # Mensagem de saída
    canal_id = guild_cfg.get("canal_saida_id")
    if canal_id:
        canal = member.guild.get_channel(canal_id)
        if canal:
            total = member.guild.member_count
            texto = (
                f"👋 Até logo!\n\n"
                f"😢 {member.mention} saiu do servidor.\n\n"
                f"📉 Agora somos **{total}** membros.\n\n"
                f"💭 Esperamos revê-lo(a) em breve!"
            )
            embed = discord.Embed(description=texto, color=0x2b2d31)
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal.send(embed=embed)

    # Log de saída
    cargos = [r.mention for r in member.roles if r.name != "@everyone"]
    embed_log = discord.Embed(
        title="📤 Membro saiu",
        color=0xed4245,
        timestamp=discord.utils.utcnow(),
    )
    embed_log.set_thumbnail(url=member.display_avatar.url)
    embed_log.add_field(name="Usuário", value=f"{member} ({member.mention})", inline=False)
    embed_log.add_field(name="ID", value=member.id, inline=True)
    embed_log.add_field(name="Total de membros", value=member.guild.member_count, inline=True)
    embed_log.add_field(name="Cargos", value=" ".join(cargos) if cargos else "Nenhum", inline=False)
    embed_log.set_footer(text=f"ID: {member.id}")
    await enviar_log(member.guild, guild_cfg, embed_log)


# ── /setup_welcome ────────────────────────────────────────────────────────────

@bot.tree.command(name="setup_welcome", description="Configura os canais de entrada, saída e log (somente admins)")
@app_commands.describe(
    canal_entrada="Canal onde a mensagem de boas-vindas será enviada",
    canal_saida="Canal onde a mensagem de saída será enviada",
    canal_log="Canal onde os logs de entrada/saída serão registrados",
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(
    interaction: discord.Interaction,
    canal_entrada: discord.TextChannel,
    canal_saida: discord.TextChannel,
    canal_log: discord.TextChannel,
):
    try:
        await interaction.response.defer(ephemeral=True)
        config = carregar_config()
        guild_id = str(interaction.guild_id)
        if guild_id not in config:
            config[guild_id] = {}
        config[guild_id]["canal_entrada_id"] = canal_entrada.id
        config[guild_id]["canal_saida_id"] = canal_saida.id
        config[guild_id]["canal_log_id"] = canal_log.id
        salvar_config(config)
        await interaction.followup.send(
            f"✅ Configurado!\n"
            f"📥 **Entrada:** {canal_entrada.mention}\n"
            f"📤 **Saída:** {canal_saida.mention}\n"
            f"📋 **Log:** {canal_log.mention}",
            ephemeral=True,
        )
    except Exception as e:
        print(f"[ERRO] setup_welcome: {e}")
        await interaction.followup.send("❌ Erro ao salvar configuração.", ephemeral=True)


# ── /msg_entrada ──────────────────────────────────────────────────────────────

@bot.tree.command(name="msg_entrada", description="Define a mensagem de boas-vindas (somente admins)")
@app_commands.describe(mensagem="Use {usuario} e {servidor} no texto.")
@app_commands.checks.has_permissions(administrator=True)
async def msg_entrada(interaction: discord.Interaction, mensagem: str):
    config = carregar_config()
    guild_id = str(interaction.guild_id)
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id]["msg_entrada"] = mensagem
    salvar_config(config)
    preview = mensagem.replace("{usuario}", interaction.user.mention).replace("{servidor}", interaction.guild.name)
    await interaction.response.send_message(
        f"✅ Mensagem atualizada!\n**Preview:** {preview}", ephemeral=True
    )


# ── /imagem_entrada ───────────────────────────────────────────────────────────

@bot.tree.command(name="imagem_entrada", description="Define a imagem/GIF no embed de boas-vindas (somente admins)")
@app_commands.describe(url="URL da imagem ou GIF")
@app_commands.checks.has_permissions(administrator=True)
async def imagem_entrada(interaction: discord.Interaction, url: str):
    config = carregar_config()
    guild_id = str(interaction.guild_id)
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id]["imagem_entrada"] = url
    salvar_config(config)
    await interaction.response.send_message(
        f"✅ Imagem configurada!", ephemeral=True
    )


# ── /msg_saida ────────────────────────────────────────────────────────────────

@bot.tree.command(name="msg_saida", description="Define a mensagem de saída (somente admins)")
@app_commands.describe(mensagem="Use {usuario} no texto.")
@app_commands.checks.has_permissions(administrator=True)
async def msg_saida(interaction: discord.Interaction, mensagem: str):
    config = carregar_config()
    guild_id = str(interaction.guild_id)
    if guild_id not in config:
        config[guild_id] = {}
    config[guild_id]["msg_saida"] = mensagem
    salvar_config(config)
    preview = mensagem.replace("{usuario}", interaction.user.display_name)
    await interaction.response.send_message(
        f"✅ Mensagem de saída atualizada!\n**Preview:** {preview}", ephemeral=True
    )


# ── Erros de permissão ────────────────────────────────────────────────────────

@setup_welcome.error
@msg_entrada.error
@imagem_entrada.error
@msg_saida.error
async def admin_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "🚫 Apenas administradores podem usar este comando.", ephemeral=True
        )


# ── Inicialização ─────────────────────────────────────────────────────────────
bot.run(TOKEN)
