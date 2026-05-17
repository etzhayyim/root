from typing import TypedDict
from langgraph.graph import StateGraph, END

class StudProcurementState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: StudProcurementState):
    log = []
    required = ['material_grade', 'thread_pitch_standard']
    valid = all(key in state['spec_data'] for key in required)
    log.append('Specs validated: ' + str(valid))
    return {'validation_log': log, 'is_compliant': valid}

def approval_node(state: StudProcurementState):
    return {'validation_log': state['validation_log'] + ['Approval process completed']}

graph = StateGraph(StudProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()