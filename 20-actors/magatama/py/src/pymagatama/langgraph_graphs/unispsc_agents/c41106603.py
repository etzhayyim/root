from typing import TypedDict
from langgraph.graph import StateGraph, END

class VectorState(TypedDict):
    sequence_data: str
    bsl_level: int
    validation_passed: bool

def validate_sequence(state: VectorState):
    # Simulate bioinformatic sequence validation logic
    is_valid = len(state['sequence_data']) > 0 and 'promoter' in state['sequence_data']
    return {'validation_passed': is_valid}

def check_compliance(state: VectorState):
    # Simulate regulatory compliance check for BSL levels
    if state['bsl_level'] > 2:
        print('High containment review triggered')
    return {}

graph = StateGraph(VectorState)
graph.add_node('validate', validate_sequence)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
