from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FETState(TypedDict):
    specs: dict
    validation_results: List[str]
    is_compliant: bool

def validate_specs(state: FETState):
    check = []
    for field in ['Vth', 'RDS(on)', 'VDS']:
        if field in state['specs']: check.append(f'Validated {field}')
    return {'validation_results': check, 'is_compliant': True}

def export_control_check(state: FETState):
    # Simulated dual-use check logic
    return {'is_compliant': state.get('is_compliant', True)}

graph = StateGraph(FETState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()