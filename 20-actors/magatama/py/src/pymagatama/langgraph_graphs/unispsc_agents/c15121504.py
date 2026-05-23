from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    material_id: str
    spec_requirements: dict
    validation_logs: List[str]
    is_approved: bool

def validate_resin_specs(state: ResinState) -> ResinState:
    mfi = state['spec_requirements'].get('mfi', 0)
    if mfi < 10 or mfi > 50:
        state['validation_logs'].append('MFI outside acceptable range for manufacturing.')
        state['is_approved'] = False
    else:
        state['validation_logs'].append('MFI validation passed.')
    return state

def check_compliance(state: ResinState) -> ResinState:
    if 'rohs_certified' in state['spec_requirements']:
        state['validation_logs'].append('Compliance checked.')
    else:
        state['is_approved'] = False
        state['validation_logs'].append('Missing compliance documentation.')
    return state

graph = StateGraph(ResinState)
graph.add_node('validate', validate_resin_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
compiled_graph = graph.compile()
