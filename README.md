# DepAnalysis

DepAnalysis is a tool for generating graphs of call dependencies within classes.

One of the dependencies in our module is pydot, which does not fully support python 3.x yet. Before running DepAnalysis, a modification should be done to the pydot module. Please change occurences of file() in the module to open().
