from typing import TypedDict, List; from langgraph.graph import StateGraph, END; class RivetState(TypedDict): rivet_specs: dict; validation_results: List[str]; graph = StateGraph(RivetState); def validate_rivet(state: RivetState): 
    specs = state.get('rivet_specs', {}); errors = []; 
    if 'tensile_strength' not in specs: errors.append('Missing tensile strength'); 
    return {'validation_results': errors}; graph.add_node('validate', validate_rivet); graph.set_entry_point('validate'); graph.add_edge('validate', END); app = graph.compile()