from discord import embeds
from discord.ext import commands
from yahoo_oauth import OAuth2
from playhouse.shortcuts import model_to_dict


import discord
import logging
import urllib3
import yahoo_api

from database.models import Guild


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

class Yahoo(commands.Cog):

    error_message = "I'm having trouble getting that right now please try again later"

    def __init__(self, bot, KEY, SECRET):
        self.bot = bot
        self.http = urllib3.PoolManager()
        self.KEY = KEY
        self.SECRET = SECRET
        self.yahoo_api = None
    
    async def cog_before_invoke(self, ctx):
        guild = Guild.get(Guild.guild_id == str(ctx.guild.id))
        self.yahoo_api = yahoo_api.Yahoo(OAuth2(self.KEY, self.SECRET, **model_to_dict(guild)), guild.league_id, guild.league_type)
        return
    
    @commands.command("standings")
    async def standings(self, ctx):
        logger.info("standings called")
        embed = self.yahoo_api.get_standings()
        if embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send(self.error_message)

    @commands.command("roster")
    async def roster(self, ctx, *, content:str):
        logger.info("roster called")
        roster = self.yahoo_api.get_roster(content)
        if roster:
            await ctx.send(embed=roster)
        else:
            await ctx.send(self.error_message)
        

    @commands.command("trade")
    async def trade(self, ctx):
        logger.info("trade called")
        latest_trade = self.yahoo_api.get_latest_trade()

        if latest_trade == None:
            await ctx.send("No trades up for approval at this time")
            return

        teams = self.yahoo_api.league().teams()

        trader = teams[latest_trade['trader_team_key']]
        tradee = teams[latest_trade['tradee_team_key']]
        managers = [trader['name'], tradee['name']]
        
        player_set0 = []
        player_set0_details = ""
        for player in latest_trade['trader_players']:
            player_set0.append(player['name'])
            api_details = self.yahoo_api.get_player_details(player['name'])["text"]+"\n"
            if api_details: 
                player_set0_details = player_set0_details + api_details
            else:
                await ctx.send(self.error_message)
                return

        player_set1 = []
        player_set1_details = ""
        for player in latest_trade['tradee_players']:
            player_set1.append(player['name'])
            api_details = self.yahoo_api.get_player_details(player['name'])["text"]+"\n"
            if api_details: 
                player_set1_details = player_set1_details + api_details
            else:
                await ctx.send(self.error_message)
                return

            confirm_trade_message = "{} sends {} to {} for {}".format(managers[0],', '.join(player_set0),managers[1],', '.join(player_set1))
            announcement = "There's collusion afoot!\n"
            embed = discord.Embed(title="The following trade is up for approval:", description=confirm_trade_message, color=0xeee657)
            embed.add_field(name="{} sends:".format(managers[0]), value=player_set0_details, inline=False)
            embed.add_field(name="to {} for:".format(managers[1]), value=player_set1_details, inline=False)
            embed.add_field(name="Voting", value=" Click :white_check_mark: for yes, :no_entry_sign: for no")
            msg = await ctx.send(content=announcement, embed=embed)    
            yes_emoji = '\U00002705'
            no_emoji = '\U0001F6AB'        
            await msg.add_reaction(yes_emoji)
            await msg.add_reaction(no_emoji)


    @commands.command("stats")
    async def stats(self, ctx,  *, content:str):
        logger.info("player_details called")
        details = self.yahoo_api.get_player_details(content)
        if details:
            await ctx.send(embed=details['embed'])
        else:
            await ctx.send("Player not found")


    @commands.command("matchups")
    async def matchups(self,ctx):
        embed = self.yahoo_api.get_matchups()
        if embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send(self.error_message)