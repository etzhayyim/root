from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from operator import add

class ChemicalIngestState(TypedDict):
    material_id: str
    purity_level: float
    safety_clearance: bool
    log_entries: Annotated[Sequence[str], add]

def validate_purity(state: ChemicalIngestState) -> ChemicalIngestState:
    if state['purity_level'] < 0.99:
        state['log_entries'] = ['Purity too low for spec.']
    return state

def check_compliance(state: ChemicalIngestState) -> ChemicalIngestState:
    if not state['safety_clearance']:
        state['log_entries'] = state.get('log_entries', []) + ['Safety clearance missing.']
    return state

builder = StateGraph(ChemicalIngestState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()