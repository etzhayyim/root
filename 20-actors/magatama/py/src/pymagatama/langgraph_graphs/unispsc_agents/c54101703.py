from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireMillState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: WireMillState):
    errors = []
    required = ['wire_diameter_range_mm', 'motor_power_rating_kw']
    for field in required:
        if field not in state['spec_data']:
            errors.append(f'Missing {field}')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def check_export_controls(state: WireMillState):
    # Simulate dual-use check for high-performance wire mills
    return {'is_approved': state['is_approved'] and True}

workflow = StateGraph(WireMillState)
workflow.add_node('validate', validate_specs)
workflow.add_node('export_check', check_export_controls)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'export_check')
workflow.add_edge('export_check', END)
graph = workflow.compile()
