from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_id: str
    specs: dict
    validation_passed: bool

def validate_casting_specs(state: CastingState):
    required_keys = ['alloy', 'dimensions', 'hardness']
    all_present = all(k in state['specs'] for k in required_keys)
    return {'validation_passed': all_present}

def process_casting_order(state: CastingState):
    print(f'Processing brass casting casting: {state['part_id']}')
    return {'validation_passed': True}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_casting_specs)
graph.add_node('process', process_casting_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
