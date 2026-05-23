from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlloyState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_tech_specs(state: AlloyState):
    required = ['material_grade', 'tensile_strength']
    valid = all(k in state['spec_data'] for k in required)
    return {**state, 'validated': valid}

def structural_check(state: AlloyState):
    if state.get('validated'):
        return 'ready'
    return 'incomplete'

graph = StateGraph(AlloyState)
graph.add_node('validate', validate_tech_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
