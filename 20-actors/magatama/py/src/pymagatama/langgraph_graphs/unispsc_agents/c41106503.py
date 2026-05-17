from typing import TypedDict
from langgraph.graph import StateGraph, END

class RegulatorState(TypedDict):
    chemical_name: str
    purity: float
    requires_hazmat_handling: bool

def validate_purity(state: RegulatorState):
    if state['purity'] < 0.95:
        return {'status': 'rejected'}
    return {'status': 'verified'}

def check_compliance(state: RegulatorState):
    return {'compliance': 'approved'} if state['requires_hazmat_handling'] else {'compliance': 'standard'}

graph = StateGraph(RegulatorState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
app = graph.compile()