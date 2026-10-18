import json
import hikari
from pathlib import Path

projectfolder= Path(__file__).resolve().parent #gets current code directory

datafolder=None
for path in projectfolder.rglob("jsonstore"): #gets directory for the .json files
 if path.is_dir():
  datafolder=path
  break
 
if datafolder==None:
 raise Exception("Data folder not found") #crashes the program if no datafolder is found

#dictionaries to store data
lastchannel={}
defaultroles={}
auditchannels={}
helpmessages={}

#hex codes for colour
GREEN=0x51F21B
RED=0xd9111f
ORANGE=0xFCAF08

#help buttons
helpback=hikari.impl.InteractiveButtonBuilder( #button to go back a page
 style=hikari.ButtonStyle.PRIMARY,
 custom_id="helpback",
 label="<"
)
helpforward=hikari.impl.InteractiveButtonBuilder( #button to go forward a page
 style=hikari.ButtonStyle.PRIMARY,
 custom_id="helpforward",
 label=">"
)
helpbackoff=hikari.impl.InteractiveButtonBuilder( 
 style=hikari.ButtonStyle.PRIMARY,
 custom_id="helpback",
 label="<"
).set_is_disabled(True) #disables button
helpforwardoff=hikari.impl.InteractiveButtonBuilder( 
 style=hikari.ButtonStyle.PRIMARY,
 custom_id="helpforward",
 label=">"
).set_is_disabled(True)

#help rows
backoff=hikari.impl.MessageActionRowBuilder() #has the backward button off
backoff.add_component(helpbackoff)
backoff.add_component(helpforward)

forwardoff=hikari.impl.MessageActionRowBuilder() #has the forward button off
forwardoff.add_component(helpback)
forwardoff.add_component(helpforwardoff)

allon=hikari.impl.MessageActionRowBuilder() #has both buttons on
allon.add_component(helpback)
allon.add_component(helpforward)

alloff=hikari.impl.MessageActionRowBuilder() #has both buttons off
alloff.add_component(helpbackoff)
alloff.add_component(helpforwardoff)

helprows={"backoff": backoff,"forwardoff": forwardoff,"allon": allon,"alloff": alloff}
 
def load(dictionary): #updates dictionaries to match .json files, dicitonary must be a string which is the name of an existing dictionary connected to a .json file
         #''' allow multi-line strings and allows you to use "" in the string
 runcode=f'''
global {dictionary}
global datafolder

jsonfile= datafolder / "{dictionary}.json" #opens the .json

with open (jsonfile, "r") as file: #with open is needed so the file closes once we're done
 {dictionary}=json.load(file)
          '''
 
 exec(runcode) #exec() runs a string as code

def writeto(dictionary): #updates .json files to match the dictionaries
 runcode=f'''
global {dictionary}
global datafolder

jsonfile= datafolder / "{dictionary}.json"

with open (jsonfile, "w") as file:
 json.dump({dictionary}, file, indent=1)
          '''
 
 exec(runcode)

helppages=[ #list of all help pages, with index 0 being page 1 
  ''' /help - takes you here
       >page - controls which page you land on
       >section - controls which section you land on
       
      /repeater - repeats whatever you input

      /diceroll - rolls a custom amount of custom die
       >highest - highest number on the di(c)e; min 1, default 20
       >dicecount - number of die; min 1, max 15 million, default 1
       >modifier - number added to total roll (can be negative); default 0

      /coinflip - flips (a) coin(s) with custom chances
       >count - number of coins to flip; min 1, max 20 million, default 1
       >chance - chance for a coin to land on heads; default 50
       >sp - chance expressed in the Limbus sp system; max 45, min -45 (optional)

      /userinfo - gives information about a user
       >user - target user
  ''',
  ''' /auditlog - sets the channel for audit messages
      >on - True or False, toggles audit messages
      >channel - required if on is True
       
      /joinroles - set roles added automatically
      >action - choose an action to perform
      >role - choose a role, required if you selected "add" or "remove"
       
      /mute - allows you to timeout a user
      >user - select a user to timeout
      >unit - select a unit (minutes, hours, etc.); selecting "check" will check if a user is currently timed out
      >amount - select the amount of units to timeout for; min 1, default 1
      >reason - input reason for mute (optional)
       
      /unmute - allows you to remove a user's timeout
      >user - select a user to unmute
      >reason - input reason for unmute (optional)
 ''',
 '''/ban - allows you to ban a user
     >user - target user
     >reason - reason for ban (optional)

    /banlist - returns a list of all banned users
    
    /unban - unbans a user
     >userid - user's id, requires id because they're not in the server
     >reason - reason for unban (optional)
    
    /clearmessages - deletes multiple messages in a channel
     >amount - number of messages to clear; min 1, max 100
     >user - only delete messages from 1 user (optional)
    
    /role - interacts with discord roles
     >mode - select an action to preform
     >target - select a target user
     >role - targeted role (optional if "check" was selected)
 '''  
]

sectiondict={"Regular":0, "Admin": 1} #contains page numbers for the start of each section, update when needed

