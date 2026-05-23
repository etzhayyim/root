from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ServerProcurementState(TypedDict):
    commodity_code: str
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_specs(state: ServerProcurementState) -> ServerProcurementState:
    state['validation_passed'] = 'processor_architecture' in state['specs']
    state['log'].append('Validated hardware specifications.')
    return state

def check_compliance(state: ServerProcurementState) -> ServerProcurementState:
    if state.get('validation_passed'):
        state['log'].append('Compliance and export control check cleared.')
    return state

graph = StateGraph(ServerProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
