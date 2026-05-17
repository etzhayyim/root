from typing import TypedDict
from langgraph.graph import StateGraph, END

class BarricadeState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: BarricadeState):
    state['is_compliant'] = all(k in state['specs'] for k in ['material', 'reflectivity'])
    print('Validating barricade specifications...')
    return state

def safety_check(state: BarricadeState):
    print('Performing impact resistance verification...')
    return {'is_compliant': state['is_compliant'] and state['specs'].get('impact_tested', False)}

graph = StateGraph(BarricadeState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()