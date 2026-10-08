import discord
from discord.ext import commands
import io
import os
import random
import string
import base64

TOKEN = os.environ.get("DISCORD_TOKEN", "COLA_TEU_TOKEN_AQUI")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def xor_encrypt(data: bytes, key: int) -> bytes:
    return bytes(b ^ key for b in data)


def obfuscate_lua(source: str) -> str:
    key = random.randint(50, 200)
    raw = source.encode('utf-8')
    encrypted = xor_encrypt(raw, key)
    b64 = base64.b64encode(encrypted).decode('ascii')

    chunk_size = 800
    chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

    vk = '_' + ''.join(random.choices(string.ascii_letters, k=8))
    vc = '_' + ''.join(random.choices(string.ascii_letters, k=8))
    vd = '_' + ''.join(random.choices(string.ascii_letters, k=8))
    vi = '_' + ''.join(random.choices(string.ascii_letters, k=6))

    chunk_table = '{' + ','.join(f'"{c}"' for c in chunks) + '}'

    return f'''--[[ LC10 Obfuscation Layer ]]
local {vk} = {key}
local {vc} = {chunk_table}
local {vd} = table.concat({vc})
local decoded = game:GetService("HttpService"):Base64Decode({vd})
local bytes = {{}}
for {vi} = 1, #decoded do
    bytes[{vi}] = string.char(string.byte(decoded, {vi}) ~ {vk})
end
local fn = loadstring or load
fn(table.concat(bytes))()
'''


def split_text(text: str, parts: int = 4):
    n = len(text)
    size = (n + parts - 1) // parts
    return [text[i*size:(i+1)*size] for i in range(parts) if text[i*size:(i+1)*size]]


@bot.event
async def on_ready():
    print(f"[LC10 Bot] Logado como {bot.user}")


@bot.command(name="ofuscar")
async def ofuscar(ctx):
    if not ctx.message.attachments:
        await ctx.send("Precisa anexar um arquivo .lua ou .txt junto com o comando.")
        return

    att = ctx.message.attachments[0]
    if not att.filename.endswith(('.lua', '.txt')):
        await ctx.send("Precisa ser .lua ou .txt")
        return

    try:
        raw = await att.read()
        source = raw.decode('utf-8')
    except Exception as e:
        await ctx.send(f"Erro ao ler arquivo: {e}")
        return

    try:
        obfuscated = obfuscate_lua(source)
    except Exception as e:
        await ctx.send(f"Erro na ofuscacao: {e}")
        return

    parts = split_text(obfuscated, 4)

    files = []
    for i, part in enumerate(parts, 1):
        buf = io.BytesIO(part.encode('utf-8'))
        buf.seek(0)
        files.append(discord.File(buf, filename=f"LC10_parte_{i}.txt"))

    sizes = [len(p) for p in parts]
    await ctx.send(
        f"Ofuscado e dividido em 4 partes\n"
        f"Original: {len(source):,} bytes\n"
        f"Ofuscado: {len(obfuscated):,} bytes\n"
        f"Tamanhos: " + " | ".join(f"{s:,}" for s in sizes) + "\n"
        f"Baixe 1 -> 2 -> 3 -> 4 e junta com !junta",
        files=files
    )


@bot.command(name="junta")
async def junta(ctx):
    loader = '''-- LC10 - Junta as 4 partes e roda
local partes = {}
for i = 1, 4 do
    local c = readfile("LC10_parte_" .. i .. ".txt")
    if not c then
        warn("Faltando: LC10_parte_" .. i .. ".txt")
        return
    end
    table.insert(partes, c)
end
local resultado = table.concat(partes)
writefile("LC10_protected.lua", resultado)
print("Salvo: LC10_protected.lua (" .. #resultado .. " bytes)")
loadstring(resultado)()
'''
    buf = io.BytesIO(loader.encode('utf-8'))
    buf.seek(0)
    await ctx.send("Cola isso no Delta junto com as 4 partes:", file=discord.File(buf, filename="junta.lua"))


@bot.command(name="ajuda")
async def ajuda(ctx):
    embed = discord.Embed(title="LC10 Obfuscator", color=0x7C5CFF)
    embed.add_field(name="!ofuscar", value="Anexa .lua -> recebe 4 partes ofuscadas", inline=False)
    embed.add_field(name="!junta", value="Manda o script que junta as 4 partes e roda", inline=False)
    await ctx.send(embed=embed)


bot.run(TOKEN)
