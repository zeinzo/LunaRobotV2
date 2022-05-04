import importlib
import time
import re
from sys import argv
from typing import Optional

from lunaBot import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from lunaBot.modules import ALL_MODULES
from lunaBot.modules.helper_funcs.chat_status import is_user_admin
from lunaBot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

LUNA_IMG = "https://telegra.ph/file/d924c9bbe8eff97e5dd17.jpg"

PM_START_TEXT = """
**ɪ ᴀᴍ ɴᴏɪɴᴏɪ ɴᴏɪɴᴏɪ🌸🤖** [ㅤ](https://telegra.ph/file/d924c9bbe8eff97e5dd17.jpg)
️➖➖➖➖➖➖➖➖➖➖➖➖➖
**ɪ'ᴍ ᴀ ᴘᴏᴡᴇʀғᴜʟʟ ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇʀ ʙᴏᴛ ᴡɪᴛʜ ᴄᴏᴏʟ ᴍᴏᴅᴜʟᴇs. ғᴇᴇʟ ғʀᴇᴇ ᴛᴏ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs!!**
️➖➖➖➖➖➖➖➖➖➖➖➖➖
☉ **ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ғᴏʀ ᴍᴏʀᴇ.**
"""

buttons = [
    [
        InlineKeyboardButton(text="ᴜᴘᴅᴀᴛᴇ", url="http://t.me/BAZIGAR_XD"),
        InlineKeyboardButton(text="ᴀʙᴏᴜᴛ", callback_data="luna_"),
        InlineKeyboardButton(text="sᴜᴘᴘᴏʀᴛ", url="http://t.me/NOINOISUPPORT"),
    ],
    [
        InlineKeyboardButton(text="ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 🌸", url="http://t.me/NOINOI_BOT?startgroup=true"),
        InlineKeyboardButton(
            text="ᴍᴜsɪᴄ ᴄᴏᴍᴍᴀɴᴅs", callback_data="luna_basichelp"
        ),
    ],
    [
        
        InlineKeyboardButton(
            text="ᴍᴀɴᴀɢᴇʀ ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_back"),
    ],
]


HELP_STRINGS = """
**Main commands:**  [ㅤ](https://telegra.ph/file/d924c9bbe8eff97e5dd17.jpg)
❂ /start: sᴛᴀʀᴛ ᴍᴇ ʏᴏᴜ ʜᴀᴠᴇ ᴘʀᴏʙᴀʙʟʏ ᴀʟʀᴇᴀᴅʏ ᴜsᴇᴅ ᴛʜɪs..
❂ /help: Sends this message; I'll tell you more about myself.

ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ᴇɪᴛʜᴇʀ ʙᴇ ᴜsᴇᴅ ᴇɪᴛʜᴇʀ / ᴏʀ  ! ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʀᴇᴘᴏʀᴛ ᴀɴʏ ʙᴜɢs ᴏʀ ɴᴇᴇᴅ ʜᴇʟᴘ ᴡɪᴛʜ sᴇᴛᴛɪɴɢ ᴜᴘ ᴀʟɪɴᴀ ʀᴇᴀᴄʜ ᴜs ᴀᴛ ʜᴇᴀʀ"""



DONATE_STRING = """ʜᴇʜᴇ ʏᴏᴜ ᴄᴀɴ ᴅᴏɴᴇᴛ ғʀᴏᴍ ʜᴇᴀʀ!
 [NOINOI](https://t.me/NOINOISUPPORT) ❤️
"""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("lunaBot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


@run_async
def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@run_async
def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            update.effective_message.reply_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_photo(
            LUNA_IMG, caption= "I'm awake already!\n<b>Haven't slept since:</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Sᴜᴘᴘᴏʀᴛ", url="https://t.me/lunaXresso")]]
            ),
        )
        
def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass


@run_async
def luna_about_callback(update, context):
    query = update.callback_query
    if query.data == "luna_":
        query.message.edit_text(
            text="""Hi again! I'am a full-fledged group management bot built to help you manage your group easily.\n
                    \nI can do lot of stuff, some of them are:
                    \n• Restrict users who flood your chat using my anti-flood module.
                    \n• Safeguard your group with the advanced and handy Antispam system.
                    \n• Greet users with media + text and buttons, with proper formatting.
                    \n• Save notes and filters with proper formatting and reply markup.\n
                    \nNote: I need to be promoted with proper admin permissions to fuction properly.\n
                    \nCheck Setup Guide to learn on setting up the bot and on help to learn more.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Setup Guide", callback_data="luna_aselole"
                        ),
                        InlineKeyboardButton(
                            text="T & C", callback_data="luna_puqi"
                        ),
                    ],
                    [InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="luna_back")],
                ]
            ),
        )
    elif query.data == "luna_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

    elif query.data == "luna_basichelp":
        query.message.edit_text(
            text=f"**──「 Basic Guide 」──**"
            f"\n\n1.) first, add me to your group.\n"
            f"2.) then promote me as admin and give all permissions except anonymous admin.\n"
            f"3.) after promoting me, type /reload in group to update the admin list.\n"
            f"4.) add @LunaAssistant to your group or type /join to invite her.\n"
            f"5.) turn on the video chat first before start to play music.\n"
            f"\n📌 if userbot doesn't join voice chat make sure voice chat is active, or type /leave then type /join again..",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="📗 Basic CMD", callback_data="luna_admin"),
                    InlineKeyboardButton(text="📘 Advanced CMD", callback_data="luna_notes"),
                 ],
                 [
                    InlineKeyboardButton(text="📙 Admin CMD", callback_data="luna_support"),
                 ],
                 [
                    InlineKeyboardButton(text="Back", callback_data="luna_back"),
                 
                 ]
                ]
            ),
        )
    elif query.data == "luna_admin":
        query.message.edit_text(
            text=f"**──「 Basic Guide 」──**"
            f"\n\n/play (song name) - play song from youtube"
            f"\n/ytp (song name) - play song directly from"
            f"\nB/stream (reply to audio) - play song using audio file."
            f"\n/playlist - show the list song in queue"
            f"\n/song (song name) - download song from youtube."
            f"\n/search (video name) - search video from youtube detailed."
            f"\n/lyric - (song name) lyrics scrapper",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="luna_basichelp")]]
            ),
        )

    elif query.data == "luna_notes":
        query.message.edit_text(
            text=f"──「 Advanced CMD 」──\n\n"
            f"/start (in group) - see the bot alive status"
            f"\n/reload - reload bot and refresh the admin list"
            f"\n/ping - check the bot ping status"
            f"\n/uptime - check the bot uptime status"
            f"\n/id - show the group/user id & other",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="luna_basichelp")]]
            ),
        )
    elif query.data == "luna_support":
        query.message.edit_text(
            text=f"──「 Admin CMD 」──\n"
            f"\n/player - show the music playing status"
            f"\n/pause - pause the music streaming"
            f"\n/resume - resume the music was paused"
            f"\n/skip - skip to the next song"
            f"\n/end - stop music streaming"
            f"\n/join - invite userbot join to your group"
            f"\n/leave - order the userbot to leave your group"
            f"\n/auth - authorized user for using music bot"
            f"\n/unauth - unauthorized for using music bot"
            f"\n/control - open the player settings panel"
            f"\n/delcmd (on | off) - enable / disable del cmd feature"
            f"\n/music (on / off) - disable / enable music player in your group",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Back", callback_data="luna_basichelp"),
                 
                 ]
                ]
            ),
        )
    elif query.data == "luna_credit":
        query.message.edit_text(
            text=f"<b> `Cʀᴇᴅɪᴛ Fᴏʀ Lᴜɴᴀ Dᴇᴠ's` </b>\n"
            f"\nHᴇʀᴇ Sᴏᴍᴇ Dᴇᴠᴇʟᴏᴘᴇʀs Hᴇʟᴘɪɴɢ Iɴ Mᴀᴋɪɴɢ Tʜᴇ Lᴜɴᴀ",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Alina", url="https://t.me/rizexx"),
                    InlineKeyboardButton(text="Nao", url="https://t.me/xgothboi"),
                 ],
                 [
                    InlineKeyboardButton(text="Yui", url="https://t.me/Badboyanim"),
                    InlineKeyboardButton(text="Luna", url="https://t.me/tdrki_1"),
                 ],
                 [
                    InlineKeyboardButton(text="Back", callback_data="luna_basichelp"),
                 
                 ]
                ]
            ),
        )

    elif query.data == "luna_aselole":
        query.message.edit_text(
            text=f"｢ Setup Guide 」\n"
                 f"\nYou can add me to your group by clicking this link and selecting the chat.\n"
                 f"\nRead Admin Permissions and Anti-spam for basic info.\n"
                 f"\nRead Detailed Setup Guide to learn about setting up the bot in detail. (Recommended)\n"
                 f"\nIf you do need help with further instructions feel free to ask in @lunaXresso.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Admins Permissions", callback_data="luna_asu"),
                    InlineKeyboardButton(text="Anti Spam", callback_data="luna_asi"),
                 ],
                 [
                    InlineKeyboardButton(text="Back", callback_data="luna_"),
                 
                 ]
                ]
            ),
        )

    elif query.data == "luna_asu":
        query.message.edit_text(
            text=f"｢ Admin Permissions 」\n"
                     f"\nTo avoid slowing down, Luna caches admin rights for each user. This cache lasts about 10 minutes; this may change in the future. This means that if you promote a user manually (without using the /promote command), Luna will only find out ~10 minutes later.\n"
                    f"\nIf you want to update them immediately, you can use the /admincache or /reload command, that'll force Luna to check who the admins are again and their permissions\n"
                    f"\nIf you are getting a message saying:\nYou must be this chat administrator to perform this action!\n"
                    f"\nThis has nothing to do with Luna's rights; this is all about YOUR permissions as an admin. Luna respects admin permissions; if you do not have the Ban Users permission as a telegram admin, you won't be able to ban users with Luna. Similarly, to change Luna settings, you need to have the Change group info permission.\n"
                    f"\nThe message very clearly states that you need these rights - not Luna.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="luna_aselole")]]
            ),
        )

    elif query.data == "luna_asi":
        query.message.edit_text(
            text=f"｢ Anti-Spam Settings 」\n"
                     f"\nAntispam: "
                     f"\nBy enabling this, you can protect your groups free from scammers/spammers.\nRun /antispam on in your chat to enable.\nAppeal Chat: @lunaXresso\n"
                     f"\n✪ Anti-Flood allows you to keep your chat clean from flooding."
                     f"\n✪ With the help of Blaclists you can blacklist words,sentences and stickers which you don't want to be used by group members."
                     f"\n✪ By enabling Reports, admins get notified when users reports in chat."
                     f"\n✪ Locks allows you to lock/restrict some comman items in telegram world."
                     f"\n✪ Warnings allows to warn users and set auto-warns. "
                     f"\n✪ Welcome Mute helps you prevent spambots or users flooding/spamming your group. Checl Greetings for more info",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="luna_aselole")]]
            ),
        )

    elif query.data == "luna_puqi":
        query.message.edit_text(
            text=f" ｢ Terms and Conditions 」\n"
                f"\nTo use this bot, You need to agree with Terms and Conditions.\n"
                f"\n✪ If someone is spamming your group, you can use report feature from your Telegram Client."
                f"\n✪ Make sure antiflood is enabled, so that users cannot flood/spam your chat."
                f"\n✪ Do not spam commands, buttons, or anything in bot PM, else you will be Ignored by bot or Gbanned."
                f"\n✪ If you need to ask anything about this bot or you need help, reach us at @lunaXresso"
                f"\n✪ Make sure you read rules and follow them when you join Support Chat."
                f"\n✪ Spamming in Support Chat, will reward you GBAN and reported to Telegram as well.\n"
                f"\nTerms & Conditions can be changed anytime.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                  [
                     InlineKeyboardButton(text="Credits", callback_data="luna_angjay"),
                     InlineKeyboardButton(text="Back", callback_data="luna_"),
                  ]
                ]
            ),
        )

    elif query.data == "luna_angjay":
        query.message.edit_text(
            text=f"Luna is a powerful bot for managing groups with additional features.\n"
              f"\nLuna's Licensed Under The GNU (General Public License v3.0)\n"
              f"\nIf you have any question about Luna,"
              f"\nreach us at Support Chat.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                  [
                     InlineKeyboardButton(text="Back", callback_data="luna_puqi"),
                     InlineKeyboardButton(text="☎️ Support", url=f"https://t.me/lunaXresso"),
                  ]
                ]
            ),
        )   

@run_async
def Source_about_callback(update, context):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text=""" Hi.. ɪ'ᴀᴍ Lᴜɴᴀ*
                 \nHere is the [sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ](https://www Xhamster.com) .""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Back", callback_data="source_back")
                 ]
                ]
            ),
        )
    elif query.data == "source_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

@run_async
def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Help",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Hᴇʟᴘ ❔",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Sᴜᴘᴘᴏʀᴛ Cʜᴀᴛ 📢 ",
                            url="https://t.me/{}".format(SUPPORT_CHAT),
                        )
                    ],
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Sepertinya tidak ada pengaturan khusus pengguna yang tersedia :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


@run_async
def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


@run_async
def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 1963422158 and DONATION_LINK:
            update.effective_message.reply_text(
                "You can also donate to the person currently running me "
                "[here]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(f"@{SUPPORT_CHAT}", "I Aᴍ Aʟɪᴠᴇ 🔥")
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)

    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_.*")

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")

    about_callback_handler = CallbackQueryHandler(luna_about_callback, pattern=r"luna_")
    source_callback_handler = CallbackQueryHandler(Source_about_callback, pattern=r"source_")

    donate_handler = CommandHandler("donate", donate)
    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, clean=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
