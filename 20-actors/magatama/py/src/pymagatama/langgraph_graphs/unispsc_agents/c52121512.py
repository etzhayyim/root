from langgraph.graph import StateGraph, END
from typing import TypedDict
class PillowSpecState(TypedDict):
    specs: dict
    validated: bool
def validate_specs(state: PillowSpecState):
    required = ['material', 'thread_count', 'dimensions']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid}
def check_compliance(state: PillowSpecState):
    print(f'Compliance check for thread count: {state['specs'].get('thread_count')} against standard.')
    return 'validated' if state['validated'] else 'error'
graph = StateGraph(PillowSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()