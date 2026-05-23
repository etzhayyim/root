from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    specs: dict
    validation_passed: bool
    export_flag: bool

def validate_specs(state: BearingState):
    s = state['specs']
    passed = 'load_rating' in s and 'tolerance_class' in s
    high_precision = s.get('tolerance_class') in ['P4', 'P2']
    return {'validation_passed': passed, 'export_flag': high_precision}

def check_compliance(state: BearingState):
    if state['export_flag']:
        print('Checking dual-use export compliance for precision bearings...')
    return {'validation_passed': True}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
