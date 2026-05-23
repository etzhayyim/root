from typing import TypedDict
from langgraph.graph import StateGraph, END

class WorkflowState(TypedDict):
    part_id: str
    spec_data: dict
    validated: bool

def validate_specs(state: WorkflowState):
    # Simulated validation logic for power transmission components
    specs = state.get('spec_data', {})
    state['validated'] = all(k in specs for k in ['load_rating', 'material'])
    return state

def process_procurement(state: WorkflowState):
    print(f'Processing part validation for {state['part_id']}')
    return {'validated': True}

graph = StateGraph(WorkflowState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
