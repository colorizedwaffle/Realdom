import hikari
#other files in the bot V
from botstorage import bot
from storage import load
import webserver

storefiles=["lastchannel", "defaultroles", "auditchannels"] #stores dictionaries connected to .json files

for file in storefiles: #loads files
 load(f"{file}")

import botcommands #registers commands with discord

webserver.keepalive()
bot.run() #starts the bot
