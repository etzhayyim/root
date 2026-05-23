from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PipeProcessState(TypedDict):
    material_grade: str
    pressure_rating: float
    specs_verified: bool
    compliance_log: List[str]

def validate_material(state: PipeProcessState) -> PipeProcessState:
    if state['material_grade'] in ['ASTM-A53', 'ASTM-A106']:
        state['specs_verified'] = True
        state['compliance_log'].append('Material grade validated')
    else:
        state['specs_verified'] = False
        state['compliance_log'].append('Material grade unknown')
    return state

def check_pressure(state: PipeProcessState) -> PipeProcessState:
    if state['pressure_rating'] >= 10.0:
        state['compliance_log'].append('Pressure rating sufficient for high-pressure application')
    return state

graph = StateGraph(PipeProcessState)
graph.add_node('validate', validate_material)
graph.add_node('pressure_check', check_pressure)
graph.set_entry_point('validate')
graph.add_edge('validate', 'pressure_check')
graph.add_edge('pressure_check', END)
app = graph.compile()
