from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CarbonState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_carbon_specs(state: CarbonState):
    spec = state['spec_data']
    logs = []
    if spec.get('tensile_strength_mpa', 0) < 3500:
        logs.append('Insufficient tensile strength for aerospace grade.')
    return {'validation_logs': logs, 'is_approved': len(logs) == 0}

def route_by_validation(state: CarbonState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(CarbonState)
graph.add_node('validate', validate_carbon_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'approved': END, 'rejected': END})
graph = graph.compile()
