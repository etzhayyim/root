from langgraph.graph import StateGraph, END
from typing import TypedDict
class CRTState(TypedDict):
    model: str
    compliance_cleared: bool
    disposal_plan: str
def validate_specs(state: CRTState):
    state['compliance_cleared'] = True if 'CRT' in state['model'] else False
    return state
def check_disposal(state: CRTState):
    state['disposal_plan'] = 'Licensed E-Waste Facility' if state['compliance_cleared'] else 'None'
    return state
graph = StateGraph(CRTState)
graph.add_node('validate', validate_specs)
graph.add_node('disposal', check_disposal)
graph.set_entry_point('validate')
graph.add_edge('validate', 'disposal')
graph.add_edge('disposal', END)
app = graph.compile()
