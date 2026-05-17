from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodState(TypedDict):
    origin: str
    quality_report: dict
    approved: bool

def validate_quality(state: FoodState):
    print('Validating microbiological report...')
    state['approved'] = 'microbial_load' in state['quality_report']
    return state

def check_origin(state: FoodState):
    print(f'Verifying origin: {state['origin']}')
    return state

graph = StateGraph(FoodState)
graph.add_node('validate', validate_quality)
graph.add_node('origin_check', check_origin)
graph.set_entry_point('origin_check')
graph.add_edge('origin_check', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()