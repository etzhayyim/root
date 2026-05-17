from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CalligraphyState(TypedDict):
    kit_id: str
    components: List[str]
    quality_check: bool

def validate_components(state: CalligraphyState):
    required = {'brush', 'ink', 'inkstone'}
    state['quality_check'] = all(item in state['components'] for item in required)
    return state

def finalize_order(state: CalligraphyState):
    return {'kit_id': state['kit_id'], 'quality_check': state['quality_check']}

graph = StateGraph(CalligraphyState)
graph.add_node('validate', validate_components)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()