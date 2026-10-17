""" discord bot token, used to create the bot V
    MTUyNDEyNjkxMDU4NDcyMTQ4OA.Gk6j3E.rgv2b6aFvDZ7JD75vjVdbzxPcqy98RGaotP8t8
"""
import hikari
import lightbulb

bot=hikari.GatewayBot( #creates the bot
 intents=hikari.Intents.ALL,
 token="MTUyNDEyNjkxMDU4NDcyMTQ4OA.Gk6j3E.rgv2b6aFvDZ7JD75vjVdbzxPcqy98RGaotP8t8"
)

client=lightbulb.client_from_app(bot) #sets up lightbulb

bot.subscribe(hikari.StartingEvent, client.start) #links hikari and lightbulb
