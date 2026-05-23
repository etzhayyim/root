from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AdhesiveState(TypedDict):
    spec_requirements: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_viscosity(state: AdhesiveState) -> AdhesiveState:
    val = state['spec_requirements'].get('viscosity_cps', 0)
    status = 'PASS' if 500 <= val <= 2000 else 'FAIL'
    return {'validation_results': [f'Viscosity: {status}']}

def validate_temp_range(state: AdhesiveState) -> AdhesiveState:
    r = state['spec_requirements'].get('operating_temp_range_celsius', [0, 0])
    status = 'PASS' if r[0] < -40 and r[1] > 150 else 'FAIL'
    return {'validation_results': [f'TempRange: {status}']}

def check_final_approval(state: AdhesiveState) -> str:
    if all('PASS' in res for res in state['validation_results']):
        return 'approved'
    return 'rejected'

graph = StateGraph(AdhesiveState)
graph.add_node('val_viscosity', validate_viscosity)
graph.add_node('val_temp', validate_temp_range)
graph.add_edge('val_viscosity', 'val_temp')
graph.add_conditional_edges('val_temp', check_final_approval, {'approved': END, 'rejected': END})
graph.set_entry_point('val_viscosity')
graph = graph.compile()
