from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DiffuserState(TypedDict):
    part_id: str
    inspection_results: dict
    approved: bool

def validate_specs(state: DiffuserState):
    # Simulate aerospace QC validation logic
    specs = state.get('inspection_results', {})
    state['approved'] = specs.get('ndt_clear', False) and specs.get('material_cert', True)
    return state

def export_check(state: DiffuserState):
    # Dual-use compliance check logic
    print(f'Checking export threshold for {state['part_id']}')
    return 'export_passed'

graph = StateGraph(DiffuserState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)

# Compile the graph
app = graph.compile()
