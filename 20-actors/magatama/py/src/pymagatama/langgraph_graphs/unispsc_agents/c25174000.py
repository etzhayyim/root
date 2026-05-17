from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CoolingSystemState(TypedDict):
    part_number: str
    specifications: dict
    validation_status: bool
    error_logs: List[str]

def validate_thermal_specs(state: CoolingSystemState):
    specs = state['specifications']
    is_valid = specs.get('temp_rating', 0) > 120 and specs.get('pressure_psi', 0) > 15
    return {'validation_status': is_valid, 'error_logs': [] if is_valid else ['Thermal requirement not met']}

def route_to_qa(state: CoolingSystemState):
    return 'qa_process' if state['validation_status'] else END

graph = StateGraph(CoolingSystemState)
graph.add_node('validate', validate_thermal_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_to_qa)
graph.add_edge('qa_process', END)
graph = graph.compile()