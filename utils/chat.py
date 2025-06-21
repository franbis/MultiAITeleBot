from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from models.chat import MessageRole, Chat, Message



def get_chat(ses, id):
    """
    Find a chat by id and return it.
    
    Args:
        ses:            Database session.
        id:             Chat's id.
    """
    return ses.get(Chat, id)


def get_or_create_chat(ses, id, config, *args, **kwargs):
    """
    Find a chat by id and return it, create it if nonexistent.
    
    Args:
        ses:            Database session.
        id:             Chat's id.
        config:         Bot configuration manager.
    """

    chat = None
    if not (chat := ses.get(Chat, id)):
        chat = Chat(
            id=id,
            sys_msg=config.get('chat.default_sys_msg'),
            *args,
            **kwargs
        )
        ses.add(chat)

    return chat


def add_msg(ses, id, user_name, chat_id, config, content, role=MessageRole.user):
    """
    Create and add a message to a chat.
    
    Args:
        ses:            Database session.
        id:             Chat's id.
        user_name:      Sender's username.
        config:         Bot configuration manager.
        content:        Message's content.
        role:           Message type.
    """

    chat = get_or_create_chat(ses, chat_id, config)
    chat.last_msg_at = datetime.now(timezone.utc)

    msg = Message(
        id=id,
        user_name=user_name,
        chat=chat,
        role=role,
        content=content
    )
    ses.add(msg)

    if chat.messages.count() > config.get('chat.max_msgs'):
        ses.delete(chat.messages.first())


def add_telegram_msg(ses, msg, config, content, role=MessageRole.user):
    """
    Create and add a message to a chat from a Telegram message.
    
    Args:
        ses:            Database session.
        msg:            Telegram message.
        config:         Bot configuration manager.
        content:        Message's content.
        role:           Message type.
    """

    add_msg(
        ses=ses,
        id=msg.id,
        user_name=msg.from_user.username,
        chat_id=msg.chat.id,
        config=config,
        content=content,
        role=role
    )


def purge_old_chats(ses, config):
    """
    Delete chats older than the days set at 'chat.purge_days' in
    the bot configuration.

    Args:
        ses:        Database session.
        config:     Bot configuration manager.
    """

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.get('chat.purge_days'))
    stmt = delete(Chat).where(Chat.last_msg_at < cutoff)
    ses.execute(stmt)