from app.crud.crud_base import CRUDBase
from app.models.voice_segment import VoiceSegment
from app.schemas.voice_segment import VoiceSegmentCreate, VoiceSegmentUpdate

class CRUDVoiceSegment(CRUDBase[VoiceSegment, VoiceSegmentCreate, VoiceSegmentUpdate]):
    pass

crud_voice_segment = CRUDVoiceSegment(VoiceSegment)