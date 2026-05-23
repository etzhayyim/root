from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: PumpState):
    errors = []
    if 'pressure_rating' not in state['specifications']: errors.append('Pressure rating missing')
    if 'material' not in state['specifications']: errors.append('Material verification required')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: PumpState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(PumpState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': 'process', '__end__': END})
graph.add_edge('process', END)
graph = graph.compile()
