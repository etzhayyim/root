from typing import TypedDict
from langgraph.graph import StateGraph, END

class IcingToolState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: IcingToolState):
    required = ['material_grade', 'iso_compliance']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def check_material(state: IcingToolState):
    if state.get('approved'):
        print('Executing material safety check...')
    return 'end'

graph = StateGraph(IcingToolState)
graph.add_node('validate', validate_specs)
graph.add_node('safety_check', check_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
