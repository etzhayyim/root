from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalIngestState(TypedDict):
    material_id: str
    purity_level: float
    hazmat_clearance: bool
    inspection_log: Annotated[Sequence[str], operator.add]

def validate_purity(state: ChemicalIngestState) -> ChemicalIngestState:
    if state['purity_level'] < 0.999:
        state['inspection_log'] = ['Purity below threshold']
    return state

def check_hazmat(state: ChemicalIngestState) -> ChemicalIngestState:
    if not state['hazmat_clearance']:
        state['inspection_log'] = state['inspection_log'] + ['Hazmat clearance required']
    return state

graph = StateGraph(ChemicalIngestState)
graph.add_node('validate', validate_purity)
graph.add_node('hazmat', check_hazmat)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazmat')
graph.add_edge('hazmat', END)
graph = graph.compile()