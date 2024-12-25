import json
from interactions import Modal, ModalContext, ParagraphText, ShortText, SlashContext, modal_callback, slash_command
import asyncio

import tracemalloc

tracemalloc.start()


with open('config.json', 'r') as configfile:
    config = json.load(configfile)
    token = config["token"]
    guild = config["guild"]

bot = Client(
    token=str(token),
    default_scope=int(guild),
    )
@interactions.listen()
async def on_startup():
    print("Bot started")
    
@interactions.slash_command(name="my_modal_command", description="Playing with Modals")
async def my_command_function(ctx: interactions.SlashContext):
    await ctx.defer()
    my_modal = interactions.Modal(
        interactions.ShortText(label="Short Input Text", custom_id="short_text"),
        interactions.ParagraphText(label="Long Input Text", custom_id="long_text"),
        title="My Modal",
    )
    await ctx.send_modal(modal=my_modal)
    
@modal_callback("my_modal")
async def on_modal_answer(ctx: ModalContext, short_text: str, long_text: str):
    print(f"Short text: {short_text}, Paragraph text: {long_text}")
    await ctx.send(f"Short text: {short_text}, Paragraph text: {long_text}", ephemeral=True)






bot.start()
    