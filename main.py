from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

def get_token(token_purpose: str) -> str:
    if token_purpose == "bot":
        filename = "bot_token.txt"
    elif token_purpose == "vk":
        filename = "vk_token.txt"
    else:
        return ""
    try:
        with open(filename, "r") as token_file:
            return_value = token_file.read()
    except:
        return ""
    token_file.close()
    return return_value

def show_help(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown(
        """Ниже под страницей подразумевается какая-либо публичная страница ВКонтакте. В последующих обновлениях при необходимости будут добавляться и другие платформы.\n*Список команд:*
    */meme* - Прислать мем
    */memepages* - Показать список страниц, из которых я могу присылать мемы в эту беседу
    */memepages_add* - Добавление страниц(-ы) в список. После вызова этой команды пришлите список коротких имен страниц через пробел
    */memepages_remove* - Удалить страницу(-ы) из списка. После вызова этой команды пришлите список коротких имен страниц через пробел
    */memepages_truncate* - Полностью очистить список страниц, из которых я могу присылать мемы в эту беседу""",
        quote=True
    )

def send_meme(update: Update, context: CallbackContext) -> None:
    pass

def show_memepages(update: Update, context: CallbackContext) -> None:
    index = 1
    reply_message = ""
    try:
        for page in context.chat_data["memepages"]:
            reply_message += f"{index}) *{page}*\n"
            index += 1
    except KeyError:
        reply_message = "Список страниц пуст. Добавьте что-нибудь, иначе я не смогу ничего отправлять"
    update.message.reply_markdown(
        reply_message,
        quote=True
    )

def add_memepages(update: Update, context: CallbackContext) -> None:
    context.chat_data["adding_user_id"] = update.effective_user.id
    update.message.reply_markdown(
        "Отправьте короткие имена страниц *через пробел*, которых вы хотите добавить (короткие имена могут быть найдены в ссылке на страницу)",
        quote=True
    )

def remove_memepages(update: Update, context: CallbackContext) -> None:
    if "memepages" not in context.chat_data.keys():
        update.message.reply_markdown(
            "Чтобы удалять страницы, для начала их нужно добавить, а список пуст",
            quote=True
        )
        return
    context.chat_data["deleting_user_id"] = update.effective_user.id
    update.message.reply_markdown(
        "Отправьте короткие имена страниц *через пробел*, которых вы хотите удалить (если не знаете, можете уточнить имена страниц командой /memepages)",
        quote=True
    )

def truncate_memepages(update: Update, context: CallbackContext) -> None:
    if "memepages" not in context.chat_data.keys():
        update.message.reply_markdown(
            "Чтобы очищать список, он не должен быть пустой",
            quote=True
        )
        return
    context.chat_data.pop("memepages", None)
    update.message.reply_markdown(
        "Список страниц был очищен",
        quote=True
    )

def memepages_modifying_type(update: Update, context: CallbackContext) -> str:
    user_id = update.effective_user.id
    try:
        if context.chat_data["adding_user_id"] == user_id:
            return "adding"
    except KeyError:
        pass
    try:
        if context.chat_data["deleting_user_id"] == user_id:
            return "deleting"
    except KeyError:
        pass
    return ""

def add_memepages_to_chat_info(context: CallbackContext, pages_to_add: set) -> str:
    """Function returns a reply that bot sends to user
    """

    added_pages = set()
    if "memepages" not in context.chat_data.keys():
        context.chat_data["memepages"] = []
    for page in pages_to_add:
        if page not in context.chat_data["memepages"]:
            context.chat_data["memepages"].append(page)
            added_pages.add(page)
    not_added_pages = pages_to_add.difference(added_pages)
    reply_str = ""
    if added_pages:
        reply_str = "Добавлены страницы: "
        for page in added_pages:
            reply_str += f"{page}, "
        reply_str = reply_str[:-2] + "\n"
    if not_added_pages:
        reply_str += "Страницы "
        for page in not_added_pages:
            reply_str += f"{page}, "
        reply_str = reply_str[:-2] + " не были добавлены, потому что уже есть в списке"
    return reply_str

def delete_memepages_from_chat_info(context: CallbackContext, pages_to_delete: set) -> str:
    """Function returns a reply that bot sends to user
    """
    deleted_pages = set()
    for page in pages_to_delete:
        if page in context.chat_data["memepages"]:
            context.chat_data["memepages"].remove(page)
            deleted_pages.add(page)

    if not context.chat_data["memepages"]:
        context.chat_data.pop("memepages", None)
    not_deleted_pages = pages_to_delete.difference(deleted_pages)
    reply_str = ""
    if deleted_pages:
        reply_str = "Удалены страницы: "
        for page in deleted_pages:
            reply_str += f"{page}, "
        reply_str = reply_str[:-2] + "\n"
    if not_deleted_pages:
        reply_str += "Страницы "
        for page in not_deleted_pages:
            reply_str += f"{page}, "
        reply_str = reply_str[:-2] + " не были удалены, потому что их не было в списке"
    return reply_str

def check_memepages_existence(memepages: set) -> list:
    """The function returns a list of existing pages from the given set
    """
    
    #штуки с vk api, щас лень писать
    pass

def handle_text_message(update: Update, context: CallbackContext) -> None:
    message_text = update.effective_message.text
    sender_id = update.effective_user.id
    
    modtype = memepages_modifying_type(update, context)
    if modtype == "adding":
        #добавить сюда проверку на существование всех страниц, которых нужно добавить
        context.chat_data.pop("adding_user_id", None)
        pages_to_add = set(message_text.split())
        update.message.reply_markdown(
            add_memepages_to_chat_info(context, pages_to_add),
            quote=True
        )

    elif modtype == "deleting":
        context.chat_data.pop("deleting_user_id", None)
        pages_to_delete = set(message_text.split())
        update.message.reply_markdown(
            delete_memepages_from_chat_info(context, pages_to_delete),
            quote=True
        )

def main() -> None:
    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("help", show_help))
    dispatcher.add_handler(CommandHandler("meme", send_meme))
    dispatcher.add_handler(CommandHandler("memepages", show_memepages))
    dispatcher.add_handler(CommandHandler("memepages_add", add_memepages))
    dispatcher.add_handler(CommandHandler("memepages_remove", remove_memepages))
    dispatcher.add_handler(CommandHandler("memepages_truncate", truncate_memepages))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_text_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    bot_token    = get_token("bot")
    vk_api_token = get_token("vk")
    main()
