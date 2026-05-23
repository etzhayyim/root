from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    cas_number: str
    purity_level: float
    safety_clearance: bool
    validation_log: List[str]

def validate_cas(state: ChemicalProcurementState) -> ChemicalProcurementState:
    state['validation_log'].append(f'Validating CAS: {state["cas_number"]}')
    return state

def check_purity(state: ChemicalProcurementState) -> ChemicalProcurementState:
    if state['purity_level'] < 99.0:
        state['validation_log'].append('Low purity - rejecting')
        state['safety_clearance'] = False
    else:
        state['safety_clearance'] = True
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate_cas', validate_cas)
graph.add_node('check_purity', check_purity)
graph.set_entry_point('validate_cas')
graph.add_edge('validate_cas', 'check_purity')
graph.add_edge('check_purity', END)
compiled_graph = graph.compile()
