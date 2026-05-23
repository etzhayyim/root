from typing import TypedDict
from langgraph.graph import StateGraph, END

class CuttingMachineState(TypedDict):
    specs: dict
    validation_errors: list
    is_compliant: bool

def validate_specs(state: CuttingMachineState):
    errors = []
    if not state['specs'].get('Safety_Interlock_Standard'):
        errors.append('Missing safety interlock compliance')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_export_controls(state: CuttingMachineState):
    print('Checking dual-use export control registry...')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(CuttingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_controls)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
