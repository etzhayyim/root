from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    material_name: str
    purity_level: float
    gmp_certified: bool
    validation_notes: List[str]

def validate_quality(state: PharmState):
    notes = state.get('validation_notes', [])
    if state['purity_level'] < 99.0:
        notes.append('Purity below pharmaceutical threshold')
    if not state['gmp_certified']:
        notes.append('Missing GMP certification')
    return {'validation_notes': notes}

graph = StateGraph(PharmState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()