from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ActuatorState(TypedDict):
    spec_data: dict
    validation_log: Annotated[list, add_messages]
    status: str

def validate_specs(state: ActuatorState):
    specs = state['spec_data']
    if specs.get('torque_rating_nm', 0) > 0:
        return {'validation_log': ['Torque specs valid'], 'status': 'VALIDATED'}
    return {'validation_log': ['Invalid torque'], 'status': 'FAILED'}

def route_by_status(state: ActuatorState):
    return 'end' if state['status'] == 'VALIDATED' else END

graph = StateGraph(ActuatorState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_conditional_edges('validator', route_by_status, {'end': END})
graph.add_edge('validator', END)
app = graph.compile()
