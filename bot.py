import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
import toml

# Carregar configurações do arquivo TOML
config = toml.load('config.toml')
discord_token = config['token']
youtube_url = config['youtube_url']
channel_id = int(config['channel_id'])

# Configurações do FFMPEG
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Configurações do YoutubeDL
ydl_options = {
    'format': 'bestaudio/best',
    'noplaylist': 'True'
}

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        super().__init__(command_prefix='/', intents=intents)
        self.voice_client = None

    async def on_ready(self):
        print("Bot is ready.")
        channel = self.get_channel(channel_id)
        if channel:
            print(f"Found the voice channel with ID: {channel_id}. Attempting to connect to: {channel.name}.")
            await self.connect_and_monitor(channel)
        else:
            print(f"Could not find the voice channel with ID: {channel_id}. Please check the configuration.")

    async def connect_and_monitor(self, channel):
        # Always stay connected to the specified channel
        try:
            self.voice_client = await channel.connect()
            print(f"Connected to the voice channel: {channel.name}.")
        except discord.errors.ClientException as e:
            print(f"ClientException: {e}")
        except discord.errors.Forbidden as e:
            print(f"Forbidden: Lack of permission to connect to the voice channel: {e}")
        except Exception as e:
            print(f"Error connecting to the voice channel: {e}")
            return

        # Monitor continuously to start/stop playing based on the presence of others
        while not self.is_closed():
            try:
                # Check if there are other members in the voice channel besides the bot
                if len(channel.members) > 1:  # Bot + at least one other person
                    try:
                        with YoutubeDL(ydl_options) as ydl:
                            info = ydl.extract_info(youtube_url, download=False)
                            url = info['formats'][0]['url']

                        # Start playing if not already playing
                        if not self.voice_client.is_playing():
                            self.voice_client.play(FFmpegPCMAudio(url, **ffmpeg_options))
                            print("Music started playing.")

                        # Continue playing while there are other members in the channel
                        while self.voice_client.is_playing() and len(channel.members) > 1:
                            await asyncio.sleep(1)

                    except Exception as e:
                        print(f"Error playing music (likely a 403 or connection issue): {e}")
                        await asyncio.sleep(10)

                else:
                    # Stop playing if no one else is in the channel
                    if self.voice_client.is_playing():
                        print("No one else in the voice channel, stopping music.")
                        self.voice_client.stop()

                # Check presence every second
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Error monitoring the voice channel: {e}")
                await asyncio.sleep(10)

bot = MusicBot()
bot.run(discord_token)
