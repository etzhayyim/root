from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    specs: dict
    validation_results: Annotated[Sequence[str], operator.add]
    status: str

def validate_specs(state: ActuatorState):
    specs = state['specs']
    if 'torque_rating_nm' in specs and specs['torque_rating_nm'] > 0:
        return {'validation_results': ['Torque specs valid'], 'status': 'validated'}
    return {'validation_results': ['Invalid torque'], 'status': 'failed'}

def check_compliance(state: ActuatorState):
    return {'validation_results': ['Compliance check passed'], 'status': 'compliant'}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
