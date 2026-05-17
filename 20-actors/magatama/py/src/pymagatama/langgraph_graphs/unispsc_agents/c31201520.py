from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TapeSpecState(TypedDict):
    material: str
    adhesion: float
    compliance_codes: List[str]
    approved: bool

def validate_tape_specs(state: TapeSpecState):
    # Basic validation for industrial floor marking specs
    if state['adhesion'] > 5.0 and 'OSHA' in state['compliance_codes']:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(TapeSpecState)
graph.add_node('validate', validate_tape_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()