from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorState(TypedDict):
    specs: dict
    validation_errors: list
    is_compliant: bool

def validate_motor_specs(state: MotorState):
    errors = []
    required = ['rated_power_kw', 'voltage_rating_v']
    for field in required:
        if field not in state['specs']:
            errors.append(f'Missing {field}')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def export_control_check(state: MotorState):
    # logic for dual-use export control based on kw rating
    if state['specs'].get('rated_power_kw', 0) > 500:
         state['is_compliant'] = False
    return state

graph = StateGraph(MotorState)
graph.add_node('validate', validate_motor_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()