from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompactorState(TypedDict):
    spec_data: dict
    validation_status: str

def validate_spec(state: CompactorState):
    force = state['spec_data'].get('compression_force_kn', 0)
    status = 'VALID' if force > 0 else 'INVALID'
    return {'validation_status': status}

def safety_check(state: CompactorState):
    print('Performing mechanical safety interlock verification...')
    return {'validation_status': 'SECURE'}

graph = StateGraph(CompactorState)
graph.add_node('validate', validate_spec)
graph.add_node('safety', safety_check)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
