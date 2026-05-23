from typing import TypedDict
from langgraph.graph import StateGraph, END

class DispenserState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: DispenserState):
    log = []
    compliant = True
    if 'material_cert' not in state['spec_data']:
        log.append('Missing food safety certification.')
        compliant = False
    return {'validation_log': log, 'is_compliant': compliant}

def finalize_order(state: DispenserState):
    print('Procurement logic finalized')
    return {}

graph = StateGraph(DispenserState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.compile()
