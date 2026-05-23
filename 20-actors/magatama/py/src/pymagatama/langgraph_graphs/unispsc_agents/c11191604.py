from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class ProcessingState(TypedDict):
    material_id: str
    purity_level: float
    compliance_checks: Annotated[list[str], operator.add]
    is_approved: bool

def validate_purity(state: ProcessingState) -> ProcessingState:
    if state['purity_level'] >= 99.9:
        state['compliance_checks'].append('purity_certified')
    return state

def check_regulatory(state: ProcessingState) -> ProcessingState:
    state['compliance_checks'].append('regulatory_cleared')
    state['is_approved'] = True
    return state

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_purity)
graph.add_node('regulatory', check_regulatory)
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
