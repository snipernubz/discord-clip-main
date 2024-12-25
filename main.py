import json
import interactions
import asyncio
import moviepy
from pytube import YouTube
from datetime import timedelta
import os 

import tracemalloc

tracemalloc.start()

with open('config.json', 'r') as configfile:
    config = json.load(configfile)
    token = config["token"]
    guild = config["guild"]

bot = interactions.Client(
    token=str(token),
    default_scope=int(guild),
    )

@interactions.listen()
async def on_startup():
    print("Bot started")

# test commands

@interactions.slash_command()
async def pog(ctx: interactions.SlashContext):
    """basic ping command"""
    await ctx.send(ephemeral=True, content=f"Ping! {bot.latency}ms")


@interactions.slash_command()
async def relay(ctx: interactions.SlashContext, text: str):
    """relay what u say"""
    await ctx.send(ephemeral=True, content=f"You said '{text}'!")
 
@interactions.slash_command()
async def channel_test(ctx):
     print(ctx)
     await ctx.send(content=f"pog")
     
################# actual commands  #####################

 # functions to help with varying tasks

def convert_sec(sec):
    """
    Converts Seconds into a HH:MM:SS format
    Args:
        sec (string): Time in Seconds

    Returns:
        string : Time in HH:MM:SS format
    """
    
    td = timedelta(seconds = sec)
    return str(td)
  
def convert_hms(time):
    """
    Converts HH:MM:SS into Seconds

    Args:
        time (string): HH:MM:SS string

    Returns:
        string : Time in Seconds
    """    
    secs = sum(int(x) * 60 ** i for i, x in enumerate(reversed(time.split(':'))))
    return secs 
   
# create continue/abort buttons
def create_con_btn(conid, contxt = "Continue", badid = "abort", badtxt = "Abort"):
    """
    Creates a Confirm and Abort button

    Args:
        conid (str): custom id for confirm button
        contxt (str): custom txt for confirm button
        badid (str): custom id for abort button
        badtxt (str): custom txt for abort button
    Returns:
        ActionRow: Actionrow containing the Confirm and Abort buttons
    """    
    
    fixedconid = str(conid)
    fixedcontxt = str(contxt)
    con_button = interactions.Button(
        style=interactions.ButtonStyle.SUCCESS,
        label=fixedcontxt,
        custom_id=fixedconid,
    )
    fixedbadid = str(badid)
    fixedbadtxt = str(badtxt)
    abr_button = interactions.Button(
        style=interactions.ButtonStyle.DANGER,
        label=fixedbadtxt,
        custom_id=fixedbadid,
    )
    
    
    con_abr_row = interactions.ActionRow.new(con_button, abr_button)
    return con_abr_row
 
@interactions.component_callback("abort")
async def abr_response(ctx):
    await ctx.send(ephemeral=True, content="You chose to abort")

def createSelectOpt(dict):
    """ Create list of select Options from a dict """
    Selectopt = []
    for x, y in dict.items():
        Selectopt.append(interactions.SelectOption(label=x, value=y))
    return Selectopt



# make command

    # functions and Variables specific to the "make" command

vid_info = {}
res_itag = {}
download_con = False
dp = 0

def downloadCompleted():
    print("downloadCompleted was called")
    download_con = True
    
def downloadProgress(s, chunk, bytes_remaining):
    print("download progress was called")
    size = s.filesize
    bytes_downloaded = size - bytes_remaining
    download_percent = bytes_downloaded / size * 100
    dp = int(download_percent)
    print(f"dp is now {dp}%")



@interactions.slash_command()
async def make(ctx: interactions.SlashContext):
    """make command"""
    pass


#make command
    # code for the "make clip" subcommand

@make.subcommand()
async def clip(ctx: interactions.SlashContext, clip_link: str):
    """Make a clip from a video"""
    
    
    print(f"Link: {clip_link}")
    
    video_url = str(clip_link)
    global videoobj 
    
    videoobj = YouTube(url=video_url, on_progress_callback=downloadProgress, on_complete_callback=downloadCompleted())
    
    # check video avalability
    videoobj.check_availability()
    
    print(f"Video title: '{videoobj.title}' video has length of '{videoobj.length}' seconds") 

    # add video info to vid_info 
    vid_info["video link:"] = video_url
    vid_info["video title:"] = videoobj.title
    vid_info["video length:"] = convert_sec(videoobj.length)
    
    end_label = str(f'end time MAX: {vid_info.get("video length:").upper()} (format HH:MM:SS.MS)')
    
    # make clip times modal
    clip_times_modal = interactions.Modal(
        title="(clip) Choose Start time",
        custom_id="clip_start",
        components=[
            interactions.TextInput(
            style=interactions.TextStyleType.SHORT,
            label="start time (format HH:MM:SS.MS)",
            custom_id="clip_start_time",
            min_length=1,
            max_length=8,
        ), 
            interactions.TextInput(
            style=interactions.TextStyleType.SHORT,
            label=end_label,
            custom_id="clip_end_time",
            min_length=1,
            max_length=10,
        )],
    )
    
    # send times modal
    
    await ctx.send_modal(clip_times_modal)


@interactions.modal_callback("clip_times_modal")
async def on_modal_response(ctx, clip_start_time: str, clip_end_time: str):
    
    vid_info["start time:"] = clip_start_time
    vid_info["end time:"] = clip_end_time
    
    # make clip quality Selectmenu
    video_streams = videoobj.streams
    pro_streams = video_streams.filter(progressive=True)
    for x in pro_streams:
        t = f"{x.resolution} audio: {x.is_progressive}"
        res_itag[t] = x.itag
    
    webm_streams = videoobj.streams.filter(only_video=True, file_extension="webm")
    for x in webm_streams:
        t = f"{x.resolution} audio?: {x.is_progressive}"
        res_itag[t] = x.itag
    

    Menu = interactions.SelectMenu(
            placeholder="Resolution, audio?",
            custom_id="select_qual",
            options=createSelectOpt(res_itag),
            
        )
    
    await ctx.send(components=Menu)

  
@interactions.component_callback("select_qual")
async def select_qual_res(ctx, response: str):
    
    
    vid_info["resolution:"] = videoobj.streams.get_by_itag(int(response[0])).resolution
    
    #vid_info["approx size:"] = videoobj.streams.get_by_itag(int(response[0])).filesize_mb
    
    vid_info["itag:"] = response[0]
    
    
    await ctx.edit(content="Final confirm", components=create_con_btn("clip_qual"))
    
    

@interactions.component_callback("clip_qual")
async def final_confirm(ctx):
    
    #make vid_info embed
    
    info_embed = interactions.Embed(title='Confirm Options', description='Are these correct?')
    for x, y in vid_info.items():
        info_embed.add_field(name=str(x) , value=str(y), inline=False)
   
    #create y/n buttons
    ybutton = interactions.Button(
        style=interactions.ButtonStyle.SUCCESS,
        label="Yes",
        custom_id="good_confirm",
    )
    
    nbutton = interactions.Button(
        style=interactions.ButtonStyle.DANGER,
        label="No",
        custom_id="bad_confirm",
    )
    
    row = create_con_btn("good_confirm","Yes","bad_confirm","No")
    
    # send embed and buttons
    await ctx.send(ephemeral=True, embeds=info_embed, components=row) 



@interactions.component_callback("good_confirm")
async def good_confirm_res(ctx):
    #await ctx.disable_all_components()
    await ctx.send(ephemeral=True, content="Downloading the video \n Please be patient ")
    
  
    # download the video
    videostream = videoobj.streams.get_by_itag(int(vid_info["itag:"]))
    print("downlading the video")
    videostream.download(filename="yt_vid.webm")
    
    while dp != 0:
        await ctx.send(ephemeral=True, content=f"Percent {dp}%")
        asyncio.sleep(0.5)
    await ctx.send(ephemeral=True, content="Video Downloaded \n")
    
    await ctx.defer(edit_origin=True)
    
    # moviepy shit
    
    global vidClip
    vidClip = moviepy.VideoFileClip("yt_vid.webm")
    print("loaded video")
    vidClip.save_frame("first.png", vid_info["start time:"])
    vidClip.save_frame("end.png", vid_info["end time:"])
    
    str_frame = interactions.File("first.png")
    end_frame = interactions.File("end.png")
    
    str_frame_embed=interactions.Embed(title="Is this the correct section?", description="Starting Frame")
    end_frame_embed=interactions.Embed(title="Is this the correct section?", description="Ending Frame")
    
    #send first and last frame of clip to let user confirm if correct times
    channel = ctx.channel
    await channel.send(ephemeral=True,  embeds=str_frame_embed)
    await channel.send(ephemeral=True,  files=str_frame)
    await channel.send(ephemeral=True,  embeds=end_frame_embed)
    await channel.send(ephemeral=True,  files=end_frame)
    row=create_con_btn("good_sec","Yes","bad_sec","No")
    await ctx.send(ephemeral=True,  components=row)
    os.remove("first.png")
    os.remove("end.png")
    
@interactions.component_callback("bad_confirm")
async def bad_confirm_res(ctx):
    await ctx.disable_all_components()
    await ctx.send(ephemeral=True, content="Command Canceled, please run it again")
    
@interactions.component_callback("bad_sec")
async def bad_sec_response(ctx):
    # make clip start modal
    clip_start_modal = interactions.Modal(
        title="(clip) Choose Start time",
        custom_id="sec_start",
        components=[interactions.TextInput(
            style=interactions.TextStyleType.SHORT,
            label="start time (format HH:MM:SS)",
            custom_id="sec_start_time",
            min_length=1,
            max_length=8,
        )],
    )
    
    # send start modal
    await ctx.popup(clip_start_modal)



@interactions.modal_callback("sec_start")
async def modal_response(ctx, start_time: str):

  vid_info["start time:"] = start_time
  
  await ctx.send(ephemeral=True,  content="choose end time", components=create_con_btn("sec_start_con"))

  

@interactions.component_callback("sec_start_con")
async def sec_start_con_response(ctx):
    
    # make clip end modal
    
    end_label = str(f'end time MAX: {vid_info.get("video length:").upper()} (format HH:MM:SS)')
    
    clip_end_modal = interactions.Modal(
            title="(clip) Choose end time",
            custom_id="sec_end",
            components=[interactions.TextInput(
                style=interactions.TextStyleType.SHORT,
                label=end_label,
                custom_id="sec_end_time",
                min_length=1,
                max_length=10,
            )],
        )
    
    await ctx.popup(clip_end_modal)
    

@interactions.modal_callback("sec_end")
async def modal_response(ctx, end_time: str):
    
    vid_info["end time:"] = end_time
    row=create_con_btn("good_confirm","Continue")
    await ctx.send(ephemeral=True, content="Continue to confirm section", components=row)

@interactions.component_callback("good_sec")
async def good_sec_response(ctx):
    modClip = vidClip.subclip(vid_info["start time:"], vid_info["end time:"])
    print("Extracted clip")
    await ctx.send(ephemeral=True, content="Clip made \n Give me a bit to give it to ya!")
    await ctx.defer(edit_origin=True)
    modClip.write_videofile(filename="result.webm", preset="slower")
    os.remove('yt_vid.webm')
    result = interactions.File("result.webm")
    await ctx.send(ephemeral=True, content="Here ya go!")
    await ctx.channel.send(files=result)
    os.remove("result.webm")
    

  

@clip.error
async def clip_error(ctx: interactions.SlashContext, error: Exception):
    err = str(error)
    print(f"ERROR: {err}")
    await ctx.send(ephemeral=True, content=f"ERROR: {err}")
    
    


bot.start()


