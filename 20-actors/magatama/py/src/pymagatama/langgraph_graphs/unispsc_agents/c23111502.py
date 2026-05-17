from typing import TypedDict
from langgraph.graph import StateGraph, END

class TestState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: TestState):
    required = ['Load Capacity', 'Accuracy']
    errors = [k for k in required if k not in state['spec_data']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def finalize_procurement(state: TestState):
    print('Procurement logic finalized')
    return state

graph = StateGraph(TestState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()