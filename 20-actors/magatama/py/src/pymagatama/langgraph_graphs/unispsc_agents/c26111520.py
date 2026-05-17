from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrunnionState(TypedDict):
    spec_data: dict
    validation_results: dict
    is_compliant: bool

def validate_specs(state: TrunnionState) -> TrunnionState:
    # Logic to verify material and tolerance specs against engineering standards
    state['is_compliant'] = all(k in state['spec_data'] for k in ['material', 'tolerance'])
    print('Validating trunnion specifications...')
    return state

def check_compliance(state: TrunnionState) -> str:
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph_builder = StateGraph(TrunnionState)
graph_builder.add_node('validate', validate_specs)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', END)
graph = graph_builder.compile()