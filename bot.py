import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
import toml

config = toml.load('config.toml')
discord_token = config['token']
youtube_url = config['youtube_url']
channel_id = int(config['channel_id'])

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        super().__init__(command_prefix='/', intents=intents)

    async def on_ready(self):
        print("Bot is ready.")
        channel = self.get_channel(channel_id)
        if channel:
            await self.connect_and_play(channel)

    async def connect_and_play(self, channel):
        vc = await channel.connect()
        while not self.is_closed():
            try:
                with YoutubeDL({'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True}) as ydl:
                    info = ydl.extract_info(youtube_url, download=False)
                    url = info['formats'][0]['url'] if info['formats'] else None
                if url:
                    vc.play(FFmpegPCMAudio(url, **{'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}))
                    await self.wait_until_disconnected(vc)
                else:
                    print("No valid audio format found, retrying in 10 seconds...")
                    await asyncio.sleep(10)
            except Exception as e:
                print(f"Error occurred: {e}")
                await asyncio.sleep(5)  # Wait before retrying to handle temporary issues

    async def wait_until_disconnected(self, vc):
        while vc.is_playing() or vc.is_paused():
            await asyncio.sleep(1)
        print("Disconnected, reconnecting...")
        await vc.disconnect()

bot = MusicBot()
bot.run(discord_token)
