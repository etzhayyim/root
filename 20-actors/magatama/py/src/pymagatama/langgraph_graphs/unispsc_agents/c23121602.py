from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotProcurementState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: RobotProcurementState):
    required = ['payload_capacity_kg', 'degrees_of_freedom']
    errors = [field for field in required if field not in state['spec_sheet']]
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_export(state: RobotProcurementState):
    print('Checking dual-use export regulations...')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(RobotProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
