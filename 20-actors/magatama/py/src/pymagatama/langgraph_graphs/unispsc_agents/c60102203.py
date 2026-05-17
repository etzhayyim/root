from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PhonicsState(TypedDict):
    kit_components: List[str]
    validation_passed: bool

def validate_components(state: PhonicsState):
    required = ['phonics_cards', 'audio_guides', 'workbooks']
    passed = all(item in state['kit_components'] for item in required)
    return {'validation_passed': passed}

def assemble_kit(state: PhonicsState):
    if state['validation_passed']:
        print('Kit assembly verified.')
    return state

graph = StateGraph(PhonicsState)
graph.add_node('validate', validate_components)
graph.add_node('assemble', assemble_kit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
app = graph.compile()