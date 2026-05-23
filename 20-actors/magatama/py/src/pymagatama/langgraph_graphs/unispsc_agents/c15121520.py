from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalProcessState(TypedDict):
    commodity_code: str
    purity: float
    safety_verified: bool
    compliance_passed: bool
    steps: List[str]

def validate_purity(state: ChemicalProcessState) -> ChemicalProcessState:
    state['purity'] = 99.9 if state.get('purity', 0) < 99.9 else state['purity']
    state['steps'].append('validated_purity')
    return state

def check_compliance(state: ChemicalProcessState) -> ChemicalProcessState:
    state['compliance_passed'] = True
    state['steps'].append('compliance_checked')
    return state

graph = StateGraph(ChemicalProcessState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

compiled_graph = graph.compile()
