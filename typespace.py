import sys

from config import glob, Glob

from ast import *
from process_ast import *
from dcc import parse

import traceback

builtin_types = [
  "Object",
  "String",
  "Number",
  "Array",
  "Boolean",
  "Iterator",
  "CanIterate",
  "Float32Array",
  "Uint8Array",
  "Uint16Array",
  "Uint32Array",
  "Int32Array",
  "ArrayBuffer",
  "WebGLRenderingContext",
  "WebGLUnifornLocation",
  "MouseEvent",
  "KeyboardEvent",
  "KeyEvent",
  "undefined",
  "ObjectMap",
  "Function",
  "console",
  "Math",
  "WebKitCSSMatrix",
]

builtin_functions = [
]

builtin_code = {
  "Iterator": """
  function Iterator<T>() {
    this.next = function() : T {
    }
  }
  
  """,
  "CanIterate": """
    function CanIterate<T>() {
      this.__iterator__ = function() : Iterator<T> {
      }
    }
  """,
  "Array": """
    function Array<T>() {
      this.length = 0 : int;
      this.push = function(T item) {
      }
    }
  """,
  "console": """
    function console() {
      this.log = function(String str) {
      }
      
      this.trace = function() {
      }
      
      this.debug = function(String str) {
      }
    }
  """, "Math": """
    function Math() {
      this.sqrt = function(float f) : float {
      }
      
      this.floor = function(float f) : float {
      }
      
      this.abs = function(float f) : float {
      }
      
      this.pi = 3.141592654 : float;
    }
  """
 
}

class JSError (Exception):
  pass

class TypeSpace:
  def empty_type(self):
    n = FunctionNode("(unknown type)", 0)
    n.class_type = "class"
    
    return n
    
  def __init__(self):
    self.functions = {}
    self.types = {}
    self.globals = {}
    self.logrec = []
    self.logmap = {}
    self.builtin_typenames = builtin_types
        
  def add_builtin_methods(self):
    for k in self.functions:
      f = self.functions[k]
      if not node_is_class(f): continue
  
  def warning(self, msg, srcnode):
    sys.stderr.write("\n%s:(%s): warning: %s"%(srcnode.file, srcnode.line+1, msg))
  
  def error(self, msg, srcnode):
    if glob.g_print_stack:
      pass #traceback.print_stack()
    
    sys.stderr.write("\n%s:(%s): error: %s\n"%(srcnode.file, srcnode.line+1, msg))
    sys.stderr.write(" " + glob.g_lines[srcnode.line] + "\n")
    
    raise JSError("%s:(%s): error: %s\n"%(srcnode.file, srcnode.line+1, msg))
  
  def get_type(self, type, scope={}):
    print("typespace.get_type call:", type)
    if type in scope:
      ret = scope[type]
    elif type in self.functions: 
      print(self.functions[type])
      if node_is_class(self.functions[type]):
        ret =  self.functions[type]
      elif self.functions[type].type == None:
        ret = VoidTypeNode()
      else:
        ret = self.functions[type].type
    elif type in self.types:
      ret =  self.types[type]
    else:
      ret =  None
      
    return ret
    
  def limited_eval(self, node):
    if type(node) in [IdentNode, StrLitNode, NumLitNode]:
      return node.val
    elif type(node) in [ExprNode, ExprListNode] and len(node.children) > 0:
      return self.limited_eval(node.children[-1])
    elif type(node) == BinOpNode:
      return self.limited_eval(node.children[1])
    elif type(node) == ArrayRefNode:
      None       
  
  def _find_in_scope(self, name, locals, func):
    globals = self.globals
    
    if name in locals:
      return locals[name]
    elif name in globals:
      return globals[name]
    elif func != None and name in func.members:
      return func.members[name]
    
  def lookup(self, node, locals={}, func=None, depth=0):
    if type(node) == IdentNode:
      if depth == 0:
        return self._find_in_scope(node.val, {}, None)
      else:
        return node
    elif type(node) == BinOpNode and node.op == ".":
      if type(node.children[0]) == IdentNode:
        var = self._find_in_scope(node.children[0].val, locals, func)
        
        if var == None: return None
        
        ret = self.member_lookup(var, node.children[1])
        return ret
      else:
        var = self.lookup(node.children[0], locals, func)
        
        return self.member_lookup(var, node.children[1])
  
  """
  def member_add(self, node, mname, member):
    if type(node) == FunctionNode:
      node.members[mname] = member
    elif type(node) == ObjLitNode:
      node.add(AssignNode(IdentNode(mname), member))
      
  def member_lookup(self, node, member):
    member = member.val
    
    if type(node) == FunctionNode:
      member = "this." + member
      if member in node.members:
        return node.members[member]
    elif type(node) == ObjLitNode:
      for m in node.children:
        mname = self.limited_eval(m.children[0])
        if mname == member:
          return m.children[1]
  """
  
  def build_type(self, node, locals, func):
    is_class = func != None and func_is_class(func)
    
    globals = self.globals
    
    #handle builtins first
    if type(node) == NumLitNode:
      return self.types["number"]
    elif type(node) == StrLitNode:
      return self.types["string"]
    elif type(node) == ArrayLitNode:
      return node
    elif type(node) == ObjLitNode:
      return node
    elif type(node) == FunctionNode:
      return node
      
    if type(node) == IdentNode:
      var = node.val
      if var == "this":
        var = node
        while var != None and not node_is_class(var):
          var = var.parent
        
        if var == None:
          return None
      elif var in locals:
        var = locals[var]
      elif "this." in var and var in func.members:
        var = func.members[var]
      elif var in globals:
        var = globals[var]
      elif var in self.types:
        var = self.types[var]
      else:
        return None
       
      return var
      
    if type(node) == ExprNode:
      return self.build_type(node.children[0], locals, func)
    elif type(node) == BinOpNode:
      if node.op == ".":
        t = self.build_type(node.children[0], locals, func)
        if t != None:
          name = self.limited_eval(node.children[1])
          return self.member_lookup(t, node.children[1])
        else:
          return None
      else:
        return self.build_type(node.children[1], locals, func)
    elif type(node) == KeywordNew:
      var = node.children[0]
      if type(var) == FuncCallNode:
        return self.build_type(var.children[0], locals, func)
      elif type(var) == IdentNode:
        return self.build_type(var, locals, func)
    if type(node) == FuncCallNode:
        return self.build_type(node.children[0], locals, func)
    
    if isinstance(node, BuiltinType):
      return node
    
    print("build_types IMPLEMENT ME: %s"%str(type(node)))
   
  def infer_types(self, nfiles):
      self.filenodes = nfiles
      infer_types(self)
