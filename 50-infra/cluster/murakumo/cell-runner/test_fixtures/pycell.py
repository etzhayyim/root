"""A trivial PYTHON cell fixture for the lite-runner auto-fallback test: a `fire`
that returns a content-addressed result map, exactly the shape a real python cell
returns. Exercises the bb runner shelling a python-only cell (cutover-safety)."""


def fire():
    return {"cid": "bafypyfixture0001"}
