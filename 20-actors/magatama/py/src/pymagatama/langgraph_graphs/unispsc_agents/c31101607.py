from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_id: str
    inspection_passed: bool
    compliance_checked: bool

def validate_specs(state: CastingState):
    print(f'Validating metallurgical specs for {state['part_id']}')
    return {'compliance_checked': True}

def perform_inspection(state: CastingState):
    print(f'Executing X-ray structural integrity sweep of {state['part_id']}')
    return {'inspection_passed': True}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('inspect', perform_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
