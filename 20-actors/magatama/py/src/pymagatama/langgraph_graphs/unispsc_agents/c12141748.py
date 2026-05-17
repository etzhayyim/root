from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class LubricantState(TypedDict):
    spec_data: dict
    validation_logs: List[str]
    status: str

def validate_chemistry(state: LubricantState) -> LubricantState:
    spec = state.get('spec_data', {})
    if 'flash_point' not in spec:
        state['validation_logs'].append('Missing Flash Point')
        state['status'] = 'REJECTED'
    return state

def check_compliance(state: LubricantState) -> LubricantState:
    if state.get('status') == 'REJECTED':
        return state
    state['validation_logs'].append('Compliance Verified')
    state['status'] = 'APPROVED'
    return state

graph = StateGraph(LubricantState)
graph.add_node('validate', validate_chemistry)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
compile_graph = graph.compile()