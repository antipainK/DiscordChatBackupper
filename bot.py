from random import randrange
import discord
from discord.ext.commands import Bot
import os
from zipfile import ZipFile
import requests
import re
import shutil

from text_helper import *

################################################################################

bot_name = "Discord Chat Backupper by WuKos"
bot_version = "1.0.1"
# https://discord.com/oauth2/authorize?client_id=789584577387692093&scope=bot

################################################################################

delete_after_upload = True
anonymize_nicknames = True
include_dates = False
include_this_bot_messages = False
delete_command_after_casting = True

################################################################################

markdown_file_name_length_limit = 25            # How long markdown file name can be
discord_chat_history_depth_limit = 10000        # How "deep" do the bot should go (important if doing a backup of huge channels)

################################################################################

source_path = os.path.dirname(os.path.realpath(__file__))
build_path = os.path.join(source_path, "build")
if not os.path.exists(build_path):
    os.mkdir(build_path)

bot = Bot("!")


def read_token():
    with open("token.txt", "r") as file:
        return file.readlines()[0].strip()


token = read_token()


def get_all_file_paths(directory):  # for ZipFile
    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths



image_formats = ["png", "jpg", "jpeg", "gif"]
first_names = ["William", "James", "Harper", "Mason", "Evelyn", "Ella", "Marie", "John", "George", "Oliver", "Jack",
               "Harry", "Jacob", "Charlie", "Thomas", "Oscar", "Connor", "Kyle", "Richard", "Amelia", "Olivia", "Emily",
               "Poppy", "Isabella", "Jessica", "Sophie", "Samantha", "Elizabeth", "Lauren", "Sarah", "Abraham",
               "Stephan", "Madison", "Colton", "Cooper", "Myles", "Hope", "Garek", "Harold", "Hermione", "Haroldzina",
               "Student", "Dziekan", "Joseph", "Adolf", "Emmett", "Lily", "Kendall", "Demon", "MC", "Jackson", "Avery",
               "Scarlett", "Eleanor", "Wyatt", "Carter", "Julian", "Grayson", "Lucy", "Miles", "Jeremy", "Edgar",
               "Allan", "Katarina", "Ichigo", "Subaru Natsuki", "Emilia", "Chika", "Kaguya", "Norman", "Nishimiya",
               "Rimuru", "Veldora", "Rigurd", "Maou", "Senku", "Tsukasa", "Levi"]


def filter_string(string):
    filtered_Polish_string = string.replace("ó", "o").replace("ż", "z").replace("ź", "z").replace("ę", "e").replace("ą", "a").replace("ś", "s").replace("ł", "l").replace("ć", "c").replace("ń", "n").replace("Ó", "O").replace("Ż", "Z").replace("Ź", "Z").replace("Ę", "E").replace("Ą", "A").replace("Ś", "S").replace("Ł", "L").replace("Ć", "C").replace("Ń", "N")
    return re.sub('[^a-zA-Z0-9 \n\.\-\_]', '', filtered_Polish_string).replace(" ", "-")


@bot.command()
async def tell_me_ctx(ctx):
    await ctx.send(ctx.channel)
    await ctx.send(ctx.channel.category)


def write_markdown_line_to_file(markdown_line, file):
    file.write(markdown_line.encode("utf-8"))


async def inner_backup_channel(ctx, channel, main_path, create_new_directory=False, first_names_offset=0):
    channel_name = filter_string(channel.name)
    channel_fullname = filter_string(channel.category.name) + " - " + channel_name
    markdown_name = channel_name[0:markdown_file_name_length_limit - 3] + ".md"

    if create_new_directory:
        channel_path = os.path.join(main_path, channel_name)
        if not os.path.exists(channel_path):
            os.mkdir(channel_path)
    else:
        channel_path = main_path

    file = open(os.path.join(channel_path, markdown_name), 'wb')
    write_markdown_line_to_file("### Channel name: " + channel.name + "\n___\n", file)

    try:
        async for message in channel.history(limit=discord_chat_history_depth_limit, oldest_first=True):

            if not include_this_bot_messages:
                if message.author == bot.user:
                    continue

            output_string = "\n"

            if anonymize_nicknames:
                output_string += first_names[(int(message.author.id) + first_names_offset) % len(first_names)] + ": "
            else:
                output_string += message.author.name + ": "

            if include_dates:
                output_string += "&nbsp;_(" + str(message.created_at)[0:19] + ")_"

            output_string += "\n\n" + message.clean_content + "\n\n"

            for attachment in message.attachments:
                attachment_file_name = str(attachment.id) + "_" + filter_string(attachment.filename)
                attachment_file_path = os.path.join(channel_path, attachment_file_name)

                await attachment.save(attachment_file_path)

                if any(attachment_file_name.lower().endswith(image_format) for image_format in image_formats):
                    output_string += "\n\n![" + attachment.filename + "](" + attachment_file_name + "?raw=true)\n\n"
                else:
                    output_string += "[" + attachment.filename + "](" + attachment_file_name + ")\n\n"

            if message.reactions:
                output_string += "Reactions: "
                for reaction in message.reactions:
                    output_string += " "
                    if type(reaction.emoji) is type("string"):
                        output_string += reaction.emoji
                    else:
                        output_string += reaction.emoji.name
                    output_string += " - " + str(reaction.count) + " ,"
                output_string = output_string[:-1] + "\n\n"

            output_string += "___"
            write_markdown_line_to_file(output_string, file)

    except discord.errors.Forbidden:
        printTabbed("Lacking permission to browse through messages on '" + channel_fullname + "'.")
        await ctx.send("Lacking permission to browse through messages on '" + channel_fullname + "'.")

    file.close()


def zip_files(main_folder_name, main_path):
    printTabbed("Zipping " + main_folder_name + ".zip - Started...")
    file_paths = get_all_file_paths(main_path)
    zip_name = main_folder_name + ".zip"
    zip_path = os.path.join(build_path, zip_name)
    length_of_build_path = len(build_path)
    with ZipFile(zip_path, "w") as zip_saved:
        for file in file_paths:
            zip_saved.write(file, file[length_of_build_path:])
    printTabbed("Zipping " + zip_name + " - Finished.")
    return zip_name, zip_path


async def send_file_to_FileIO(ctx, file_name, file_path):
    printTabbed("Uploading " + file_name + " to File.io - Started...")
    await ctx.send("Uploading " + file_name + " to File.io - Started...")

    try:
        zip_file = open(file_path, 'rb')
        files = {
            'file': (file_name, zip_file),
        }
        response = requests.post('https://file.io/', files=files)
        result = response.json()
        zip_file.close()

        printTabbed("Uploading " + file_name + " to File.io - Finished.")
        await ctx.send("Uploading " + file_name + " to File.io - Finished.")

        if result["success"]:
            await ctx.send("Download (single-use) `" + file_name + "`: " + result["link"])
        else:
            await ctx.send("There was an error during the upload. Error message: " + result["message"] + ".")

    except MemoryError:
        printTabbed("Error: Memory error (file too large?)")
        await ctx.send("Error: Memory Error (probably the file is too large).")


async def send_file_to_channel(ctx, file_name, file_path):

    printTabbed("Uploading " + file_name + " to Discord - Started...")
    await ctx.send("Uploading " + file_name + " to Discord - Started...")

    try:
        await ctx.send(file=discord.File(file_path))
        printTabbed("Uploading " + file_name + " to Discord - Finished.")

    except discord.errors.HTTPException:
        printTabbed("Uploading " + file_name + " to Discord - Finished with an error!")
        await ctx.send("Uploading " + file_name + " to Discord - Finished with an error!")
        await send_file_to_FileIO(ctx, file_name, file_path)


async def delete_backup_files(main_folder_name, main_path, zip_path):
    printTabbed("Deleting " + main_folder_name + " - Started...")
    try:
        shutil.rmtree(main_path)
        os.remove(zip_path)
        printTabbed("Deleting " + main_folder_name + " - Finished.")
    except OSError as e:
        print(e)


@bot.command()
async def backup_channel(ctx):
    first_names_offset = randrange(len(first_names))
    filtered_name = filter_string(ctx.channel.name)
    main_folder_name = "channelBackup_" + filtered_name
    main_path = os.path.join(build_path, main_folder_name)

    try:
        if delete_command_after_casting:
            try:
                await ctx.message.delete()
            except discord.errors.Forbidden:
                printTabbed("Lacking permission to delete messages on '" + filtered_name + "'.")

        printTabbed("Backup of '" + filtered_name + "' - Started...")
        await ctx.send("Backup of '" + filtered_name + "' - Started...")

        if not os.path.exists(main_path):
            os.mkdir(main_path)

        await inner_backup_channel(ctx, ctx.channel, main_path, first_names_offset=first_names_offset)

        printTabbed("Backup of '" + filtered_name + "' - Finished.")
        await ctx.send("Backup of '" + filtered_name + "' - Finished.")

        zip_name, zip_path = zip_files(main_folder_name, main_path)

        await send_file_to_channel(ctx, zip_name, zip_path)

        if delete_after_upload:
            await delete_backup_files(main_folder_name, main_path, zip_path)

    except discord.errors.Forbidden:
        printTabbed("Lacking permission to send messages on '" + filtered_name + "'.")





@bot.command()
async def backup_all(ctx):

    first_names_offset = randrange(len(first_names))

    main_folder_name = "serverBackup_" + filter_string(ctx.guild.name)
    main_path = os.path.join(build_path, main_folder_name)
    print("Backup of: " + filter_string(ctx.guild.name) + " - Started...")
    await ctx.send("Backup of: " + filter_string(ctx.guild.name) + " - Started...")

    if not os.path.exists(main_path):
        os.mkdir(main_path)

    for text_channel in ctx.guild.text_channels:

        if text_channel.category is not None:
            channel_name = filter_string(text_channel.category.name) + "_" + filter_string(text_channel.name)
        else:
            channel_name = filter_string(text_channel.name)


        channel_path = os.path.join(main_path, channel_name)
        if not os.path.exists(channel_path):
            os.mkdir(channel_path)


        markdown_name = filter_string(text_channel.name[0:20]) + ".md"
        file = open(os.path.join(channel_path, markdown_name), 'wb')

        header_text = "### " + text_channel.name + "\n\n"
        file.write((header_text).encode("utf-8"))

        try:
            async for message in text_channel.history(limit=discord_chat_history_depth_limit, oldest_first=True):
                output_string = "\n"
                was_attachment = False

                if anonymize_nicknames:
                    output_string += first_names[(int(message.author.id) + first_names_offset) % len(first_names)] + ": "
                else:
                    output_string += message.author.name + ": "

                for attachment in message.attachments:
                    was_attachment = True
                    attachment_file_name = str(attachment.id) + "_" + filter_string(attachment.filename)
                    attachment_file_path = os.path.join(channel_path, attachment_file_name)
                    await attachment.save(attachment_file_path)

                    if any(attachment_file_name.lower().endswith(image_format) for image_format in image_formats):
                        output_string += "\n![" + attachment.filename + "](" + attachment_file_name + "?raw=true)\n\n"
                    else:
                        output_string += "[" + attachment.filename + "](" + attachment_file_name + ")\n\n"

                if was_attachment:  ## If there's a picture, we want to also save the reactions to it
                    if message.reactions:
                        output_string += "|"
                    for reaction in message.reactions:
                        output_string += " "
                        if type(reaction.emoji) is type("string"):
                            output_string += reaction.emoji
                        else:
                            output_string += reaction.emoji.name
                        output_string += " - " + str(reaction.count) + " |"

                output_string += "\n\n"

                output_string += message.content
                output_string += "\n___"
                file.write((output_string).encode("utf-8"))

        except discord.errors.Forbidden:
            # No permissions
            print("Error: No permissions to " + str(text_channel.category) + " - " + str(text_channel))
            await ctx.send("Error: No permissions to " + str(text_channel.category) + " - " + str(text_channel))
        file.close()

    print("Backup of: " + filter_string(ctx.guild.name) + " - Finished.")

    zip_name, zip_path = zip_files(main_folder_name, main_path)

    await send_file_to_channel(ctx, zip_name, zip_path)

    if delete_after_upload:
        print("Deleting " + main_folder_name + " - Started...")
        try:
            shutil.rmtree(main_path)
            os.remove(zip_path)
            print("Deleting " + main_folder_name + " - Finished.")
        except OSError as e:
            print(e)



@bot.event
async def on_ready():
    printMessage("Bot " + bot_name + " - " + bot_version + " is now fully working.")
    printNewLines()
    printTabbed("Displaying logs:")
    printNewLines()


bot.run(token)