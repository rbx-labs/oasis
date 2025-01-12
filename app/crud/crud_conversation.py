from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.crud_base import CRUDBase
from app.models.conversation import Conversation
from app.schemas.audio import ConversationCreate, Conversation as ConversationSchema

class CRUDConversation(CRUDBase[Conversation, ConversationCreate, ConversationSchema]):
    def get_by_audio_id(self, db: Session, *, audio_id: int) -> List[Conversation]:
        return db.query(self.model).filter(Conversation.audio_id == audio_id).all()

crud_conversation = CRUDConversation(Conversation) 