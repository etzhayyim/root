from langgraph.graph import StateGraph, END
from typing import TypedDict
class AudioState(TypedDict):
    audio_file_path: str
    validation_status: bool
    upload_complete: bool
def validate_audio_format(state: AudioState):
    # Simulate validation logic for hold audio files
    return {'validation_status': state['audio_file_path'].endswith('.mp3')}
def process_upload(state: AudioState):
    return {'upload_complete': True}
graph = StateGraph(AudioState)
graph.add_node('validate', validate_audio_format)
graph.add_node('upload', process_upload)
graph.set_entry_point('validate')
graph.add_edge('validate', 'upload')
graph.add_edge('upload', END)
graph = graph.compile()
