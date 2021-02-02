import requests
import random
import time
from telegram import (
    Update,
    InputMediaPhoto
)
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

def vk_query_response(method: str, **params) -> dict:
    query = "https://api.vk.com/method/{_method}?v=5.126&access_token={token}{parameters}".format(
        _method     = method,
        token       = vk_api_token,
        parameters  = "".join([f"&{key}={value}" for key, value in params.items()])
    )
    return requests.get(query).json()

def show_help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        """Ниже под страницей подразумевается какая-либо публичная страница ВКонтакте. В последующих обновлениях при необходимости будут добавляться и другие платформы.\nСписок команд:
        /meme - Прислать мем
        /memepages - Показать список страниц, из которых я могу присылать мемы в эту беседу
        /memepages_add - Добавление страниц(-ы) в список. После вызова этой команды пришлите список коротких имен страниц через пробел
        /memepages_remove - Удалить страницу(-ы) из списка. После вызова этой команды пришлите список коротких имен страниц через пробел
        /memepages_truncate - Полностью очистить список страниц, из которых я могу присылать мемы в эту беседу
        /memepages_export - Список коротких имен страниц через пробел (не путать с оформленным /memepages) для удобства экспортирования списка в другие группы""",
        quote=True
    )

def send_meme(update: Update, context: CallbackContext) -> None:
    start_time = time.time()
    if "memepages" not in context.chat_data.keys():
        update.message.reply_text(
            "Я не могу отправлять записи, если список пуст. Добавьте страницы в список командой /memepages_add",
            quote=True
        )
        return
    posts_count = 100
    random_domain = random.choice(tuple(context.chat_data["memepages"])) #random.choice не поддерживает сеты
    response = vk_query_response(
        "wall.get",
        domain = random_domain,
        count  = posts_count
    )
    if "response" not in response.keys():
        update.message.reply_text("Сервис недоступен, повторите попытку позже")
        return
    try:
        posts = [post for post in response["response"]["items"] if post["marked_as_ads"] == 0]
    except KeyError:
        print("no marked as ads")
        posts = [post for post in response["response"]["items"]]
    if not posts:
        update.message.reply("Стена одного из сообществ, добавленного в список пока пуста, отправьте команду еще раз")
        return
    wall_post = random.choice(posts)
    try:
        attachments = wall_post["attachments"]
    except KeyError:
        attachments = []
    photo_urls = [attachment["photo"]["sizes"][-1]["url"] for attachment in attachments if attachment["type"] == "photo"]
    message_caption = wall_post["text"]+f"\n\nВзято из vk.com/{random_domain}"
    if not photo_urls:
        update.message.reply_text(
            message_caption,
            quote=True
        )
    elif len(photo_urls) == 1:
        update.message.reply_photo(
            photo   = photo_urls[0],
            caption = message_caption,
            quote   = True
        )
    else:
        media_list = [InputMediaPhoto(media=url) for url in photo_urls]
        media_list[0].caption = message_caption
        update.message.reply_media_group(
            media   = media_list,
            quote   = True
        )
    #benchmarks
    #print(f"Meme sending query responded in {time.time() - start_time} seconds")

def get_pages_info(screen_names: set) -> list:
    response = vk_query_response(
        "groups.getById",
        group_ids=",".join([name for name in screen_names])
    )
    try:
        return response["response"]
    except KeyError:
        return []

def show_memepages(update: Update, context: CallbackContext) -> None:
    try:
        full_names = {page_info["screen_name"] : page_info["name"] for page_info in get_pages_info(context.chat_data["memepages"])}
        reply_message = "\n".join([f"{index+1}) {full_name} ({screen_name})" for index, (screen_name, full_name) in enumerate(full_names.items())])
    except KeyError:
        reply_message = "Список страниц пуст. Добавьте что-нибудь, иначе я не смогу ничего отправлять"
    update.message.reply_text(
        reply_message,
        quote=True
    )

def add_memepages(update: Update, context: CallbackContext) -> None:
    context.chat_data["adding_user_id"] = update.effective_user.id
    update.message.reply_text(
        "Отправьте короткие имена страниц через пробел, которых вы хотите добавить (короткие имена могут быть найдены в ссылке на страницу)",
        quote=True
    )

def remove_memepages(update: Update, context: CallbackContext) -> None:
    if "memepages" not in context.chat_data.keys():
        update.message.reply_text(
            "Чтобы удалять страницы, для начала их нужно добавить, а список пуст",
            quote=True
        )
        return
    context.chat_data["deleting_user_id"] = update.effective_user.id
    update.message.reply_text(
        "Отправьте короткие имена страниц через пробел, которых вы хотите удалить (если не знаете, можете уточнить имена страниц командой /memepages)",
        quote=True
    )

def truncate_memepages(update: Update, context: CallbackContext) -> None:
    if "memepages" not in context.chat_data.keys():
        update.message.reply_text(
            "Чтобы очищать список, он не должен быть пустой",
            quote=True
        )
        return
    context.chat_data.pop("memepages", None)
    update.message.reply_text(
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
    if "memepages" not in context.chat_data.keys():
        context.chat_data["memepages"] = set()

    #находим страницы, которые существуют в вк
    pages_info = get_pages_info(pages_to_add)
    exist_pages = set([page["screen_name"] for page in pages_info])

    #несуществующие страницы - те которыe есть в pages_to_add, но нет в exist_pages
    nonexist_pages = pages_to_add.difference(exist_pages)

    #находим и вычитаем закрытые страницы
    closed_pages = set([page["screen_name"] for page in pages_info if page["is_closed"] == 1])
    exist_pages.difference_update(closed_pages)

    #недобавленные страницы - те, которые уже есть в context.chat_data["memepages"]
    not_added_pages = exist_pages.intersection(context.chat_data["memepages"])

    #добавленные страницы - те, которые есть в exist_pages но нет в context.chat_data["memepages"]
    added_pages = exist_pages.difference(context.chat_data["memepages"])

    #обновляем множество чатов через объединение с существующими
    context.chat_data["memepages"].update(exist_pages)

    #генерируем ответ одной строкой
    reply_str = ""
    if added_pages:
        if added_pages == pages_to_add:
            reply_str += "Все указанные страницы добавлены в список"
        else:
            reply_str += "{page_addition_case}: {list_of_pages}\n".format(
                page_addition_case = "Добавлены страницы" if len(added_pages) > 1 else "Добавлена страница",
                list_of_pages      = ", ".join([page for page in added_pages])
        )
    if not_added_pages:
        reply_str += "{pages_case} {list_of_pages} {were_not_added_case}, потому что уже есть в списке\n".format(
            pages_case          = "Страницы" if len(not_added_pages) > 1 else "Страница",
            list_of_pages       = ", ".join([page for page in not_added_pages]),
            were_not_added_case = "не были добавлены" if len(not_added_pages) > 1 else "не была добавлена"
        )
    if nonexist_pages:
        reply_str += "{pages_case} {list_of_pages} не существует, проверьте правильность написания коротких имен\n".format(
            pages_case    = "Страниц" if len(nonexist_pages) > 1 else "Страницы",
            list_of_pages = ",".join([page for page in nonexist_pages])
        )
    if closed_pages:
        reply_str += "{pages_case} {list_of_pages} {closed_case}, я не смогу брать оттуда записи\n".format(
            pages_case    = "Страницы" if len(closed_pages) > 1 else "Страница",
            list_of_pages = ", ".join(closed_pages),
            closed_case   = "закрыты" if len(closed_pages) > 1 else "закрыта"
        )

    return reply_str

def delete_memepages_from_chat_info(context: CallbackContext, pages_to_delete: set) -> str:
    """Function returns a reply that bot sends to user
    """

    #удаленные страницы - те, которые есть в context.chat_data["memepages"]
    deleted_pages = pages_to_delete.intersection(context.chat_data["memepages"])

    #неудаленные - те, которых нет в deleted_pages но есть в pages_to_delete
    not_deleted_pages = pages_to_delete.difference(deleted_pages)

    #обновляем множество чатов через разницу с теми, которые нужно удалить
    context.chat_data["memepages"].difference_update(pages_to_delete)

    if not context.chat_data["memepages"]:
        context.chat_data.pop("memepages", None)

    #генерируем ответ одной строкой
    reply_str = ""
    if deleted_pages:
        reply_str += "{deleted_pages_case}: {pages_list}\n".format(
            deleted_pages_case = "Удалены страницы" if len(deleted_pages) > 1 else "Удалена страница",
            pages_list         = ", ".join([page for page in deleted_pages])
        )
    if not_deleted_pages:
        reply_str += "{pages_case} {pages_list} {were_not_deleted_case}, потому что их не было в списке".format(
            pages_case            = "Страницы" if len(not_deleted_pages) > 1 else "Страница",
            pages_list            = ", ".join([page for page in not_deleted_pages]),
            were_not_deleted_case = "не были удалены" if len(not_deleted_pages) > 1 else "не была удалена"
        )
    return reply_str

def handle_text_message(update: Update, context: CallbackContext) -> None:
    message_text = update.effective_message.text
    sender_id = update.effective_user.id
    
    modtype = memepages_modifying_type(update, context)
    if modtype == "adding":
        #добавить сюда проверку на существование всех страниц, которых нужно добавить
        context.chat_data.pop("adding_user_id", None)
        pages_to_add = set(message_text.split())
        update.message.reply_text(
            add_memepages_to_chat_info(context, pages_to_add),
            quote=True
        )

    elif modtype == "deleting":
        context.chat_data.pop("deleting_user_id", None)
        pages_to_delete = set(message_text.split())
        update.message.reply_text(
            delete_memepages_from_chat_info(context, pages_to_delete),
            quote=True
        )

def send_screen_names(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        " ".join(context.chat_data["memepages"]),
        quote=True
    )

def main() -> None:
    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("help", show_help))
    dispatcher.add_handler(CommandHandler("meme", send_meme, run_async=True)) #too slow query to run without async
    dispatcher.add_handler(CommandHandler("memepages", show_memepages))
    dispatcher.add_handler(CommandHandler("memepages_add", add_memepages))
    dispatcher.add_handler(CommandHandler("memepages_remove", remove_memepages))
    dispatcher.add_handler(CommandHandler("memepages_truncate", truncate_memepages))
    dispatcher.add_handler(CommandHandler("memepages_export", send_screen_names))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_text_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    bot_token    = get_token("bot")
    vk_api_token = get_token("vk")
    main()
