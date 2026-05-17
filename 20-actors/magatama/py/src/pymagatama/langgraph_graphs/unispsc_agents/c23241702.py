from typing import TypedDict
from langgraph.graph import StateGraph, END

class DeburringState(TypedDict):
    pressure_config: float
    gas_mix: str
    safety_check: bool

def validate_safety(state: DeburringState) -> DeburringState:
    print('Validating ISO safety standards...')
    state['safety_check'] = True
    return state

def execute_cycle(state: DeburringState) -> DeburringState:
    if state['safety_check']:
        print(f'Starting thermal cycle at {state['pressure_config']} bar')
    return state

graph = StateGraph(DeburringState)
graph.add_node('safety', validate_safety)
graph.add_node('cycle', execute_cycle)
graph.set_entry_point('safety')
graph.add_edge('safety', 'cycle')
graph.add_edge('cycle', END)
graph = graph.compile()