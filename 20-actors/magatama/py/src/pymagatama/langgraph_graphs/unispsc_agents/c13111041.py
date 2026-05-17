from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    commodity_code: str
    purity_level: float
    safety_clearance: bool
    validation_logs: List[str]

def validate_purity(state: ChemicalProcurementState) -> ChemicalProcurementState:
    if state['purity_level'] < 0.99:
        state['validation_logs'].append('Purity check failed: Below 99%')
        state['safety_clearance'] = False
    else:
        state['validation_logs'].append('Purity check passed')
    return state

def check_safety_regulations(state: ChemicalProcurementState) -> ChemicalProcurementState:
    if not state['safety_clearance']:
        state['validation_logs'].append('Safety review required for dangerous goods')
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_safety', check_safety_regulations)
graph.add_edge('validate_purity', 'check_safety')
graph.add_edge('check_safety', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()