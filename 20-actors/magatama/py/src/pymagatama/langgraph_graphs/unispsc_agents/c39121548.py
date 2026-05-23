from typing import TypedDict
from langgraph.graph import StateGraph, END

class VacuumSwitchState(TypedDict):
    part_number: str
    specifications: dict
    validation_passed: bool

def validate_specs(state: VacuumSwitchState):
    specs = state.get('specifications', {})
    # Logic: Validate pressure range and voltage compatibility
    valid = 'range' in specs and 'voltage' in specs
    return {'validation_passed': valid}

def route_by_validation(state: VacuumSwitchState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(VacuumSwitchState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END})
graph.compile()
