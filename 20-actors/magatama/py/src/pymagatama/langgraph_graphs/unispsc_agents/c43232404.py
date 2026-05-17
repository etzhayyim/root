from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GUIState(TypedDict):
    requirements: List[str]
    compliance_check: bool
    graph_ready: bool

def validate_gui_specs(state: GUIState):
    state['compliance_check'] = 'security' in state['requirements']
    return {'compliance_check': state['compliance_check']}

def finalize_build(state: GUIState):
    state['graph_ready'] = True
    return {'graph_ready': True}

graph = StateGraph(GUIState)
graph.add_node('validate', validate_gui_specs)
graph.add_node('finalize', finalize_build)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
app = graph.compile()