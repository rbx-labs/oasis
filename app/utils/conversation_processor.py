from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Tuple
import time
from app.schemas.audio import ConversationCreate
from app.crud.crud_conversation import crud_conversation
import logging

logger = logging.getLogger(__name__)

class ConversationProcessor:
    @staticmethod
    async def create_conversation(
        audio_id: int,
        conversation_data: Dict[str, str],
        db: Session
    ) -> Any:
        """
        Create conversation entry from speaker data
        Args:
            audio_id: ID of the audio file
            conversation_data: Dictionary containing speaker and content
            db: Database session
        Returns:
            Created conversation entry
        """
        try:
            conversation_in = ConversationCreate(
                audio_id=audio_id,
                speaker=conversation_data["speaker"],
                content=conversation_data["content"]
            )
            db_conversation = crud_conversation.create(db, obj_in=conversation_in)
            logger.info(f"Created conversation entry with ID: {db_conversation.id}")
            
            return db_conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error creating conversation: {str(e)}"
            ) 