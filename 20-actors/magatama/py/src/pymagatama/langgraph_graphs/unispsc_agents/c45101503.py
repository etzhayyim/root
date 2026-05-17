from typing import TypedDict
from langgraph.graph import StateGraph, END

class LetterpressState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: LetterpressState):
    required = ['Maximum printing area', 'Power requirements']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core specs'}

def route_by_validation(state: LetterpressState):
    return 'process' if state['validated'] else END

def process_equipment(state: LetterpressState):
    print('Processing letterpress certification...')
    return {'validated': True}

graph = StateGraph(LetterpressState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_equipment)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()