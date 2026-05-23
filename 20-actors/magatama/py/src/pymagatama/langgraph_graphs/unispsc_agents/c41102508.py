from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AspiratorState(TypedDict):
    specs: dict
    is_validated: bool
    validation_log: List[str]

def validate_specs(state: AspiratorState):
    required = ['material', 'suction_type', 'vial_capacity']
    missing = [f for f in required if f not in state['specs']]
    if not missing:
        return {'is_validated': True, 'validation_log': ['Specs pass standard criteria']}
    return {'is_validated': False, 'validation_log': [f'Missing fields: {missing}']}

graph = StateGraph(AspiratorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
