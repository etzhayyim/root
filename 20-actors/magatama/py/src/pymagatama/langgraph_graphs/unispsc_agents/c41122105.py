from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RollerBottleState(TypedDict):
    bottle_spec: dict
    validation_passed: bool
    log: List[str]

def validate_sterility(state: RollerBottleState):
    sal = state['bottle_spec'].get('sal', 0)
    passed = sal >= 6
    return {'validation_passed': passed, 'log': [f'Sterility check: {passed}']}

def check_dimensions(state: RollerBottleState):
    dim = state['bottle_spec'].get('dimensions', {})
    passed = all(k in dim for k in ['diameter', 'length'])
    return {'validation_passed': passed, 'log': ['Dimension check completed']}

graph = StateGraph(RollerBottleState)
graph.add_node('validate_sterility', validate_sterility)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_sterility')
graph.add_edge('validate_sterility', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()