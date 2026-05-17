from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChamberState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: ChamberState):
    s = state['specs']
    passed = all([s.get('temp_range'), s.get('humidity_range'), s.get('dimensions')])
    return {'validation_passed': passed, 'compliance_report': 'Validated' if passed else 'Failed'}

def process_procurement(state: ChamberState):
    print('Initiating environmental chamber procurement workflow...')
    return {'compliance_report': 'Workflow Completed'}

graph = StateGraph(ChamberState)
graph.add_node('validate', validate_specs)
graph.add_node('procure', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph = graph.compile()