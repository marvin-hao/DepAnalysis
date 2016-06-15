# DepAnalysis

DepAnalysis is a tool for generating graphs of call dependencies within classes.

One of the dependencies of our module is pydot, which does not fully support Python 3.x yet. Before running DepAnalysis, a modification should be done to the pydot module. Please change occurrences of file() in the module to open().
