from typing import TypedDict
from langgraph.graph import StateGraph, END

class TTSProcessState(TypedDict):
    text: str
    language: str
    is_compliant: bool

def validate_text(state: TTSProcessState):
    state['is_compliant'] = len(state['text']) < 5000
    return state

def synthesize_audio(state: TTSProcessState):
    print(f'Synthesizing text for {state.get('language')}')
    return {'text': 'Audio Generated'}

graph = StateGraph(TTSProcessState)
graph.add_node('validate', validate_text)
graph.add_node('synthesize', synthesize_audio)
graph.set_entry_point('validate')
graph.add_edge('validate', 'synthesize')
graph.add_edge('synthesize', END)
graph = graph.compile()
