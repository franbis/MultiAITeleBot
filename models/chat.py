import enum

from sqlalchemy import Enum, Column, BigInteger, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship



Base = declarative_base()


# There are other roles and 'system' was replaced by 'developer'
# in the OpenAI API, tho it's better to keep this flexible for any
# AI that uses the more common standard.
class MessageRole(enum.Enum):
    system = 'system'
    assistant = 'assistant'
    user = 'user'
msg_role_enum = Enum(MessageRole, name='msg_role_enum')


class Chat(Base):
    __tablename__ = 'chats'

    # Telegram chat id.
    id = Column(BigInteger, primary_key=True)
    # Although Message with 'role' set to 'system' could be used, use
    # a string for simplicity.
    sys_msg = Column(String, nullable=True)
    last_msg_at = Column(DateTime(timezone=True), nullable=True)
    
    # Set 'lazy' to 'dynamic' to enable the use of queries.
    messages = relationship(
        'Message',
        back_populates='chat',
        passive_deletes=True,
        lazy='dynamic'
    )


    def get_context(self, max_items=None):
        """Return a list of messages to pass to the AI as context."""
        msgs = []

        if self.sys_msg:
            # Push the system message.
            msgs.append({
                'role': 'system',
                'content': self.sys_msg
            })

        # Get the messages from newest to oldest so that a
        # context limit can be applied.
        # NOTE: Telegram gives incremental ids to messages.
        q = self.messages.order_by(Message.id.desc())
        q = q.limit(max_items) if max_items else q
        # Push assistant and user messages.
        # Flip the list for ascended order.
        for msg in q.all()[::-1]:
            msgs.append({
                'name': f'@{msg.user_name}',
                'role': msg.role.name,
                'content': msg.content
            })

        return msgs


    def erase(self):
        """Delete all the messages."""
        self.messages.delete(synchronize_session=False)



class Message(Base):
    __tablename__ = 'messages'

    # NOTE: There is no need for a timestamp, Telegram gives incremental
    #       ids to messages and all is needed here is their order.

    # Telegram message id.
    id = Column(BigInteger, primary_key=True)
    # System messages don't need a user.
    user_name = Column(String, nullable=True)
    role = Column(msg_role_enum, nullable=False)
    content = Column(JSON)

    chat_id = Column(BigInteger, ForeignKey('chats.id', ondelete='CASCADE'))
    chat = relationship('Chat', back_populates='messages')