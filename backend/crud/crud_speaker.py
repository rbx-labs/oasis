from typing import List, Optional
from sqlalchemy.orm import Session
from crud.crud_base import CRUDBase
from models.speaker import Speaker
from schemas.speaker import SpeakerCreate, SpeakerUpdate

class CRUDSpeaker(CRUDBase[Speaker, SpeakerCreate, SpeakerUpdate]):
    def get_by_profile_id(self, db: Session, *, profile_id: str) -> Optional[Speaker]:
        """
        Retrieve a speaker by profile_id.
        """
        return db.query(Speaker).filter(Speaker.profile_id == profile_id).first()
    
    def get_or_create(self, db: Session, profile_id: str) -> Speaker:
        """
        Get a speaker by profile_id, or create a new one if it doesn't exist.
        """
        speaker = db.query(Speaker).filter(Speaker.profile_id == profile_id).first()
        if not speaker:
            speaker = Speaker(profile_id=profile_id)
            db.add(speaker)
            db.commit()
            db.refresh(speaker)
        return speaker

    def get_all_profiles(self, db: Session) -> List[Speaker]:
        """
        Retrieve all speaker profiles.
        """
        return db.query(Speaker).all()

    def delete_profile(self, db: Session, speaker_id: str) -> bool:
        """
        Delete a speaker by ID.
        """
        speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
        if speaker:
            db.delete(speaker)
            db.commit()
            return True
        return False

    def reset_all_profiles(self, db: Session) -> None:
        """
        Delete all speaker profiles.
        """
        db.query(Speaker).delete()
        db.commit()

crud_speaker = CRUDSpeaker(Speaker)