from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralIngestState(TypedDict):
    raw_data: dict
    purity_validated: bool
    compliance_tags: List[str]
    log: List[str]

def validate_chemical_purity(state: MineralIngestState) -> MineralIngestState:
    purity = state['raw_data'].get('purity', 0)
    state['purity_validated'] = purity >= 99.5
    state['log'].append(f'Purity check: {purity}%')
    return state

def check_sanctions(state: MineralIngestState) -> MineralIngestState:
    origin = state['raw_data'].get('origin', 'unknown')
    if origin in ['restricted_zone_a', 'restricted_zone_b']:
        state['compliance_tags'].append('sanctions-sensitive')
    return state

def compile_graph():
    builder = StateGraph(MineralIngestState)
    builder.add_node('validate', validate_chemical_purity)
    builder.add_node('compliance', check_sanctions)
    builder.set_entry_point('validate')
    builder.add_edge('validate', 'compliance')
    builder.add_edge('compliance', END)
    return builder.compile()

graph = compile_graph()
