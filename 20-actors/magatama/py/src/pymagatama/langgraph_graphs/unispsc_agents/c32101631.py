from typing import TypedDict
from langgraph.graph import StateGraph, END

class ComparatorState(TypedDict):
    part_number: str
    specifications: dict
    compliance_cleared: bool

def validate_specs(state: ComparatorState):
    # Simulate CAD/Spec validation for voltage comparator parameters
    required = ['offset_voltage', 'propagation_delay']
    state['compliance_cleared'] = all(k in state['specifications'] for k in required)
    return state

def export_review(state: ComparatorState):
    # Simulate dual-use export control screening logic
    print(f"Screening part {state['part_number']} for export control.")
    return state

workflow = StateGraph(ComparatorState)
workflow.add_node('validate', validate_specs)
workflow.add_node('export_check', export_review)
workflow.add_edge('validate', 'export_check')
workflow.add_edge('export_check', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
