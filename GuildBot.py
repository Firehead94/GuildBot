import discord
import asyncio
import json
import os
import sys
import re
from configparser import ConfigParser

from discord.ext import commands

configfile = 'GuildBot.ini'

config = ConfigParser()
config.read(configfile)
DISCORD_TOKEN = config.get('main', 'discord_token')
DISCORD_PREFIX = config.get('main', 'discord_prefix')
DISCORD_ADMINS = str(config.get('main', 'discord_admin')).split(',')
BOT_STATUS = 'Raid Assist'

class DiscordBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        try:
            with open('settings.json') as file:
                self.settings = json.load(file)
            self.channel = self.settings['channel']
            self.roles = self.settings['roles']
            self.reset = self.settings['reset']
            self.start = self.settings['start']
        except:
            with open('settings.json', 'w') as file:
                json.dump({},file,indent=4)
            self.settings = {
                'channel':'',
                'roles':{},
                'reset':'',
                'start':''
            }
            self.channel = ''
            self.roles = {}
            self.reset = ''
            self.start = ''
        super().__init__(*args, **kwargs)

    def save(self):
        with open('settings.json', 'w') as file:
            json.dump(self.settings, file, indent=4)
        self.reload()

    def reload(self):
        with open('settings.json') as file:
            self.settings = json.load(file)
        self.channel = self.settings['channel']
        self.roles = self.settings['roles']
        self.reset = self.settings['reset']
        self.start = self.settings['start']

    async def on_ready(self):
        print("----------------------------------------")
        print('Welcome to GuildBot for Discord')
        print("----------------------------------------")
        print("Logged in as: "+self.user.name)
        print("User ID: "+str(self.user.id))
        print('Prefix: '+DISCORD_PREFIX)
        activity = discord.Game(BOT_STATUS)
        await self.change_presence(status=discord.Status.online, activity=activity)

discordbot = DiscordBot(command_prefix=DISCORD_PREFIX)


async def is_admin(ctx):
    if str(ctx.message.author.id) in DISCORD_ADMINS:
        return True
    return False


@discordbot.command(name="setchannel")
@commands.check(is_admin)
async def setchannel(ctx):
    discordbot.settings['channel'] = str(ctx.channel.id)
    discordbot.save()


@discordbot.command(name="reset")
@commands.check(is_admin)
async def reset(ctx, emote):
    discordbot.settings['reset'] = str(emote)
    discordbot.save()


@discordbot.command(name="add")
@commands.check(is_admin)
async def add(ctx, emote, role):
    discordbot.settings['roles'][str(emote)] = str(role)
    discordbot.save()


@discordbot.command(name='remove')
@commands.check(is_admin)
async def remove(ctx, emote):
    del discordbot.settings['roles'][str(emote)]
    discordbot.save()


@discordbot.command(name='start')
@commands.check(is_admin)
async def start(ctx, role):
    discordbot.settings['start'] = str(role)
    discordbot.save()

@discordbot.command(name='count')
async def count(ctx, role_mention):
    try:
        role_mention = role_mention.strip()
        role_id = role_mention[3:-1]
        role = discord.utils.get(ctx.guild.roles, id=int(role_id))
        await ctx.send('There are {} {} players in the discord'.format(len(role.members), role.name))
    except:
        await ctx.send('**ERROR** make sure to mention the role.')

@discordbot.event
async def on_member_join(member):
    await member.add_roles(discord.utils.get(member.guild.roles, id=int(discordbot.start)))


@discordbot.event
async def on_raw_reaction_add(payload):
    if str(payload.user_id) == str(discordbot.user.id):
        pass
    else:
        if str(payload.channel_id) == str(discordbot.channel):
            guild = discordbot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            if str(payload.emoji.id) == discordbot.settings['reset']:
                for emote in message.reactions:
                    if str(emote.emoji.id) is not discordbot.reset:
                        try:
                            await member.remove_roles(discord.utils.get(guild.roles, id=int(discordbot.roles[str(emote.emoji.id)])))
                        except:
                            pass
                for emote,role_id in discordbot.roles.items():
                    try:
                        await message.remove_reaction(discord.utils.get(guild.emojis, id=int(emote)), member)
                    except:
                        pass
                await message.remove_reaction(discord.utils.get(guild.emojis, id=int(discordbot.settings['reset'])), member)
            else:
                await member.add_roles(discord.utils.get(guild.roles, id=int(discordbot.roles[str(payload.emoji.id)])), reason="Auto Assign")


async def mainDiscord(bot):
    await bot.login(DISCORD_TOKEN)
    await bot.connect()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(mainDiscord(discordbot))
        loop.run_forever()
    except discord.LoginFailure:
        print('GuildBot Failed to Login: Invalid Credentials.\n'
              'This may be a temporary issue, consult Discords\n'
              'Login Server Status before attemping again.\n'
              'If servers are working properly, you may need\n'
              'a new token. Please replace the token in the\n'
              'GuildBot.ini file with a new token.\n')
    except KeyboardInterrupt:
        loop.run_until_complete(discordbot.logout())
    except Exception as e:
        print("Fatal exception, attempting graceful logout.\n{}".format(e))
        loop.run_until_complete(discordbot.logout())
    finally:
        loop.close()
        exit(1)