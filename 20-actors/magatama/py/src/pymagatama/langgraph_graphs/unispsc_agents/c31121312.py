from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    part_specs: dict
    validation_status: bool

def validate_casting_specs(state: CastState):
    specs = state['part_specs']
    # Check for critical dimensions and material compliance
    is_valid = 'tolerance' in specs and 'alloy_type' in specs
    return {'validation_status': is_valid}

def update_manufacturing_status(state: CastState):
    if state['validation_status']:
        print('Processing machining workflow...')
    return state

graph = StateGraph(CastState)
graph.add_node('validate', validate_casting_specs)
graph.add_node('manufacture', update_manufacturing_status)
graph.add_edge('validate', 'manufacture')
graph.add_edge('manufacture', END)
graph.set_entry_point('validate')
app = graph.compile()
