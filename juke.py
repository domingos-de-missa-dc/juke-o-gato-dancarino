#
#   Author: fmfarto @ GitHub
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

serverId= os.environ.get("SERVER_ID")

audioPath = 'audio' if platform.system() == 'Windows' else os.environ.get("AUDIO_PATH")

bot = commands.Bot(command_prefix="?", intents=discord.Intents.default())

availableSounds = {}

class myBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.slyced = False
        

    async def on_ready(self):
        await tree.sync(guild=discord.Object(id=serverId))

        # might be overkill for a request a day, but will enable us to make more requests to the Webhook if there are some interesting ideas to be done
        # or even fetch some API data for some interesting stuff
        self.session = aiohttp.ClientSession()
        
        self.synced = True
        print("Bot is online")

        await pupulateAvailableSounds()
        print("Sound list ready")
        
        self.paymentReminder.start()

    @tasks.loop(hours=24.0)
    async def paymentReminder(self):
        """ Remind server that payment is pending from first day of the month until 6th """
        todaysDay = date.today().day
        payDay = 6
        if todaysDay >= 1 and todaysDay <= payDay:
            daysLeftToPay = payDay - todaysDay
            payload = {"username": "Autoridade Tributária", "content": "@here\nPaga o que deves!\nDias até o server morrer: " + str(daysLeftToPay) + ":fire:" + "\n", "embeds": [{"title": "Imposto", "color": 16777215, "description": "4.32€"}]}
            webhook_url = os.environ.get("WEBHOOK")
            await self.session.post(webhook_url, json=payload)  

    async def on_member_join(self, member):
        #guild = self.get_guild(int(serverId))
        guild = member.guild
        role = discord.utils.get(guild.roles, name="Plebs")

        try:
            await member.add_roles(role)
        except discord.HTTPException:
            await guild.system_channel.send(f'Deus não conseguiu categorizar o estatuto de {member.name}')

    async def on_message_delete(self, message):
        try:
            file = discord.File("images/delete.jpg")
            await message.channel.send(content=message.author.mention, file=file)
        except FileNotFoundError | discord.HTTPException | discord.Forbidden | ValueError | TypeError as ex:
            print(ex)

    async def on_message_edit(self, messageBefore, messageAfter):
        try:
            file = discord.File("images/delete.jpg")
            await messageBefore.channel.send(content=messageBefore.author.mention, file=file)
        except FileNotFoundError | discord.HTTPException | discord.Forbidden | ValueError | TypeError as ex:
            print(ex)

bot = myBot()
tree = app_commands.CommandTree(bot)

@tree.command(name="ping", description="Ping", guild=discord.Object(id=serverId))
async def self(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong in system: {platform.system()}")


@tree.command(name="disconnect", description="Disconnect from channel", guild=discord.Object(id=serverId))
async def self(interaction: discord.Interaction):
    voiceClient = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if voiceClient != None:
        await voiceClient.disconnect()

    await interaction.response.send_message("Disconnected")


@tree.command(name="list", description="List available sounds", guild=discord.Object(id=serverId))
async def self(interaction: discord.Interaction):
    
    await pupulateAvailableSounds()
    
    returnMessage = "Available sounds:\n"

    for key, value in availableSounds.items():
        value = str(value).strip("}{'").replace(".mp3", "")
        returnMessage += f"{key}- {value}\n"

    await interaction.response.send_message(returnMessage)

@tree.command(name="save", description="Submit a sound file", guild=discord.Object(id=serverId))
async def self(interaction: discord.Interaction, attachment: discord.Attachment):
    if platform.system() == 'Windows':
        await interaction.response.send_message("Wait for the bot to be deployed in the server")
        return

    if attachment.content_type == "audio/mpeg":
        await attachment.save(os.path.join(audioPath, attachment.filename))
        await interaction.response.send_message("Saved!")
    else:
        await interaction.response.send_message("Broken file, must be of audio type.")


@tree.command(name="trolagem", description="Send the bot to play a sound on another channel", guild=discord.Object(id=serverId))
async def self(interaction: discord.Interaction, channel: discord.VoiceChannel, audio: int):
    
    audioName = str(availableSounds.get(audio)).strip("}{'")
    if audioName == 'None':
        await interaction.response.send_message(f"Sound with number {audio} not found.")
        return
    
    targetChannel = discord.utils.get(interaction.guild.voice_channels, name=channel.name)
    
    if targetChannel != None:
        voiceClient = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        
        if voiceClient == None:
            voiceClient = await targetChannel.connect()
        
        if targetChannel.id != voiceClient.channel.id:
            await voiceClient.disconnect()
            voiceClient = await targetChannel.connect()

        audioSource = discord.FFmpegPCMAudio(os.path.join(audioPath, audioName))
        
        try:
            voiceClient.play(audioSource)
            await interaction.response.send_message(f"Playing {audioName.replace('.mp3', '')} on {channel}")
        except discord.errors.ClientException:
            await interaction.response.send_message(f"An audio is already playing")

        # with await we cease control to the event loop so other commands can be run
        while voiceClient.is_playing():
            await asyncio.sleep(.1)
        
        await voiceClient.disconnect()
    else:
        await interaction.channel.send("Target channel not found")


@tree.command(name="play", description="Play a sound", guild=discord.Object(id=serverId))
async def self(interaction: discord.Interaction, audio: int):

    audioName = str(availableSounds.get(audio)).strip("}{'")
    if audioName == 'None':
        await interaction.response.send_message(f"Sound with number {audio} not found.")
        return
        
        
    voice = interaction.user.voice
    if voice == None:
        await interaction.channel.send("You are not connected to a voice channel")
        return

    voiceChannel = voice.channel
    voiceClient = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voiceClient == None:
        voiceClient = await voiceChannel.connect()

    audioFile = os.path.join(audioPath, audioName)
    audioSource = discord.FFmpegPCMAudio(audioFile)

    try:
        voiceClient.play(audioSource)
        await interaction.response.send_message(f"Playing sound: {audioName.replace('.mp3', '')}")
    except discord.errors.ClientException:
        await interaction.response.send_message(f"An audio is already playing")
        

@tree.command(name="whoami", description="Who am I", guild=discord.Object(id=serverId))
async def self(interaction: discord.Interaction):
    await interaction.response.send_message("https://www.youtube.com/watch?v=NUYvbT6vTPs")

async def pupulateAvailableSounds():
    i = 1
    for file in os.listdir(audioPath):
        availableSounds[i] = {file}
        i += 1

bot.run(os.environ.get("API_KEY"))

# TODO
# refactor audio play code to be done in a sync function
# play a song selecting it with emoji reactions
# /save restrict file size
# play YT links
# if the bot is connected and is called on another channel it doesnt change channel
# venv
# pythonify the naming convention
# add command to replace default role on_member_join