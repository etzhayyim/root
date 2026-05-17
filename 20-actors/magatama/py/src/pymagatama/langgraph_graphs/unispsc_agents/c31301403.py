from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    part_id: str
    specs: dict
    approved: bool
    error_log: List[str]

def validate_specs(state: ForgingState):
    required = ['grade', 'tolerance']
    missing = [f for f in required if f not in state['specs']]
    return {'approved': len(missing) == 0, 'error_log': missing}

def check_compliance(state: ForgingState):
    if state['approved']:
        print(f'Part {state['part_id']} is compliant.')
    return 'end'

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()