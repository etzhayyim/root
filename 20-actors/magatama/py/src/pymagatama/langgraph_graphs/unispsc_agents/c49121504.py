from typing import TypedDict
from langgraph.graph import StateGraph, END

class SleepingBagState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_logs: list

def validate_specs(state: SleepingBagState):
    required = ['comfort_temp', 'fill_type', 'weight']
    passed = all(k in state['spec_data'] for k in required)
    return {**state, 'validation_passed': passed}

def process_procurement(state: SleepingBagState):
    print(f'Processing Sleeping Bag: {state['spec_data']}')
    return state

graph = StateGraph(SleepingBagState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()