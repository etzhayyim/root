from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProjectorState(TypedDict):
    model_number: str
    lumen_check: bool
    compliance_verified: bool

def validate_specs(state: ProjectorState):
    print(f'Validating specs for {state['model_number']}')
    return {'lumen_check': True, 'compliance_verified': True}

def finalize_procurement(state: ProjectorState):
    print('Procurement validated.')
    return {}

graph = StateGraph(ProjectorState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
app = graph.compile()
