#
#  Author: fmfarto @ GitHub
#

import discord
import asyncio
import aiohttp

import os
import platform
from datetime import date

from discord.ext import commands
from discord import app_commands
from discord.ext import tasks

SERVER_ID = os.environ.get("SERVER_ID")
WEBHOOK = os.environ.get("WEBHOOK")
API_KEY = os.environ.get("API_KEY")
IMAGE_PATH = 'images' if platform.system() == 'Windows' else os.environ.get("IMAGE_PATH")
AUDIO_PATH = 'audio' if platform.system() == 'Windows' else os.environ.get("AUDIO_PATH")

available_sounds = {}
available_images = {}

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.slyced = False
        

    async def on_ready(self):
        await tree.sync(guild=discord.Object(id=SERVER_ID))

        self.session = aiohttp.ClientSession()
        
        self.synced = True
        print("Bot is online")

        # load images and audios into bot
        await asyncio.tasks.gather(populate_available_images(), populate_available_sounds())
        print("Sounds and images ready")
        
    async def on_member_join(self, member):
        guild = member.guild
        role = discord.utils.get(guild.roles, name="Plebs")

        try:
            await member.add_roles(role)
        except discord.HTTPException:
            await guild.system_channel.send(f'Deus não conseguiu categorizar o estatuto de {member.name}')

    async def on_message_delete(self, message):
        try:
            file = discord.File(available_images['delete'])
            await message.channel.send(content=message.author.mention, file=file)
        except FileNotFoundError | discord.HTTPException | discord.Forbidden | ValueError | TypeError:
            pass

    async def on_message_edit(self, message_before, message_after):
        if len(message_before.embeds) >= len(message_after.embeds) :
            try:
                file = discord.File(available_images['delete'])
                await message_before.channel.send(content=message_before.author.mention, file=file)
            except FileNotFoundError | discord.HTTPException | discord.Forbidden | ValueError | TypeError:
                pass


bot = commands.Bot(command_prefix="?", intents=discord.Intents.default())
bot = MyBot()
tree = app_commands.CommandTree(bot)

@tree.command(name="ping", description="Ping", guild=discord.Object(id=SERVER_ID))
async def self(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong in system: {platform.system()}")


@tree.command(name="disconnect", description="Disconnect from channel", guild=discord.Object(id=SERVER_ID))
async def self(interaction: discord.Interaction):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if voice_client != None:
        await voice_client.disconnect()

    await interaction.response.send_message("Disconnected")


@tree.command(name="list", description="List available sounds", guild=discord.Object(id=SERVER_ID))
async def self(interaction: discord.Interaction):
    
    await populate_available_sounds()
    
    return_message = "Available sounds:\n"

    for key, value in available_sounds.items():
        value = str(value).strip("}{'").replace(".mp3", "")
        return_message += f"{key}- {value}\n"

    await interaction.response.send_message(return_message)


@tree.command(name="save", description="Submit a sound file", guild=discord.Object(id=SERVER_ID))
async def self(interaction: discord.Interaction, attachment: discord.Attachment):
    if platform.system() == 'Windows':
        await interaction.response.send_message("Wait for the bot to be deployed in the server")
        return

    if attachment.content_type == "audio/mpeg":
        await attachment.save(os.path.join(AUDIO_PATH, attachment.filename))
        await interaction.response.send_message("Saved!")
    else:
        await interaction.response.send_message("Broken file, must be of audio type.")


@tree.command(name="trolagem", description="Send the bot to play a sound on another channel", guild=discord.Object(id=SERVER_ID))
async def self(interaction: discord.Interaction, channel: discord.VoiceChannel, audio: int):
    
    audio_name = str(available_sounds.get(audio)).strip("}{'")
    if audio_name == 'None':
        await interaction.response.send_message(f"Sound with number {audio} not found.")
        return
    
    target_channel = discord.utils.get(interaction.guild.voice_channels, name=channel.name)
    
    if target_channel is not None:
        voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        
        if voice_client is None:
            voice_client = await target_channel.connect()
        
        if target_channel.id != voice_client.channel.id:
            await voice_client.disconnect()
            voice_client = await target_channel.connect()

        audio_source = discord.FFmpegPCMAudio(os.path.join(AUDIO_PATH, audio_name))
        
        try:
            voice_client.play(audio_source)
            await interaction.response.send_message(f"Playing {audio_name.replace('.mp3', '')} on {channel}")
        except discord.errors.ClientException:
            await interaction.response.send_message(f"An audio is already playing")

        # with await we cease control to the event loop so other commands can be run
        while voice_client.is_playing():
            await asyncio.sleep(.1)
        
        await voice_client.disconnect()
    else:
        await interaction.channel.send("Target channel not found")


@tree.command(name="play", description="Play a sound", guild=discord.Object(id=SERVER_ID))
async def self(interaction: discord.Interaction, audio: int):

    audio_name = str(available_sounds.get(audio)).strip("}{'")
    if audio_name == 'None':
        await interaction.response.send_message(f"Sound with number {audio} not found.")
        return
        
        
    voice = interaction.user.voice
    if voice is None:
        await interaction.channel.send("You are not connected to a voice channel")
        return

    voice_channel = voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client is None:
        voice_client = await voice_channel.connect()

    audio_file = os.path.join(AUDIO_PATH, audio_name)
    audio_source = discord.FFmpegPCMAudio(audio_file)

    try:
        voice_client.play(audio_source)
        await interaction.response.send_message(f"Playing sound: {audio_name.replace('.mp3', '')}")
    except discord.errors.ClientException:
        await interaction.response.send_message(f"An audio is already playing")
        

@tree.command(name="whoami", description="Who am I", guild=discord.Object(id=SERVER_ID))
async def self(interaction: discord.Interaction):
    await interaction.response.send_message("https://www.youtube.com/watch?v=NUYvbT6vTPs")

async def populate_available_sounds():
    i = 1
    for file in os.listdir(AUDIO_PATH):
        available_sounds[i] = {file}
        i += 1

async def populate_available_images():
    available_images['delete'] = IMAGE_PATH + "/delete.jpg"
    # add more if needed

bot.run(API_KEY)

# TODO
# play a song selecting it with emoji reactions
# /save restrict file size
# play/download YT links
# if the bot is connected and is called on another channel it doesnt change channel