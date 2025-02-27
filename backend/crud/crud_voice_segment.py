from crud.crud_base import CRUDBase
from models.voice_segment import VoiceSegment
from schemas.voice_segment import VoiceSegmentCreate, VoiceSegmentUpdate

class CRUDVoiceSegment(CRUDBase[VoiceSegment, VoiceSegmentCreate, VoiceSegmentUpdate]):
    pass

crud_voice_segment = CRUDVoiceSegment(VoiceSegment)