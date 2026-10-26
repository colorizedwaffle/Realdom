import hikari
import lightbulb
import os

bot=hikari.GatewayBot( #creates the bot
 intents=hikari.Intents.ALL,
 token=os.environ["bottoken"] 
)

client=lightbulb.client_from_app(bot) #sets up lightbulb

bot.subscribe(hikari.StartingEvent, client.start) #links hikari and lightbulb
