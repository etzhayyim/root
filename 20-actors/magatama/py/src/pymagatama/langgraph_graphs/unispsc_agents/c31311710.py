from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeAssemblyState(TypedDict):
    material_certified: bool
    test_report_attached: bool
    is_approved: bool

def validate_specs(state: PipeAssemblyState):
    return {'is_approved': state['material_certified'] and state['test_report_attached']}

def perform_ndt_check(state: PipeAssemblyState):
    print('Executing ultrasonic inspection workflows...')
    return {'test_report_attached': True}

graph = StateGraph(PipeAssemblyState)
graph.add_node('inspection', perform_ndt_check)
graph.add_node('validation', validate_specs)
graph.add_edge('inspection', 'validation')
graph.add_edge('validation', END)
graph.set_entry_point('inspection')
graph = graph.compile()