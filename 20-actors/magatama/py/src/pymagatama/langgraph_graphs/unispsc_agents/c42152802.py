from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalToolState(TypedDict):
    tool_id: str
    spec_compliance: bool
    sterilization_req: str

def validate_tool_specs(state: DentalToolState):
    state['spec_compliance'] = bool(state.get('tool_id') and state.get('sterilization_req'))
    return 'check_complete'

def finalize_procurement(state: DentalToolState):
    return {'status': 'READY_FOR_ORDER'}

graph = StateGraph(DentalToolState)
graph.add_node('validate', validate_tool_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
