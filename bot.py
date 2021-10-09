import discord
import asyncio 
import requests
from requests import get
import aiosqlite
from discord.ext import commands
from discord.ext import tasks
from itertools import cycle
from asyncio import sleep
import json
import math
import asyncio



intents = discord.Intents.default()
intents.members = True
status = cycle(['BOT', 'https://github.com/pumbaczech', 'FORTNITE', 'BOT'])
bot = commands.Bot(command_prefix="!", intents=intents)
bot.multiplier = 1
bot.remove_command("help")

async def initialize():
    await bot.wait_until_ready()
    bot.db = await aiosqlite.connect("expData.db")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS guildData (guild_id int, user_id int, exp int, PRIMARY KEY (guild_id, user_id))")
    

@bot.event
async def on_ready():
    change_status.start()
    print('Currently Online as {0.user}'.format(bot))
    print("Ready")





@bot.command()
async def ping(ctx):
  await ctx.send(f"Pong! {bot.latency}")

@bot.command()
async def help(ctx):
    helpEmbed = discord.Embed(title = "!Help", color = discord.Color.red())
    helpEmbed.add_field(name = "Moderation", value = "!tempban, !clear |")
    helpEmbed.add_field(name = "Fortnite", value = "!map, !news, !shop |")
    helpEmbed.add_field(name = "Fun", value = "!meme")
    helpEmbed.add_field(name = "Info", value = "!infoserver, !ping, !stats, !leaderboard, !servercount")
    helpEmbed.set_footer(text="Created by pumbaczech#0818")
    await ctx.send(embed = helpEmbed)

@tasks.loop(seconds=5)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status)))


@bot.command()
async def meme(ctx):
    content = get("https://meme-api.herokuapp.com/gimme").text
    data = json.loads(content,)
    meme = discord.Embed(title=f"{data['title']} "",author: "f"{data['author']}", Color = discord.Color.random()).set_image(url=f"{data['url']}")
    await ctx.reply(embed=meme)

@bot.command()
async def infoserver(ctx):
    name = str(ctx.guild.name)
    description = str(ctx.guild.description)

    owner = str(ctx.guild.owner)
    id = str(ctx.guild.id)
    region = str(ctx.guild.region)
    memberCount = str(ctx.guild.member_count)

    icon = str(ctx.guild.icon_url)

    embed = discord.Embed(
        title=name + " Server Information",
        description=description,
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value=owner, inline=True)
    embed.add_field(name="Server ID", value=id, inline=True)
    embed.add_field(name="Region", value=region, inline=True)
    embed.add_field(name="Member Count", value=memberCount, inline=True)
    embed.set_footer(text="Created by pumbaczech#0818")
    await ctx.send(embed=embed)


class DurationConverter(commands.Converter):
    async def convert(self, ctx, argument):
        amount = argument[:-1]
        unit = argument[-1]

        if amount.isdigit() and unit in ['s', 'm']:
            return (int(amount), unit)

        raise commands.BadArgument(message='Not a valid duration')











@bot.command()
async def shop(ctx):
    embed = discord.Embed(tittle="fortnite item shop")
    embed.set_image(url="https://fortool.fr/cm/assets/shop/en.png")
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if not message.author.bot:
        cursor = await bot.db.execute("INSERT OR IGNORE INTO guildData (guild_id, user_id, exp) VALUES (?,?,?)", (message.guild.id, message.author.id, 1)) 

        if cursor.rowcount == 0:
            await bot.db.execute("UPDATE guildData SET exp = exp + 1 WHERE guild_id = ? AND user_id = ?", (message.guild.id, message.author.id))
            cur = await bot.db.execute("SELECT exp FROM guildData WHERE guild_id = ? AND user_id = ?", (message.guild.id, message.author.id))
            data = await cur.fetchone()
            exp = data[0]
            lvl = math.sqrt(exp) / bot.multiplier
        
            if lvl.is_integer():
                await message.channel.send(f"{message.author.mention} well done! You're now level: {int(lvl)}.")

        await bot.db.commit()

    await bot.process_commands(message)


@bot.command()
async def news(ctx):
    r = requests.get("https://fortnite-api.com/v2/news/br")
    data = r.json()
    embed = discord.Embed(tittle="News")
    embed.set_image(url=data["data"]["image"])
    await ctx.send(embed=embed)




@bot.command()
async def map(ctx):
    embed = discord.Embed(tittle="FORTNITE MAP")
    embed.set_image(url="https://fortnite-api.com/images/map_en.png")
    await ctx.send(embed=embed)


@bot.event
async def on_member_join(message):
    await member.create_dm()
    await member.dm_channel.send("WELCOME TO SERVER")

@bot.event
async def on_member_remove(member):
    print(f'{member} has left a server.')

@bot.event
async def on_member_join(member):
    print(f'{member} has joined a server.')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Invalid command')

@bot.command()
async def clear(ctx, amount : int):
    await ctx.channel.purge(limit=amount)

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify an amount of messages to delete.')



@bot.command()
async def  tempban(ctx, member: commands.MemberConverter, duration: DurationConverter):

    multiplier = {'s': 1, 'm': 60}
    amount, unit = duration

    await ctx.guild.ban(member)
    await ctx.send(f'{member} has been banned for {amount}{unit}.')
    await asyncio.sleep(amount * multiplier[unit])
    await ctx.guild.unban(member)



intents=discord.Intents.default()
intents = discord.Intents(messages=True, guilds=True)


@bot.command()
async def stats(ctx, member: discord.Member=None):
    if member is None: member = ctx.author

    
    async with bot.db.execute("SELECT exp FROM guildData WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id)) as cursor:
        data = await cursor.fetchone()
        exp = data[0]

        
    async with bot.db.execute("SELECT exp FROM guildData WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
        rank = 1
        async for value in cursor:
            if exp < value[0]:
                rank += 1

    lvl = int(math.sqrt(exp)//bot.multiplier)

    current_lvl_exp = (bot.multiplier*(lvl))**2
    next_lvl_exp = (bot.multiplier*((lvl+1)))**2

    lvl_percentage = ((exp-current_lvl_exp) / (next_lvl_exp-current_lvl_exp)) * 100

    embed = discord.Embed(title=f"Stats for {member.name}", colour=discord.Colour.red())
    embed.add_field(name="Level", value=str(lvl))
    embed.add_field(name="Exp", value=f"{exp}/{next_lvl_exp}")
    embed.add_field(name="Rank", value=f"{rank}/{ctx.guild.member_count}")
    embed.add_field(name="Level Progress", value=f"{round(lvl_percentage, 2)}%")
    embed.set_footer(text="Created by pumbaczech#0818")

    await ctx.send(embed=embed)

@bot.command(pass_context=True)
async def servercount(ctx):
    embed=discord.Embed(tittle="Counter", colour=discord.Colour.red())
    embed.add_field(name="playing on: " ,value=str(len(bot.guilds)) + " Servers")
    embed.set_footer(text="Created by pumbaczech#0818")
    await ctx.send(embed=embed)

@bot.command()
async def leaderboard(ctx): 
    buttons = {}
    for i in range(1, 6):
        buttons[f"{i}\N{COMBINING ENCLOSING KEYCAP}"] = i 

    previous_page = 0
    current = 1
    index = 1
    entries_per_page = 10

    embed = discord.Embed(title=f"Leaderboard Page {current}", description="", colour=discord.Colour.red())
    msg = await ctx.send(embed=embed)

    for button in buttons:
        await msg.add_reaction(button)

    while True:
        if current != previous_page:
            embed.title = f"Leaderboard Page {current}"
            embed.description = ""

            async with bot.db.execute(f"SELECT user_id, exp FROM guildData WHERE guild_id = ? ORDER BY exp DESC LIMIT ? OFFSET ? ", (ctx.guild.id, entries_per_page, entries_per_page*(current-1),)) as cursor:
                index = entries_per_page*(current-1)

                async for entry in cursor:
                    index += 1
                    member_id, exp = entry
                    member = ctx.guild.get_member(member_id)
                    embed.description += f"{index}) {member.mention} : {exp}\n"

                await msg.edit(embed=embed)

        try:
            reaction, user = await bot.wait_for("reaction_add", check=lambda reaction, user: user == ctx.author and reaction.emoji in buttons, timeout=60.0)

        except asyncio.TimeoutError:
            return await msg.clear_reactions()

        else:
            previous_page = current
            await msg.remove_reaction(reaction.emoji, ctx.author)
            current = buttons[reaction.emoji]

bot.loop.create_task(initialize())
bot.run("you-discord-api")
asyncio.run(bot.db.close())