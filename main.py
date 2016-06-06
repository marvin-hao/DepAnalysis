import time
from ast import FunctionDef, NodeVisitor, Call, Name, ClassDef, parse
from os import path

from pydot import Cluster as GVCluster
from pydot import Dot as GVDot
from pydot import Edge as GVEdge
from pydot import Node as GVNode

BUILT_IN_FUNC = ["abs", "dict", "help", "min", "setattr", "all", "dir", "hex",
                 "next", "slice", "any", "divmod", "id", "object", "sorted",
                 "ascii", "enumerate", "input", "oct", "staticmethod", "bin",
                 "eval", "int", "open", "str", "bool", "exec", "isinstance",
                 "ord", "sum", "bytearray", "filter", "issubclass", "pow",
                 "super", "bytes", "float", "iter", "print", "tuple", "callable",
                 "format", "len", "property", "type", "chr", "frozenset", "list",
                 "range", "vars", "classmethod", "getattr", "locals", "repr",
                 "zip", "compile", "globals", "map", "reversed", "__import__",
                 "complex", "hasattr", "max", "round", " delattr", "hash",
                 "memoryview", "set"]

BUILT_IN_EXCPT = [
    "BaseException", "SystemExit", "KeyboardInterrupt", "GeneratorExit",
    "Exception", "StopIteration", "StopAsyncIteration", "ArithmeticError",
    "FloatingPointError", "OverflowError", "ZeroDivisionError", "AssertionError",
    "AttributeError", "BufferError", "EOFError", "ImportError", "LookupError",
    "IndexError", "KeyError", "MemoryError", "NameError", "UnboundLocalError",
    "OSError", "BlockingIOError", "ChildProcessError", "ConnectionError",
    "BrokenPipeError", "ConnectionAbortedError", "ConnectionRefusedError",
    "ConnectionResetError", "FileExistsError", "FileNotFoundError",
    "InterruptedError", "IsADirectoryError", "NotADirectoryError",
    "PermissionError", "ProcessLookupError", "TimeoutError", "ReferenceError",
    "RuntimeError", "NotImplementedError", "RecursionError", "SyntaxError",
    "IndentationError", "TabError", "SystemError", "TypeError", "ValueError",
    "UnicodeError", "UnicodeDecodeError", "UnicodeEncodeError",
    "UnicodeTranslateError", "Warning", "DeprecationWarning",
    "PendingDeprecationWarning", "RuntimeWarning", "SyntaxWarning",
    "UserWarning", "FutureWarning", "ImportWarning", "UnicodeWarning",
    "BytesWarning", "ResourceWarning"
]

BUILT_IN = BUILT_IN_FUNC + BUILT_IN_EXCPT


class Node(object):
    def __init__(self, ID: str, level: int = 0, parent: str = None, parent_level: int = -1, label: str = None) -> None:
        self._ID = ID.replace(".", "_")
        self._level = level
        if parent is None:
            self._parent = parent
        else:
            self._parent = parent.replace(".", "_")
        self._parent_level = parent_level
        if label is not None:
            self._label = label.replace(".", "_")
        else:
            self._label = ID

    def set_parent(self, name: str) -> None:
        self._parent = name

    def get_parent(self) -> str:
        return self._parent

    def get_id(self) -> str:
        return self._ID

    def get_level(self) -> int:
        return self._level

    def get_parent_level(self) -> int:
        return self._parent_level

    def get_label(self) -> str:
        return self._label


class Edge(object):
    def __init__(self, src: str, dst: str, label: str = None) -> None:
        if label is None:
            self._label = label
        else:
            self._label = label.replace(".", "_")
        self._src = src.replace(".", "_")
        self._dst = dst.replace(".", "_")

    def get_label(self) -> str:
        return self._label

    def get_src(self) -> str:
        return self._src

    def get_dst(self) -> str:
        return self._dst


class Graph(object):
    def __init__(self) -> None:
        self._nodes = []
        self._edges = []

    def add_node(self, node: Node) -> None:
        self._nodes.append(node)

    def add_edge(self, edge: Edge) -> None:
        self._edges.append(edge)

    def draw(self, path: str) -> None:
        raise NotImplementedError


class DependencyGraph(Graph):
    def __init__(self, label=None):
        super().__init__()
        self._lable = label

    def draw(self, path: str, format: str = "raw") -> None:

        node_aggr = {}
        for node in self._nodes:
            level = node.get_level()
            label = node.get_label()
            identifier = node.get_id()
            if node_aggr.get(level) is None:
                node_aggr[level] = {}
            if level != 0:
                gv_cluster = GVCluster(identifier)
                gv_cluster.set("label", label)
                node_aggr[level][identifier] = gv_cluster
            else:
                gv_node = GVNode(identifier)
                gv_node.set("label", label)
                node_aggr[level][identifier] = gv_node

        gv_dot = GVDot()
        gv_dot.set("ranksep", "1.0 equally")

        if self._lable is not None:
            gv_dot.set("label", self._lable)

        for node in self._nodes:
            level = node.get_level()
            parent = node.get_parent()
            parent_level = node.get_parent_level()
            identifier = node.get_id()
            if level != 0:
                if parent is not None:
                    node_aggr[parent_level][parent].add_subgraph(node_aggr[level][identifier])
                else:
                    gv_dot.add_subgraph(node_aggr[level][identifier])
            else:
                if parent is not None:
                    node_aggr[parent_level][parent].add_node(node_aggr[level][identifier])
                else:
                    gv_dot.add_node(node_aggr[level][identifier])

        for edge in self._edges:
            label = edge.get_label()
            gv_edge = GVEdge(edge.get_src(), edge.get_dst())
            if label is not None:
                gv_edge.set("label", edge.get_label())
            gv_dot.add_edge(gv_edge)

        gv_dot.write(path, format=format)


class CodeElement(object):
    def __init__(self, name: str, parent: str = None):
        self._name = name
        self._parent = parent

    def get_name(self) -> str:
        return self._name

    def get_full_name(self) -> str:
        return self._parent + "." + self._name if self._parent is not None else self._name

    def __str__(self):
        return self.get_full_name()

    def __hash__(self):
        return hash(self.get_full_name())

    def __eq__(self, other):
        return self.get_full_name() == other.get_full_name()


class FunctionCallVisitor(NodeVisitor):
    def __init__(self):
        self._name = set()

    def visit_Name(self, node) -> None:
        if node.id not in BUILT_IN_EXCPT:
            self._name.add(node.id)

    def visit_Attribute(self, node) -> None:
        attr = node.value
        if isinstance(attr, Name) and attr.id == "self":
            self._name.add(node.attr)

    def get_name(self) -> list:
        return self._name


class Function(NodeVisitor, CodeElement):
    def __init__(self, name: str, parent: str = None):
        super().__init__(name=name, parent=parent)
        self._func_call = set()

    def visit_Call(self, node: Call):
        fc_visitor = FunctionCallVisitor()
        fc_visitor.visit(node.func)
        for name in fc_visitor.get_name():
            self._func_call.add(CodeElement(name, parent=self._parent))

    def get_func_call(self) -> set:
        return self._func_call

    def get_func_call_name(self):
        return [call.get_full_name() for call in self._func_call]


class Class(NodeVisitor, CodeElement):
    def __init__(self, name: str, parent: str = None):
        super().__init__(name=name, parent=parent)
        self._func_def = set()

    def visit_FunctionDef(self, node: FunctionDef):
        # if search("__.*__", node.name) is None:
        func = Function(node.name, self.get_full_name())
        func.visit(node)
        self._func_def.add(func)

    def get_func_def(self) -> set:
        return self._func_def


class Module(NodeVisitor, CodeElement):
    def __init__(self, name: str, parent: str = None):
        super().__init__(name=name, parent=parent)
        self._class_def = set()

    def visit_ClassDef(self, node: ClassDef):
        cls = Class(node.name, self.get_full_name())
        cls.visit(node)
        self._class_def.add(cls)

    def get_cls_def(self) -> set:
        return self._class_def


class DepVisual(object):
    def __init__(self, mod_path: str):
        self._mod_path = mod_path
        self._tree = parse(open(mod_path).read())
        self._module = Module(path.basename(self._mod_path).split(".")[0])
        self._dep_graph = DependencyGraph(label=self._module.get_full_name())

    def draw(self, path: str, format: str = "raw") -> None:
        self._module.visit(self._tree)
        for cls in self._module.get_cls_def():
            self._dep_graph.add_node(Node(cls.get_full_name(), 1, label=cls.get_name()))
            for func_def in cls.get_func_def():
                self._dep_graph.add_node(Node(func_def.get_full_name(), 0, parent=cls.get_full_name(), parent_level=1,
                                              label=func_def.get_name()))
                for func_call in func_def.get_func_call():
                    if func_call in cls.get_func_def():
                        self._dep_graph.add_edge(Edge(func_def.get_full_name(), func_call.get_full_name()))

        self._dep_graph.draw(path, format=format)


if __name__ == '__main__':
    start = time.time()
    vis = DepVisual("/Users/Marvin/.pyenv/versions/3.6-dev/lib/python3.6/asyncio/base_events.py")
    vis.draw("/Users/Marvin/PycharmProjects/DepAnalysis/output.png", format="png")

    print(time.time() - start)
