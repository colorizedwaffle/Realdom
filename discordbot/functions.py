import hikari
import random
#other files in the bot V
from storage import lastchannel, defaultroles, auditchannels, helppages, sectiondict, writeto, RED, GREEN, ORANGE
from botstorage import bot

async def fixauditchannel(guildid): #guildid should be a string
 global auditchannels
 global lastchannel
 
 del auditchannels[guildid] #deletes guild key and missing channel
 writeto("auditchannels")

 if guildid in lastchannel: 
  try: #sends a message to inform the user
   channelid=int(lastchannel[guildid])
   channel=await bot.rest.fetch_channel(channelid)
   
   embed=hikari.Embed(
    title="**Audit Channel Missing**",
    description="Audit log messages will no longer be sent",
    color=RED
   )
   embed.set_footer("set a new audit channel using /auditlog")
   await channel.send(embed)
   
  except hikari.NotFoundError: #if last channel is also missing
   del lastchannel[guildid]
   writeto("lastchannel")

async def fixdefaultroles(guildid,missingroles): #guildid should be a string and missingroles should be a list
 global defaultroles
 global auditchannels
 global lastchannel
 
 for role in missingroles: 
  x=defaultroles[guildid].index(str(role)) #gets position of missing role
  defaultroles[guildid].pop(x) #deletes mising role
 
 if not defaultroles[guildid]: #deletes guild key if there are no roles
  del defaultroles[guildid]
  
 writeto("defaultroles")

 if guildid in auditchannels:
  channelid=int(auditchannels[guildid])
  channel=await bot.rest.fetch_channel(channelid)
  
  embed=hikari.Embed(
   title="**On Join Role(s) Missing**",
   description="Missing role(s) will no longer be added automatically",
   color=RED
  )
  embed.set_footer("set a new on join role or check current on join roles using /joinroles")
  await channel.send(embed)

 elif guildid in lastchannel:
  try:
   channelid=int(lastchannel[guildid])
   channel=await bot.rest.fetch_channel(channelid)
   
   embed=hikari.Embed(
    title="**On Join Role(s) Missing**",
    description="Missing role(s) will no longer be added automatically",
    color=RED
   )
   embed.set_footer("set a new on join role or check current on join roles using /joinroles")
   await channel.send(embed)
  
  except hikari.NotFoundError:
   del lastchannel[guildid]
   writeto("lastchannel")
    
async def savenewdefaultrole(guildid, roleid, deloradd):
 global defaultroles
 
 if deloradd=="add": #adding a role
  if guildid in defaultroles: #checks if server has any roles assigned
   if roleid in defaultroles[guildid]: #Checks if the role is already assigned
    return ["Role already added", True] #'True' makes the message ephemeral later
   
   defaultroles[guildid].append(roleid)
    
  else: #creates a new list if there is no roles assigned
   defaultroles[guildid]=[]
   defaultroles[guildid].append(roleid)
 
 elif deloradd=="remove": #removing a role
  if not guildid in defaultroles: 
   return ["No roles assigned to this server", True]
  
  if not roleid in defaultroles[guildid]: 
   return ["No role found", True]
  
  x=defaultroles[guildid].index(roleid) #finds the position of the role id, starting at 0
  defaultroles[guildid].pop(x) #removes the role
  
  if not defaultroles[guildid]:
   del defaultroles[guildid]
    
 elif deloradd=="check": #checking all roles
  if not guildid in defaultroles:
   return ["No roles assigned to this server", False]
  
  async def getrolenames(guildid): #gets name of the roles instead of the role's id
   allroles=[] #empty list to store all role names
   x=0 #amount of missing roles
   
   for roleid in defaultroles[guildid]: #loops through all assigned roles
    try:
     role= await bot.rest.fetch_role(int(guildid),int(roleid)) #gets the role object from the id
     allroles.append(role.name)
    except hikari.NotFoundError: #if role is missing
     n=defaultroles[guildid].index(roleid) 
     defaultroles[guildid].pop(n) #deletes missing role
     x+=1
   
   if x>0:
    allroles.append(f"**{x} Missing role(s)**")
   allroles=", ".join(allroles) #prints list without brackets, seperated by a comma and a space
   return allroles
  
  allroles=await getrolenames(guildid)
  return [f"Current on-join roles:\n{allroles}", False]
 
 writeto("defaultroles")
 
 role= await bot.rest.fetch_role(int(guildid), int(roleid))
 if deloradd=="add":
  return [f"'{role}' added successfully", False]
 else:
  return [f"'{role}' removed successfully", False]

def helpdisplay(page):
 global helppages
 reversesectiondict={(0,0):"Regular",(1,2):"Admin"}
 sectioncolours={"Regular": GREEN, "Admin": ORANGE} #contains colours for each section, update as needed
 sections=["Regular","Admin"] #list of sections, update as needed

 for (start,end),section in reversesectiondict.items(): #loops through sections and assigns them
  if page>=start and page<=end:
   currentsection=section
 
 displaypage=page+1
 embed=hikari.Embed(
   title=f"**{currentsection} Commands**",
   description=helppages[page],
   color=sectioncolours[currentsection]
  )
 embed.set_footer(f"page {displaypage}")

 return embed

def dice(highest,dicecount,modifier):
 result=[] #empty list to store all rolls
 total=0

 for i in range(dicecount): #gets rolls
  roll=random.randint(1,highest)
  total+=roll

  if len(result)<5: #avoids storing every roll by only storing the first 5
   result.append(roll)
   
 addmodifier=total+modifier
 
 messageparts=[] #list to store relevant message components
 
 #appends all message components
 if len(result)==1: #says just "rolled" if there's only 1
  messageparts.append(f"Dice: 1 d{highest}(s)")
  messageparts.append(f"Rolled: {result[0]}")
 else: #if there's more than 1 die
  
  x=", ".join(str(i) for i in result) #str(i) is needed cause .join doesn't work on integers for some reason
  messageparts.append(f"Die: {dicecount} d{highest}")
  
  if dicecount<=5: #says "all rolls" if there's only 5
   messageparts.append(f"All rolls: {x}")
  else: #says "first 5 rolls" if there's more than 5
   messageparts.append(f"First 5 rolls: {x}")
   
  messageparts.append(f"Total: {total}") #appends total
  
 if modifier!=0: #appends modifier total if there's a modifier
  messageparts.append(f"With Modifier: {addmodifier}")
 
 message=",\n".join(messageparts)
 return message

def coins(count,chance,sp):
 first5=[] #stores first 5 coins
 result=[0,0] #stores number of times it hit heads and tails, respectively

 for i in range(count):
  number=random.randint(1,100)
  if number>chance: #if it hits tails
   result[1]+=1
   if len(first5)<5:
    first5.append("Tails")
  
  else: #if it hits heads
   result[0]+=1
   if len(first5)<5:
    first5.append("Heads")

 formatted=", ".join(first5)
 if count==1: #cuts out extra parts if there's only 1
  message=f"{first5[0]}"
 elif count<=5: #cuts out extra parts if there's <5
  message=f"All coins: {formatted}"
 else:
  message=f"{result[0]} Heads, {result[1]} Tails, {count} total coins,\nFirst 5 coins: {formatted}"

 messagechance=[message] #stores message and heads chance/sp is later appended
 if not sp: #if sp wasn't selected
  messagechance.append(f"{chance}% chance to hit heads")
 if sp:
  spvalue=chance-50
  messagechance.append(f"{spvalue} sp")

 formatted="; ".join(messagechance)
 return formatted
