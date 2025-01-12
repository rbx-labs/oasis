from app.crud.crud_base import CRUDBase
from app.models.transcription import Transcription
from app.schemas.transcription import TranscriptionCreate

class CRUDTranscription(CRUDBase[Transcription, TranscriptionCreate, TranscriptionCreate]):
    pass

crud_transcription = CRUDTranscription(Transcription) 