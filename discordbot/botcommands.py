import hikari
import lightbulb
import random
from datetime import datetime, timedelta, timezone
#other files in the bot V
from functions import fixauditchannel, savenewdefaultrole, fixdefaultroles, helpdisplay, dice, coins
from storage import lastchannel, defaultroles, auditchannels, helpmessages, helppages, helprows, sectiondict, writeto, GREEN, RED, ORANGE
from botstorage import bot, client

                               #>---Prehooks---<

@client.error_handler #replies with a message if user does not have admin perms
async def error_handler(exc: lightbulb.exceptions.ExecutionPipelineFailedException):
 error=exc.__cause__ or exc #gets error cause

 if isinstance(error, lightbulb.prefab.checks.MissingRequiredPermission):
  await exc.context.respond("Admin permissions required", ephemeral=True) #makes the message only show for the user who invoked the command
  return True #flags the error as resolved                

 return False #flags the error as unresolved

@lightbulb.hook(lightbulb.ExecutionSteps.PRE_INVOKE) #saves the last channel where the bot was used
async def save_last_channel(_: lightbulb.ExecutionPipeline, ctx: lightbulb.Context):
 global lastchannel
 guildid=str(ctx.guild_id)
 channelid=str(ctx.channel_id)
 
 if guildid in lastchannel and lastchannel[guildid]==channelid: #checks if channel is already stored
  return
    
 lastchannel[guildid]=channelid
 
 writeto("lastchannel")
                               #>---Commands---<

@client.register #registers the command, so it shows up when you type "/"
class repeater(lightbulb.SlashCommand, name="repeater", description="repeats what you say", hooks=[save_last_channel]):
 text=lightbulb.string("text", "Text to repeat") #creates an option
 
 @lightbulb.invoke #invokes command, underneath is the actual logic behind it
 async def invoke(self,ctx: lightbulb.Context):
  await ctx.respond(self.text)
   

@client.register
class Help(lightbulb.SlashCommand, name="help", description="lists all commands", hooks=[save_last_channel]):
 page=lightbulb.integer("page", "Page number", default=None, min_value=1)
 section=lightbulb.string("segment", "segment to jump to", default=None,
  choices=[
   lightbulb.Choice(name="Regular", value="Regular"),
   lightbulb.Choice(name="Admin", value="Admin")
  ]
 )
 
 @lightbulb.invoke
 async def invoke(self,ctx: lightbulb.Context):
  global sectiondict
  global helpinfo
  global helppages
  global helpmessages
  global helprows
  
  helpinfo={ #stores info needed for help buttons, cuts down on globals
  "updatedpage": 0,
  "helpuser": 0,
  "maxpages": 0,
  }
  helpinfo["helpuser"]=ctx.user.id
  helpinfo["maxpages"]=len(helppages)
  
  if self.page==None: #if a page wasn't selected
   
   if self.section==None: #if a segment wasn't selected
    updatedpage=0 #updated page is 0 indexed, sets it to the first page
   else: #if a segment was selected
    updatedpage=sectiondict[self.section]
  
  elif self.page>helpinfo["maxpages"]: #if the user selected a page above the max
   await ctx.respond(f"There are only {helpinfo['maxpages']} pages", ephemeral=True)
   return
  
  else: #if page was entered correctly
   updatedpage=self.page-1
  
  helpinfo["updatedpage"]=updatedpage

  embed=helpdisplay(updatedpage)
  
  response=await ctx.respond(embed,components=[helprows["allon"]])
  
  message=await ctx.fetch_response(response) #gets id for the response
  
  guildid=str(ctx.guild_id)
  helpmessages[guildid]=str(message.id) #overwrites the last help message
  
@bot.listen(hikari.InteractionCreateEvent) #listens for interaction with help buttons
async def help_handler(event: hikari.InteractionCreateEvent):
 global helpinfo
 global helpmessages
 global helprows

 if not isinstance(event.interaction, hikari.ComponentInteraction): #if the event isn't a button press
  return

 guildid=str(event.interaction.guild_id)
 try:
  if guildid in helpmessages:
   rootmessageid=str(event.interaction.message.id) #gets the id of the message the button is attached to
   if rootmessageid!=helpmessages[guildid]: #if this isn't the most recent help message
    await event.interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE,components=[helprows["alloff"]]) #disables all buttons
    return
  
 except NameError: #if helpuser doesn't exist, it means that the help message wasn't run in this instance
  await event.interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE,components=[helprows["alloff"]])
  return
  
 currentuser=event.interaction.user.id
 if currentuser!=helpinfo["helpuser"]: #if the user clicking the button is not the one who invoked the command
  await event.interaction.create_initial_response(hikari.ResponseType.MESSAGE_CREATE,"This is not your help message",flags=hikari.MessageFlag.EPHEMERAL)
  return

 if event.interaction.custom_id=="helpback":
  if helpinfo["updatedpage"]<=0: #turns off back button if it's the first page
   helpinfo["updatedpage"]=0 #resets the updatedpage to 0 in case it's negative
    
   await event.interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE,components=[helprows["backoff"]]) #updates message to have the back button off
   return
  
  helpinfo["updatedpage"]-=1
  embed=helpdisplay(helpinfo["updatedpage"])
  await event.interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE,content=embed,components=[helprows["allon"]])
 
 elif event.interaction.custom_id=="helpforward":
  max0index=helpinfo["maxpages"]-1 #gets the max page but 0 indexed, i.e: 2 pages = 1 max0index
  if helpinfo["updatedpage"]>=max0index:
   helpinfo["updatedpage"]=max0index #resets the updatedpage to max in case it's over it
   
   await event.interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE,components=[helprows["forwardoff"]]) #updates message to have the back button off
   return
  
  helpinfo["updatedpage"]+=1
  embed=helpdisplay(helpinfo["updatedpage"])
  await event.interaction.create_initial_response(hikari.ResponseType.MESSAGE_UPDATE,content=embed,components=[helprows["allon"]])


@client.register
class diceroll(lightbulb.SlashCommand, name="diceroll", description="roll di(c)e",hooks=[save_last_channel]): 
 highest=lightbulb.integer("highest","Highest number on dice", min_value=1, default=20)
 count=lightbulb.integer("dicecount","Amount of dice", min_value=1, max_value=10_000, default=1)
 mod=lightbulb.integer("modifier","Modifier to add to total (can be negative)", default=0)

 @lightbulb.invoke
 async def invoke(self, ctx:lightbulb.Context):
  await ctx.defer()

  reply=dice(self.highest,self.count,self.mod)

  await ctx.respond(reply)

@client.register
class coinflip(lightbulb.SlashCommand, name="coinflip", description="flips (a) coin(s)",hooks=[save_last_channel]):
 count=lightbulb.integer("count","Number of coins to flip",min_value=1,max_value=20_000,default=1)
 chance=lightbulb.integer("chance","%Chance to hit heads",default=50)
 sp=lightbulb.integer("sp","Chance described as Limbus sp",max_value=45,min_value=-45,default=None)

 @lightbulb.invoke
 async def invoke(self, ctx:lightbulb.Context):
  await ctx.defer()

  sptoggle=False
  if self.sp!=None: #if sp was selected
   updatedchance=50+self.sp #sp overwrites chance
   sptoggle=True
  else:
   updatedchance=self.chance
  
  reply=coins(self.count,updatedchance,sptoggle)

  await ctx.respond(reply)

@client.register
class userinfo(lightbulb.SlashCommand, name="userinfo", description="reveals information about a user",hooks=[save_last_channel]):
 target=lightbulb.user("user","Target user", default=None)

 @lightbulb.invoke
 async def invoke(self, ctx:lightbulb.Context):
  guildid=ctx.guild_id
  
  if self.target==None:
   newtarget=ctx.user
  else:
   newtarget=self.target
   
  member=await bot.rest.fetch_member(guildid,newtarget)
  
  isbot="This user is not a bot"
  if member.is_bot:
   isbot="This user is a bot"
   
  embed=hikari.Embed(
   title=f"{member.username} Info:",
   description=f"User id: {member.id}\nUsername: {member.username}\nServer nickname: {member.nickname}"
  )
  embed.set_footer(isbot)
  embed.set_image(member.display_avatar_url)

  await ctx.respond(embed)

@client.register
class probability(lightbulb.SlashCommand, name="probability", description="calculates probability of multiple events",hooks=[save_last_channel]):
 amount=lightbulb.integer("amount","amount of events to calculate",min_value=1,max_value=10)
 
 p1=lightbulb.string("probability_1","chance for first event; fraction split up by '/'; ex. 1/10")
 p2=lightbulb.string("probability_2","chance for second event; fraction split up by '/'; ex. 1/5",default=None)
 p3=lightbulb.string("probability_3","chance for third event; fraction split up by '/'; ex. 3/10",default=None)
 p4=lightbulb.string("probability_4","chance for fourth event; fraction split up by '/'; ex. 2/5",default=None)
 p5=lightbulb.string("probability_5","chance for fifth event; fraction split up by '/'; ex. 1/2",default=None)
 p6=lightbulb.string("probability_6","chance for sixth event; fraction split up by '/'; ex. 3/5",default=None)
 p7=lightbulb.string("probability_7","chance for seventh event; fraction split up by '/'; ex. 7/10",default=None)
 p8=lightbulb.string("probability_8","chance for eigth event; fraction split up by '/'; ex. 4/5",default=None)
 p9=lightbulb.string("probability_9","chance for ninth event; fraction split up by '/'; ex. 9/10",default=None)
 p10=lightbulb.string("probability_10","chance for tenth event; fraction split up by '/'; ex. 10/10",default=None)

 @lightbulb.invoke
 async def invoke(self, ctx:lightbulb.Context):
  fractions=[self.p1,self.p2,self.p3,self.p4,self.p5,self.p6,self.p7,self.p8,self.p9,self.p10] #stores all fraction chances
  decimals=[] #empty list to store self.amount decimal chances
  count=0 #tracks number of times the for loop was run
  
  for i in fractions: #ensures fractions are created properly, and turns them into decimals
   count+=1
   if count>self.amount: #stops loop once enough options were sorted through
    break
   
   if i==None: #if one of the choices was left empty
    await ctx.respond(f"Make sure to fill out {self.amount} probabilities in order")
    return
   
   markers=["/",".",",","?",">","<"] #accepted seperator characters (incase of typos)
   for marker in markers:
    split=i.split(marker)
    if len(split)==2: #if they didn't input 2 numbers
     break
    
   if len(split)!=2: #if they didn't input 2 numbers with any seperator
    await ctx.respond("Input 2 numbers seperated by '/' for each probability",ephemeral=True)
    return
   
   try:
    numbers=(int(split[0]),int(split[1])) #appends a tuple containing the numerator and denominator as integers
   except ValueError:
    await ctx.respond("Only input integers seperated by '/' for each probability",ephemeral=True)
    return
   
   decimal=numbers[0]/numbers[1] #divides numerator by denominator to get a decimal
   if not decimal>=1: #if the fraction is equal to, or greater 1. We can avoid appending it since the % chance is 100%
    decimals.append(decimal)

  if not decimals: #if decimals is empty, it means all the numbers were = or > 1
   decimals=[1]
  
  count=-1 #tracks number of times for loop was run
  total=0 #stores total decimal probability
  for decimal in decimals: #gets total probability by multiplying all current probabilities
   count+=1
   if count==0:
    total=decimal #sets total to decimal if it's the first one, since multiplying by 0 would just give 0
   else:
    total*=decimal #multiplies total by decimal
  
  percentage=total*100 #multiplies by 100 to get a percentage
  await ctx.respond(f"Total probability: {percentage}%; correct to 15 decimals")
                               #>---Admin-Commands---<
  
@client.register
class auditset(lightbulb.SlashCommand, name="auditlog", description="set an audit log channel",hooks=[lightbulb.prefab.has_permissions(hikari.Permissions.ADMINISTRATOR), save_last_channel]): 
 toggle=lightbulb.string(
  "toggle", "Whether audit logs are kept",
  choices=[
   lightbulb.Choice(name="on",value="on"),
   lightbulb.Choice(name="off",value="off"),
  ]
 )
 channel=lightbulb.channel("channel", "Intended channel",default=None,channel_types=[hikari.ChannelType.GUILD_TEXT])

 @lightbulb.invoke
 async def invoke(self, ctx: lightbulb.Context):
  global auditchannels
  guildid=str(ctx.guild_id)
  
  if self.toggle=="off": #deletes guild id from auditchannels and informs user
   if guildid in auditchannels:
    del auditchannels[guildid]
    
    writeto("auditchannels")
      
    await ctx.respond("Audit logging is now disabled")
    return
   
   else: #if there's no audit channel
    await ctx.respond("Audit logging is already disabled", ephemeral=True)
    return
   
  if self.channel==None:
   await ctx.respond("No channel selected", ephemeral=True)
   return
  
  auditchannels[guildid]=self.channel.id
  writeto("auditchannels")

  
  await ctx.respond("Audit channel set")
  
  channel=await bot.rest.fetch_channel(self.channel.id)
  member=ctx.member
  
  embed=hikari.Embed(
   title="**Audit Logging Enabled**",
   description=f"{member.mention} enabled audit logging",
   color=GREEN
  )
  embed.add_field("\u00A0")
  embed.set_footer("use /auditset to disable audit logging or change audit channel")

  await channel.send(embed) #logs audit log creation


@client.register #change on-join role(s)
class joinrole(lightbulb.SlashCommand,name="joinroles",description="Edit which roles are given to members automatically",hooks=[lightbulb.prefab.has_permissions(hikari.Permissions.ADMINISTRATOR), save_last_channel]):
 deloradd=lightbulb.string(
   "action", "Choose an action",
   choices=[
   lightbulb.Choice(name="add", value="add"),
   lightbulb.Choice(name="remove", value="remove"),
   lightbulb.Choice(name="check", value="check"),
   lightbulb.Choice(name="clear", value="clear")
  ]
 )
 role=lightbulb.role("role", "Selected role", default=None)

 @lightbulb.invoke
 async def invoke(self, ctx: lightbulb.Context):
  global auditchannels

  if not self.role==None: #checks if roleid is not selected, and if so, sets it to 0 to allow function to run
   roleid=str(self.role.id)
  else:
   roleid=0
  
  guildid=str(ctx.guild_id)
  deloradd=self.deloradd
  
  if deloradd=="add" or deloradd=="remove": #checks if add or remove mode were selected
   if self.role==None: #checks if role was selected
    await ctx.respond("No role selected", ephemeral=True)
    return
  
  elif deloradd=="clear": #clearing all roles
   if not guildid in defaultroles:
    await ctx.respond("No roles set", ephemeral=True)
    return
    
   del defaultroles[guildid] #deletes guild id and all role ids from .json
   writeto("defaultroles")
    
   await ctx.respond("All roles cleared")
   
   if guildid in auditchannels:
    member=ctx.member
    auditid=int(auditchannels[guildid])
    
    try:
     auditchannel= await bot.rest.fetch_channel(auditid)
    except hikari.NotFoundError:
     await fixauditchannel(guildid)
     return
   
    embed=hikari.Embed(
     title="**On Join Roles Removed**",
     description=f"{member.mention} cleared all join roles",
     color=RED
    )
    embed.add_field("\u00A0")
    embed.set_footer("use /joinroles to add roles or check on-join roles")

    await auditchannel.send(embed)
   return
  
  answer=await savenewdefaultrole(guildid,roleid,deloradd) #function returns message depending on outcome
  await ctx.respond(answer[0], ephemeral=answer[1])

  if guildid in auditchannels: #if audit logging is enabled
   if deloradd=="check":
    return
   
   if answer[1]==True: #if the function returned an ephemeral message aka an issue occured
    return

   member=ctx.member
   auditid=int(auditchannels[guildid])
   
   try:
    auditchannel= await bot.rest.fetch_channel(auditid)
   except hikari.NotFoundError:
    await fixauditchannel(guildid)
    return
   
   if deloradd=="add":
    
    embed=hikari.Embed(
     title="**On Join Role Added**",
     description=f"{member.mention} added {self.role.mention} to join roles",
     color=GREEN
    )
    embed.add_field("\u00A0")
    embed.set_footer("use /joinroles to remove this role or check current on-join roles")
   
   elif deloradd=="remove":
    
    embed=hikari.Embed(
     title="**On Join Role Removed**",
     description=f"{member.mention} removed {self.role.mention} from join roles",
     color=RED
    )
    embed.add_field("\u00A0")
    embed.set_footer("use /joinroles to add this role back or check current on-join roles")

   await auditchannel.send(embed)


@client.register
class mute(lightbulb.SlashCommand, name="mute", description="mute a user",hooks=[lightbulb.prefab.has_permissions(hikari.Permissions.ADMINISTRATOR), save_last_channel]):
 global auditchannels
 
 user=lightbulb.user("user","target user")
 unit=lightbulb.string(
  "unit", "choose a unit",
  choices=[
   lightbulb.Choice(name="seconds", value="seconds"),
   lightbulb.Choice(name="minutes", value="minutes"),
   lightbulb.Choice(name="hours", value="hours"),
   lightbulb.Choice(name="days", value="days"),
   lightbulb.Choice(name="check", value="check")
  ]
 )
 amount=lightbulb.integer("amount","amount",default=1, min_value=1)
 reason=lightbulb.string("reason","reason for mute",default=None)

 @lightbulb.invoke
 async def invoke(self, ctx: lightbulb.Context):
  guildid=str(ctx.guild_id)
  target= await bot.rest.fetch_member(int(guildid),self.user.id)

  if self.user.is_bot:
   await ctx.respond("Bots cannot be muted", ephemeral=True)
   return
  
  if self.unit=="check":
   now=datetime.now(timezone.utc)
   premute=target.communication_disabled_until()
   if premute and premute>now: #if user is muted
    muteduration=premute-now

    #gets all the units V
    days=muteduration.days
    hours,remainder=divmod(muteduration.seconds, 3600) #timedelta only provides days and seconds
    minutes,seconds=divmod(remainder, 60)

    #puts them all in a list V
    muteduration_units=[(days,f"{days} days"),(hours,f"{hours} hour(s)"),(minutes,f"{minutes} minute(s)"),(seconds,f"{seconds} second(s)")] #tuples store numerical value as an integer and string with units
    
    preformat=[] #list to store all numbers and units
    for unit in muteduration_units: #gets rid of units that are 0
     if unit[0]==0:
      continue
     else:
      preformat.append(f"{unit[1]}")
    formatted=", ".join(preformat) #joins numbers and units into a readable sentence
     
    await ctx.respond(f"User is currently muted for {formatted}")
    return
   
   else: #if user is not muted
    await ctx.respond("User is not muted")
   return
  
  #actually muting ("check" not selected) V
  
  if self.amount==None:
   await ctx.respond("No amount chosen", ephemeral=True)
   return
  
  now=datetime.now(timezone.utc)
  premute=target.communication_disabled_until()
  if premute and premute>now:
   await ctx.respond("User is already muted", ephemeral=True)
   return
  
  duration=timedelta(**{self.unit:self.amount}) #creates a dictionary, then unpacks, as timedelta does not accept variables as keywords
  timeout=now+duration #gets timestamp for mute ending
  
  try:     #applies mute V
   await bot.rest.edit_member(ctx.guild_id, target.id, communication_disabled_until=timeout)
   await ctx.respond("User muted successfully")
  except hikari.errors.ForbiddenError: #if you are unable to mute
   await ctx.respond("Cannot mute user, their role may be above mine", ephemeral=True)
   return
  
  if guildid in auditchannels: #if auditlogging is enabled
   member=ctx.member
   if self.reason==None:
    reason="unspecified"
   else:
    reason=self.reason
   auditid=int(auditchannels[guildid])
   
   try:
    auditchannel= await bot.rest.fetch_channel(auditid)
   except hikari.NotFoundError:
    await fixauditchannel(guildid)
    return

   embed=hikari.Embed(
     title=f"**{self.user.username} muted**",
     description=f"{member.mention} muted {target.mention} for {self.amount} {self.unit}",
     color=ORANGE
    )
   embed.add_field(f"Reason: {reason}")
   embed.set_footer("use /unmute to unmute user")
   embed.set_thumbnail(target.display_avatar_url)
   
   await auditchannel.send(embed)


@client.register
class unmute(lightbulb.SlashCommand, name="unmute", description="unmute a user",hooks=[lightbulb.prefab.has_permissions(hikari.Permissions.ADMINISTRATOR), save_last_channel]):
 global auditchannels

 user=lightbulb.user("user", "target user")
 reason=lightbulb.string("reason", "reason for unmute", default=None)

 @lightbulb.invoke
 async def invoke(self, ctx: lightbulb.Context):
  guildid=str(ctx.guild_id)
  target= await bot.rest.fetch_member(int(guildid),self.user.id)

  if self.user.is_bot:
   await ctx.respond("Cannot unmute bots", ephemeral=True)
   return

  premute=target.communication_disabled_until()
  if premute==None or premute<datetime.now(timezone.utc):
   await ctx.respond("User is not muted", ephemeral=True)
   return

  try:     #removes mute V
   await bot.rest.edit_member(ctx.guild_id, target.id, communication_disabled_until=None)
   await ctx.respond("User unmuted successfully")
  except hikari.errors.ForbiddenError: #if you are unable to unmute
   await ctx.respond("Cannot unmute user, their role may be above mine", ephemeral=True)
   return
  
  if guildid in auditchannels:
   member=ctx.member
   if self.reason==None:
    reason="unspecified"
   else:
    reason=self.reason
   auditid=int(auditchannels[guildid])
   
   try:
    auditchannel= await bot.rest.fetch_channel(auditid)
   except hikari.NotFoundError:
    await fixauditchannel(guildid)
    return

   embed=hikari.Embed(
     title=f"**{self.user.username} unmuted**",
     description=f"{member.mention} unmuted {target.mention}",
     color=ORANGE
    )
   embed.add_field(f"Reason: {reason}")
   embed.set_footer("use /mute to re-mute user")
   embed.set_thumbnail(target.display_avatar_url)
   
   await auditchannel.send(embed)

@client.register
class ban(lightbulb.SlashCommand, name="ban", description="ban a user",hooks=[lightbulb.prefab.has_permissions(hikari.Permissions.ADMINISTRATOR), save_last_channel]):
 global auditchannels
 
 user=lightbulb.user("user", "target user")
 reason=lightbulb.string("reason", "reason for ban", default=None)

 @lightbulb.invoke
 async def invoke(self, ctx: lightbulb.Context):
  guildid=str(ctx.guild_id)

  me=bot.get_me()
  if self.user.id==me.id:
   await ctx.respond("Nah", ephemeral=True)
   return

  banned=False
  async for i in bot.rest.fetch_bans(int(guildid)):
   if i.user.id==self.user.id: #checks if user was banned
    banned=True
  
  if banned==True:
   await ctx.respond("User is already banned")
   return
  
  if self.reason==None:
   updatedreason="unspecified"
  else:
   updatedreason=self.reason
  
  try:  #bans user V
   await bot.rest.ban_user(int(guildid), self.user.id, reason=updatedreason)
   await ctx.respond("User banned successfully")
  except hikari.errors.ForbiddenError:
   await ctx.respond("Cannot ban user, their role may be above mine", ephemeral=True)
   return
  
  if guildid in auditchannels:
   member=ctx.member
   auditid=int(auditchannels[guildid])
   
   try:
    auditchannel= await bot.rest.fetch_channel(auditid)
   except hikari.NotFoundError:
    await fixauditchannel(guildid)
    return

   embed=hikari.Embed(
     title=f"**{self.user.username} was banned**",
     description=f"{member.mention} banned {self.user.username}",
     color=RED
    )
   embed.add_field(f"Reason: {updatedreason}")
   embed.add_field(f"User ID: {self.user.id}")
   embed.set_footer("use /unban to unban user or /banlist to see a list of all banned users")
   
   await auditchannel.send(embed)

@client.register
class banlist(lightbulb.SlashCommand, name="banlist", description="check the banlist",hooks=[lightbulb.prefab.has_permissions(hikari.Permissions.ADMINISTRATOR), save_last_channel]):

 @lightbulb.invoke
 async def invoke(self, ctx: lightbulb.Context):
  guildid=str(ctx.guild_id)
  
  bans=[]
  async for i in bot.rest.fetch_bans(int(guildid)): #fetch_bans does not return a list
   bans.append(i)
   
  if not bans:
   await ctx.respond("There are no banned users")
   return
  
  banlist=[] #stores all bans
  for ban in bans:
   x=f"{ban.user.username} - reason: {ban.reason} - user id: {ban.user.id}"
   banlist.append(x)
  formatted=",\n".join(banlist)

  await ctx.respond(f"All banned members:\n{formatted}")

@client.register
class unban(lightbulb.SlashCommand, name="unban", description="unban a user",hooks=[lightbulb.prefab.has_permissions(hikari.Permissions.ADMINISTRATOR), save_last_channel]):
 global auditchannels
 
 user=lightbulb.string("user_id", "target user id")
 reason=lightbulb.string("reason", "reason for unban", default=None)

 @lightbulb.invoke
 async def invoke(self, ctx: lightbulb.Context):
  guildid=str(ctx.guild_id)
  
  try: #checks if self.user is a number
   userid=int(self.user)
  except ValueError:
   await ctx.respond("Input a valid user id", ephemeral=True)
   return

  try:
   target= await bot.rest.fetch_user(userid)
  except hikari.errors.NotFoundError:
   await ctx.respond("Input a valid user id", ephemeral=True)
   return

  banned=False
  async for i in bot.rest.fetch_bans(int(guildid)):
   if i.user.id==userid: #checks if user was banned
    banned=True
  
  if banned==False:
   await ctx.respond("User is not banned", ephemeral=True)
   return
  
  if self.reason==None:
   updatedreason="unspecified"
  else:
   updatedreason=self.reason
  
  try:  #unbans user V
   await bot.rest.unban_user(int(guildid), userid, reason=updatedreason)
   await ctx.respond("User unbanned successfully")
  except hikari.errors.ForbiddenError:
   await ctx.respond("Cannot unban user, I may not have necessary permissions", ehpemeral=True)
   return
  
  if guildid in auditchannels:
   member=ctx.member
   auditid=int(auditchannels[guildid])
   
   try:
    auditchannel= await bot.rest.fetch_channel(auditid)
   except hikari.NotFoundError:
    await fixauditchannel(guildid)
    return

   embed=hikari.Embed(
     title=f"**{target.username} was unbanned**",
     description=f"{member.mention} unbanned {target.username}",
     color=ORANGE
    )
   embed.add_field(f"Reason: {updatedreason}")
   embed.add_field(f"User ID: {userid}")
   embed.set_footer("use /ban to re-ban user or /banlist to see a list of all banned users")
   
   await auditchannel.send(embed)

@client.register
class clearmessages(lightbulb.SlashCommand, name="clear", description="delete multiple messages",hooks=[lightbulb.prefab.has_permissions(hikari.Permissions.ADMINISTRATOR), save_last_channel]):
 global auditchannels

 amount=lightbulb.integer("amount", "amount of messages to clear", min_value=1, max_value=100)
 user=lightbulb.user("user", "only delete from 1 user", default=None)

 @lightbulb.invoke
 async def invoke(self, ctx: lightbulb.Context):
  guildid=str(ctx.guild_id)
  messages=[] #empty list to store messages
  usermessages=[] #stores messages from a target user

  if self.user==None: #if no user was selected
   userid=0
  else: #if a user was selected
   userid=self.user.id
   
  await ctx.defer() #waits for the command to be done before timing out
  response=await ctx.interaction.fetch_initial_response() #gets the defer message so it doesn't delete it's own response
  searched=0 #counts all messages searched through
  
  async for message in bot.rest.fetch_messages(ctx.channel_id): #gets all messages in a channel
   if message.id==response.id: #skips the deferral message
    continue
   
   messages.append(message)
   if userid==message.author.id:
    usermessages.append(message)
   searched+=1

   if self.user==None: #if no user was selected
    if len(messages)>=self.amount or searched>=500: #caps max search depth at 500 messages
     break
   else: #only stops when self.amount messages sent by the user are found (or 500 messages in general)
    if len(usermessages)>=self.amount or searched>=500:
     break

  if  self.user==None: #if no user was selected
   attempted=len(messages)
   deleted=0
   for message in messages:
    try:
     await bot.rest.delete_message(ctx.channel_id, message.id) #deletes message
     deleted+=1
    except hikari.NotFoundError: #if message is already gone
     continue
    
  else: #if a user was selected
   attempted=len(usermessages)
   deleted=0  
  for message in usermessages:
   try:
    await bot.rest.delete_message(ctx.channel_id, message.id)
    deleted+=1
   except hikari.NotFoundError: #if message is already gone
    continue
  
  await ctx.respond(f"{deleted} messages cleared successfully, {attempted-deleted} missing")
  
  if guildid in auditchannels:
   member=ctx.member
   auditid=int(auditchannels[guildid])
   channel= await bot.rest.fetch_channel(ctx.channel_id)
   
   try:
    auditchannel= await bot.rest.fetch_channel(auditid)
   except hikari.NotFoundError:
    await fixauditchannel(guildid)
    return

   embed=hikari.Embed(
     title=f"**{member.username} cleared messages**",
     description=f"{member.mention} cleared {deleted} messages in {channel}",
     color=RED
    )
   
   await auditchannel.send(embed)

@client.register
class role(lightbulb.SlashCommand, name="role", description="give or take a role",hooks=[lightbulb.prefab.has_permissions(hikari.Permissions.ADMINISTRATOR), save_last_channel]):
 global auditchannels

 mode=lightbulb.string("mode","mode",
  choices=[
   lightbulb.Choice(name="give", value="give"),
   lightbulb.Choice(name="remove", value="remove"),
   lightbulb.Choice(name="check", value="check"),
   lightbulb.Choice(name="clear", value="clear")
  ]
 )
 target=lightbulb.user("target","target user")
 role=lightbulb.role("role","targeted role", default=None)

 @lightbulb.invoke
 async def invoke(self, ctx: lightbulb.Context):
  userid=self.target.id
  member= await bot.rest.fetch_member(ctx.guild_id,userid)
  if not self.role==None: #checks if a role was selected
   roleid=self.role.id
   
  if self.mode=="give" or self.mode=="remove": #returns error if no role was selected to add/remove
   if self.role==None:
    await ctx.respond("No role selected",ephemeral=True)
    return
  
  if self.mode=="give": #returns error if user already has that role
   if roleid in member.role_ids:
    await ctx.respond("User already has role", ephemeral=True)
    return
   
   try: #tries to add the role, but if the role is above the bot's; sends an error
    await bot.rest.add_role_to_member(ctx.guild_id,userid,roleid)
    await ctx.respond("Role given successfully")
   except hikari.errors.ForbiddenError:
    await ctx.respond("Cannot give role, that role may be above mine", ephemeral=True)
    return
   
  elif self.mode=="remove":
   if not roleid in member.role_ids: #returns error if user does not have role
    await ctx.respond("User does not have role", ephemeral=True)
    return
   
   try: #tries to add the role, but if the role is above the bot's; sends an error
    await bot.rest.remove_role_from_member(ctx.guild_id,userid,roleid)
    await ctx.respond("Role removed successfully")
   except hikari.errors.ForbiddenError:
    await ctx.respond("Cannot remove role, that role may be above mine", ephemeral=True)
    return
   
  elif self.mode=="check":
   userroles=[] #list to store user's roles
   
   for roleid in member.role_ids:
    role=await bot.rest.fetch_role(ctx.guild_id,roleid)
    if role.id==ctx.guild_id: #skips adding @everyone
     continue
    userroles.append(role.name)

   if not userroles:
    await ctx.respond("User has no roles")
    return
   
   formatted=", ".join(userroles)
   await ctx.respond(f"All roles on user;\n{formatted}")
   return
  
  elif self.mode=="clear":
   if len(member.role_ids)==1: #if they have no roles (other than @everyone)
    await ctx.respond("User has no roles", ephemeral=True)
    return
    
   try: #tries to clear all roles, sends error if one of the roles cannot be cleared
    await bot.rest.edit_member(ctx.guild_id,userid,roles=[])
    await ctx.respond("Roles cleared successfully")
   except hikari.errors.ForbiddenError:
    await ctx.respond("Cannot remove roles, one of their roles may be above mine", ephemeral=True)
    return

  if str(ctx.guild_id) in auditchannels:
   member=ctx.member
   guildid=str(ctx.guild_id)
   auditid=int(auditchannels[guildid])
   
   try: #checks if audit channel is missing
    auditchannel= await bot.rest.fetch_channel(auditid)
   except hikari.NotFoundError:
    await fixauditchannel(guildid)
    return

   if self.role==None:
    rolemention=0
   else:
    rolemention=self.role.mention
    
   auditmessages={ #stores components for embeds in every mode
    "give": [f"**{member.username} gave {self.target.username} a role**", f"{member.mention} gave {self.target.username} {rolemention}", ORANGE, "Use /role remove to remove the role"],
    "remove": [f"**{member.username} removed {self.target.username}'s role**", f"{member.mention} removed {rolemention} from  {self.target.username}", RED, "Use /role give to give the role back"],
    "clear": [f"**{member.username} cleared {self.target.username}'s roles**", f"{member.mention} cleared all roles from {self.target.username}", RED, "Use /role give to give the roles back"]
   }
   
   embed=hikari.Embed(
     title=auditmessages[self.mode][0],
     description=auditmessages[self.mode][1],
     color=auditmessages[self.mode][2]
    )
   embed.set_footer(auditmessages[self.mode][3])
    
   await auditchannel.send(embed)
   
                       #>---Background-Proccesses---<

@bot.listen(hikari.MemberCreateEvent) #logs when users join the server
async def join(event):
 guildid=str(event.guild_id)
 if guildid in auditchannels: #checks if audit logging is on
  channelid=int(auditchannels[guildid])
  
  try: #checks if audit channel is missing
   channel= await bot.rest.fetch_channel(channelid)
  except hikari.NotFoundError:
   await fixauditchannel(guildid)
   return
  
  embed=hikari.Embed(
   title=f"{event.member.username}",
   description=f":green_square:{event.member.mention} **joined the server**",
   color=GREEN
  )
  embed.set_footer(f"User ID: {event.member.id}")
  embed.set_thumbnail(event.member.display_avatar_url)
  
  await channel.send(embed) #sends message to log join


@bot.listen(hikari.MemberCreateEvent) #gives new users default roles
async def autoroles(event):
 guildid=str(event.guild_id)
 if guildid in defaultroles: #checks if any default roles are stored
  if event.member.is_bot:
   return

  error=False #is True if there were roles the bot couldn't add
  missingerror=False #is True if there were roles that are deleted
  nopermroles=[] #list to store all roles the bot cannot add
  missingroles=[] #list to store all missing roles
  
  for roleid in defaultroles[guildid]: #gives default roles to new members
   try:
    await bot.rest.add_role_to_member(int(guildid),event.member.id,int(roleid))
    
   except hikari.NotFoundError: #if a role is missing
    missingroles.append(int(roleid))
    missingerror=True
    
   except hikari.errors.ForbiddenError: #if the bot cannot add a role due to perms
    error=True
    permrole=await bot.rest.fetch_role(int(guildid),int(roleid))
    nopermroles.append(permrole.name)

  if missingerror==True:
   await fixdefaultroles(guildid,missingroles)
  
  if error==True: #fixdefaultroles sends it's own message so there's no need to add missing roles here
   broken=0
   if guildid in auditchannels:
    channelid=int(auditchannels[guildid])
    try: #checks if audit channel is missing
     channel=await bot.rest.fetch_channel(channelid)
    except hikari.NotFoundError:
     await fixauditchannel(guildid)
     broken=1 #if it reaches 2, cancels sending the embed
   
   if broken==1 or not guildid in auditchannels:
    if guildid in lastchannel:
     channelid=int(lastchannel[guildid])
     try: #checks if last used channel is missing
      channel=await bot.rest.fetch_channel(channelid)
     except hikari.NotFoundError:
      del lastchannel[guildid]
      broken=2

   if not broken or broken<2: #sends embed if there's a channel
    formatted=", ".join(nopermroles)
    
    embed=hikari.Embed(
     title="Error adding role(s)",
     description=f"Bot does not have permission to add on-join role(s),\nThe role(s) may be higher than mine\nList of roles the bot cannot add: {formatted}",
     color=ORANGE
    )
    embed.set_footer(f"Idk what to put here")
    
    await channel.send(embed)
   
@bot.listen(hikari.MemberDeleteEvent) #logs when users leave the server
async def leave(event):
 guildid=str(event.guild_id)
 
 if guildid in auditchannels:
  channelid=int(auditchannels[guildid])
  
  async for i in bot.rest.fetch_bans(int(guildid)):
   if i.user.id==event.old_member.id: #checks if user was banned
    return
  
  try:
   channel= await bot.rest.fetch_channel(channelid)
  except hikari.NotFoundError:
   await fixauditchannel(guildid)
   return
   
  embed=hikari.Embed(
   title=f"{event.old_member.username}",
   description=f":red_circle:{event.old_member.mention} **left the server** :(",
   color=RED
  )
  embed.set_footer(f"User ID: {event.old_member.id}")
  embed.set_thumbnail(event.old_member.display_avatar_url)
  
  await channel.send(embed)

@bot.listen() #responds to pinging the bot
async def mention(event: hikari.GuildMessageCreateEvent):
 if event.member.is_bot:
  return
 
 self=bot.get_me()
 if self.id in event.message.user_mentions_ids:
  channel=event.get_channel()
  responses=["What","Kys","That's not a command","/help dipshit","Stop","No",  #list to store response messages
  ["❌","🖕","👎",["🏳️‍🌈","❓"],["🇰","🇾","🇸"]],
  [ #stores fake ips and other doxxy stuff
   ["82.14.193.47","91.108.72.156","176.34.219.83","109.152.64.201","185.67.143.29"], #fake ips
   ["AS1516","AS13335","AS165","AS8075","AS32934","AS645"], #fake ASNs
   ["52° 32′ 41.99″ N","40° 42′ 46.08″ N","51° 30′ 26.64″ N","48° 51′ 24.00″ N","35° 40′ 34.32″ N","53° 20′ 60.00″ N"], #fake coordinates (latitude)
   ["6° 15′ 37.08″ W","74° 00′ 21.60″ W","0° 07′ 40.08″ W","2° 21′ 07.20″ E","139° 39′ 01.08″ E","6° 15′ 00.00″ W"] #fake coordinates (longitude)
  ]
 ]
  domlist=["I'm the real one","You're fake","I'm better","Become a bot"]
  

  if event.member.id==1157813819079413801: #if user is Dominik
   choice=random.choice(domlist)
   await channel.send(choice)
   return
  
  choice=random.choice(responses) #picks a random response
  if type(choice)!=list:
   await channel.send(choice)
  
  elif type(choice[0])==list: #the dox list has a first choice of a list
   doxlist=responses[7]
   parts=[random.choice(doxlist[0]),random.choice(doxlist[1]),random.choice(doxlist[2]),random.choice(doxlist[3])] #stores info to dox
   
   await channel.send(f"{parts[0]}\n{parts[1]}\n{parts[2]} Latitude\n{parts[3]} Longitude")
   
  else: #if choice is react
   reactlist=responses[6]
   reaction=random.choice(reactlist)

   if reactlist.index(reaction)<3: #if the index of the reaction is under 3, it's not a list and only 1 reaction
    await event.message.add_reaction(reaction)
   else:
    for emoji in reaction: #adds all emojis in order
     await event.message.add_reaction(emoji)
