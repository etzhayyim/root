from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotComponentState(TypedDict):
    component_id: str
    spec_sheet: dict
    validation_logs: List[str]
    is_compliant: bool

def validate_component(state: RobotComponentState):
    logs = state.get('validation_logs', [])
    logs.append(f'Validating component {state['component_id']} for industrial standards.')
    return {'validation_logs': logs, 'is_compliant': True}

def generate_procurement_report(state: RobotComponentState):
    return {'validation_logs': state['validation_logs'] + ['Generating final procurement report.']}

graph = StateGraph(RobotComponentState)
graph.add_node('validate', validate_component)
graph.add_node('report', generate_procurement_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()