from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class OpticalState(TypedDict):
    spec_data: dict
    validation_log: Annotated[List[str], add_messages]
    is_compliant: bool

def validate_optical_spec(state: OpticalState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if 'clear_aperture_mm' not in specs:
        logs.append('Missing clear aperture specification.')
        compliant = False
    if 'optical_coating_range_nm' not in specs:
        logs.append('Missing coating wavelength range.')
        compliant = False
    return {'validation_log': logs, 'is_compliant': compliant}

def finalize_order(state: OpticalState):
    return {'validation_log': ['Order validated and ready for procurement workflow.']}

graph = StateGraph(OpticalState)
graph.add_node('validate', validate_optical_spec)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()