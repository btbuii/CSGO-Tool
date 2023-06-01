import discord
import os
from discord import app_commands, ui
from datetime import datetime
from gamestate import ProcessGameState
from data_dicts import data_dict, type_dict

MY_GUILD = discord.Object(id=1113341076032475240) # EG CSGO TOOL discord server ID

class MyClient(discord.Client): # discord client
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.all()
client = MyClient(intents=intents)

@client.event
async def on_ready(): # initialization of discord bot
    await client.change_presence(status=discord.Status.online, activity=discord.Game("Online"))
    print(f"Logged in as: {client.user}")
    print("----------")

    """=========================================================="""
    file_path = "C:\\Users\\ipwnc\\Desktop\\game_state_frame_data.parquet"
    global PSG
    PSG = ProcessGameState(file_path)
    """=========================================================="""


@client.tree.command(name = "test", description = "Test command")
async def test(interaction : discord.Interaction): # /test command to test bot status
    await interaction.response.send_message("Testing!")

@client.tree.command(name = "weapons", description = "Extracts weapon classes")
async def weapons(interaction : discord.Interaction): # /weapons command, extract weapons classes

    class WeaponsModal(ui.Modal, title = "Extract weapons classes"):
        data_type = ui.TextInput(label = "What format do you want the weapons classes?", placeholder = "i.e. counter, set", style = discord.TextStyle.short, required = True)

        async def on_submit(self, interaction : discord.Interaction):
            parsed = str(self.data_type).lower()
            data_returned = PSG.extract_weapons_classes(parsed)
            data_returned = str(data_returned)
            if data_returned == None:
                await interaction.response.send_message("Invalid input. Valid inputs include: counter, set")
            else:
                await interaction.response.send_message(f"Submitting [weapon_class] data in {parsed} format...")
                
                # code block for returning data in list format --> causes discord rate limiting
                # if len(data_returned) > 2000:
                #    segments = [data_returned[i:i+2000] for i in range(0, len(data_returned), 2000)]
                #    for segment in segments:
                #        await interaction.followup.send(segment)
                # else:

                await interaction.followup.send(data_returned)

    await interaction.response.send_modal(WeaponsModal())

@client.tree.command(name = "boundary", description = "Returns number of entries in which player is within chokepoint on Bombsite B")
async def boundary(interaction : discord.Interaction): # /boundary command, returns percentage of entries within chokepoint boundary
    data_returned = PSG.within_boundary()
    percentage = len(data_returned) * 100.0 / PSG.size
    formatted_percentage = "{:.3f}".format(percentage)
    await interaction.response.send_message(f"Looking over the data provided, **{len(data_returned)}** entries fall within the boundary of the chokepoint on Bombsite B. **{PSG.size}** total entries were reviewed. Using the given data, players are typically found in the boundary **{formatted_percentage}%** of the time.")


@client.tree.command(name = "filter", description = "Filters data based on provided arguments")
async def filter(interaction : discord.Interaction): # /filter command, returns rows within range of arguments

    class FilterModal(ui.Modal, title = "Data filtering"):
        column_to_filter = ui.TextInput(label = "Column to filter by", placeholder = "i.e. is_alive, team, side", style = discord.TextStyle.short, required = True)
        equal_value = ui.TextInput(label = "Get values EQUAL to", style = discord.TextStyle.short, required = False)
        not_equal_value = ui.TextInput(label = "Get values NOT EQUAL to", style = discord.TextStyle.short, required = False)
        minimum_value = ui.TextInput(label = "Get values GREATER THAN or EQUAL to", style = discord.TextStyle.short, required = False)
        maximum_value = ui.TextInput(label = "Get values LESS THAN or EQUAL to", style = discord.TextStyle.short, required = False)

        async def on_submit(self, interaction : discord.Interaction):
            column = str(self.column_to_filter).lower()
            equal = str(self.equal_value)
            not_equal = str(self.not_equal_value)
            minimum = str(self.minimum_value)
            maximum = str(self.maximum_value)
            
            try:
                current_type = type_dict[column]
            except KeyError:
                await interaction.response.send_message("Column name doesn't exist. Use /dictionary for valid column names to filter by.")
                return 

            # if all fields left empty
            if ((not equal) and (not not_equal) and (not minimum) and (not maximum)):
                await interaction.response.send_message("Please enter a value for at least one filtering input.")
                return

            # if filtering by bool or str and only maximum / minimum is provided 
            if ((current_type == bool or current_type == str) and (minimum or maximum) and (not not_equal) and (not equal)):
                await interaction.response.send_message("Invalid filter values. Please confirm and try again.")
                return
            # otherwise, we are dealing with (1. int, with at least one filter provided), (2. bool / str with EQUAL or NON-EQUAL filter provided)
            else:
                if current_type == bool:
                    if equal.title() == "True" or equal.title() == "False": # filter by exact match
                        filtered_data = PSG.filter_data_by_bool(column, equal_value = bool(equal.title()))
                    elif not_equal() == "True" or not_equal.title() == "False": # filter by exact non-match
                        filtered_data = PSG.filter_data_by_bool(column, not_equal_value = bool(not_equal.title()))
                    else:
                        await interaction.response.send_message(f"The **{column}** column is of type **bool**. Please adjust your filter values accordingly and try again.")
                elif current_type == str:
                    filtered_data = PSG.filter_data_by_str(column, equal, not_equal)
                elif current_type == int:
                    if equal.isnumeric(): # filter by exact matches
                        filtered_data = PSG.filter_data_by_int(column, equal_value = int(equal))
                    elif not_equal.isnumeric():
                        if minimum.isnumeric() and maximum.isnumeric(): # filter by exact non-matches within minimum and maximum
                            filtered_data = PSG.filter_data_by_int(column, minimum_value = int(minimum), maximum_value = int(maximum), not_equal_value = int(not_equal))
                        elif minimum.isnumeric(): # filter by exact non-matches within minimum
                            filtered_data = PSG.filter_data_by_int(column, minimum_value = int(minimum), not_equal_value = int(not_equal))
                        elif maximum.isnumeric(): # filter by exact non-matches within maximum
                            filtered_data = PSG.filter_data_by_int(column, maximum_value = int(maximum), not_equal_value = int(not_equal))
                        else:
                            await interaction.response.send_message(f"The **{column}** column is of type **int**. Please adjust your filter values accordingly and try again.")
                            return
            
            def create_report(data):
                percentage = len(data) * 100.0 / PSG.size
                formatted_percentage = "{:.3f}".format(percentage)

                embed = discord.Embed(
                    title = "Data report",
                    description = f"Filtering Parquet file by **{column}**. Looking over the data provided, **{len(data)}** entries met the filter condition. **{PSG.size}** total entries were reviewed. The filtered data makes up **{formatted_percentage}%** of the total data.", 
                    timestamp = datetime.now(),
                    colour = discord.Colour.blue()
                )
                embed.add_field(name = "EQUAL to", value = f"{equal if equal else None}", inline = True)
                embed.add_field(name = "NOT EQUAL to", value = f"{not_equal if not_equal else None}", inline = True)
                embed.add_field(name = "GREATER than or EQUAL to", value = f"{minimum if minimum else None}", inline = True)
                embed.add_field(name = "LESS than or EQUAL to", value = f"{maximum if maximum else None}", inline = True)
                embed.set_footer(text = f"Report requested by {interaction.user.display_name}")

                return embed

            await interaction.response.send_message(embed = create_report(filtered_data))

    await interaction.response.send_modal(FilterModal())


@client.tree.command(name = "dictionary", description = "Prints attributes, descriptions, and types in data dictionary") 
async def dictionary(interaction : discord.Interaction):

    embed = discord.Embed(title = "Data Dictionary", description = "Each row represents a player's game state per frame (tick)", timestamp = datetime.now(), color = discord.Colour.blue())
    for k, v in data_dict.items():
        embed.add_field(name = k, value = v)

    await interaction.response.send_message(embed=embed)

"""
@client.tree.command(name = "start", description = "Upload a file as you type this command to start")
async def start(interaction : discord.Interaction):

    if len(interaction.message.attachments) == 0: # if a file is not uploaded
        await interaction.response.send_message("Please upload a file.")
        return

    attachment = interaction.message.attachments[0]

    if not attachment.filename.endswith(".parquet"):
        await interaction.response.send_message("Invalid file format. Upload a Parquet file.")
        return 

    local_path = "C:\\Users\\ipwnc\\Desktop\\EG CSGO Tool"
    file_path = os.path.join(local_path, attachment.filename)
    await attachment.save(file_path)
    await interaction.response.send_message("File received.")
"""

client.run("TOKEN")