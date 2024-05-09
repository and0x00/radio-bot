import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
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
                with YoutubeDL({'format': 'bestaudio/best', 'noplaylist': 'True'}) as ydl:
                    info = ydl.extract_info(youtube_url, download=False)
                    url = info['formats'][0]['url']
            except Exception as e:
                print(f"Error extracting info: {e}")
                await asyncio.sleep(5)
                continue

            vc.play(FFmpegPCMAudio(url, **{'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}))
            while True:
                if not vc.is_playing():
                    vc.stop()
                    await vc.disconnect()
                    vc = await channel.connect()
                    vc.play(FFmpegPCMAudio(url, **{'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}))
                await asyncio.sleep(1)

bot = MusicBot()
bot.run(discord_token)
