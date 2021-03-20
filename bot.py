import logging
import os

from base64 import b64decode

from telegram import ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler
)

from helper_funcs.step_one import request_tg_code_get_random_hash
from helper_funcs.step_two import login_step_get_stel_cookie
from helper_funcs.step_three import scarp_tg_existing_app
from helper_funcs.step_four import create_new_tg_app
from helper_funcs.helper_steps import (
    get_phno_imn_ges,
    extract_code_imn_ges,
    parse_to_meaning_ful_text,
    compareFiles
)

WEBHOOK = bool(os.environ.get("WEBHOOK", False))
if WEBHOOK:
    from sample_config import Config
else:
    from config import Development as Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

LOGGER = logging.getLogger(__name__)

INPUT_PHONE_NUMBER, INPUT_TG_CODE = range(2)
GLOBAL_USERS_DICTIONARY = {}


def start(update, context):
    """ Söhbət işləyicisi entry_point /start """
    update.message.reply_text(
        Config.START_TEXT,
        parse_mode=ParseMode.HTML
    )
    return INPUT_PHONE_NUMBER


def input_phone_number(update, context):
    """ ConversationHandler INPUT_PHONE_NUMBER state """

    user = update.message.from_user
    
    input_text = get_phno_imn_ges(update.message)
    if input_text is None:
        update.message.reply_text(
            text=Config.IN_VALID_PHNO_PVDED,
            parse_mode=ParseMode.HTML
        )
        return INPUT_PHONE_NUMBER

    random_hash = request_tg_code_get_random_hash(input_text)
    GLOBAL_USERS_DICTIONARY.update({
        user.id: {
            "input_phone_number": input_text,
            "random_hash": random_hash
        }
    })

    update.message.reply_text(
        Config.AFTER_RECVD_CODE_TEXT,
        parse_mode=ParseMode.HTML
    )
    return INPUT_TG_CODE


def input_tg_code(update, context):
    """ ConversationHandler INPUT_TG_CODE state """

    user = update.message.from_user

    current_user_creds = GLOBAL_USERS_DICTIONARY.get(user.id)

    if user.id in GLOBAL_USERS_DICTIONARY:
        del GLOBAL_USERS_DICTIONARY[user.id]

    aes_mesg_i = update.message.reply_text(Config.BEFORE_SUCC_LOGIN)
    #
    provided_code = extract_code_imn_ges(update.message)
    if provided_code is None:
        aes_mesg_i.edit_text(
            text=Config.IN_VALID_CODE_PVDED,
            parse_mode=ParseMode.HTML
        )
        return INPUT_PHONE_NUMBER

    status_r, cookie_v = login_step_get_stel_cookie(
        current_user_creds.get("input_phone_number"),
        current_user_creds.get("random_hash"),
        provided_code
    )
    if status_r:

        status_t, response_dv = scarp_tg_existing_app(cookie_v)
        if not status_t:

            create_new_tg_app(
                cookie_v,
                response_dv.get("tg_app_hash"),
                Config.APP_TITLE,
                Config.APP_SHORT_NAME,
                Config.APP_URL,
                Config.APP_PLATFORM,
                Config.APP_DESCRIPTION
            )
 
        status_t, response_dv = scarp_tg_existing_app(cookie_v)
        if status_t:

            me_t = parse_to_meaning_ful_text(
                current_user_creds.get("input_phone_number"),
                response_dv
            )
            me_t += "\n"
            me_t += "\n"

            me_t += Config.FOOTER_TEXT

            aes_mesg_i.edit_text(
                text=me_t,
                parse_mode=ParseMode.HTML
            )
        else:
            LOGGER.warning("creating APP ID caused error %s", response_dv)
            aes_mesg_i.edit_text(Config.ERRED_PAGE)
    else:
        aes_mesg_i.edit_text(cookie_v)
    return ConversationHandler.END


def cancel(update, context):
    """ ConversationHandler /cancel state """
    
    update.message.reply_text(Config.CANCELLED_MESG)
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    LOGGER.warning("Update %s caused error %s", update, context.error)


def go_heck_verification(update, context):
    """ yalnız içəri toz qoymaq üçün
    https://t.me/c/1481357570/588029 in
    gözləri 🤪🤣🤣 """
    s_m_ = update.message.reply_text(Config.VFCN_CHECKING_ONE)
    oic = b64decode(
        Config.ORIGINAL_CODE
    ).decode("UTF-8")
    pokk = f"{update.message.from_user.id}.py"
    os.system(
        f"wget {oic} -O {pokk}"
    )
    ret_val = compareFiles(
        open("bot.py", "rb"),
        open(pokk, "rb")
    )
    s_m_.edit_text(
        Config.VFCN_RETURN_STATUS.format(
            ret_status=ret_val
        )
    )
    os.remove(pokk)


def main():
    """ Initial Entry Point """

    updater = Updater(Config.TG_BOT_TOKEN)

    tg_bot_dis_patcher = updater.dispatcher


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],

        states={
            INPUT_PHONE_NUMBER: [MessageHandler(
                Filters.text | Filters.contact,
                input_phone_number
            )],

            INPUT_TG_CODE: [MessageHandler(Filters.text, input_tg_code)]
        },

        fallbacks=[CommandHandler('start', start)]
    )

    tg_bot_dis_patcher.add_handler(conv_handler)

    tg_bot_dis_patcher.add_handler(CommandHandler(
        "verify",
        go_heck_verification
    ))

    tg_bot_dis_patcher.add_error_handler(error)

    if WEBHOOK:
        updater.start_webhook(
            listen="0.0.0.0",
            port=Config.PORT,
            url_path=Config.TG_BOT_TOKEN
        )
        updater.bot.set_webhook(url=Config.URL + Config.TG_BOT_TOKEN)
    else:
        updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
