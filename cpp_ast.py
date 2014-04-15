from ast import *

class CFunctionNode (FunctionNode):
  def __init__(self, name):
    super(CFunctionNode, self).__init__(name)
  
  def copy():
    c = CFunctionNode(self.name)
    self.copy_basic(c)
    self.copy_children(c)
    
    return c
    
  def gen_js(self, tlevel):
    s = ""
    tlevel -= 1
    
    t = tab(tlevel)
    s += t
    
    if self.type == None:
      s += "void "
    else:
      s += self.type.get_type_str() + " "
    
    s += self.name + "("
    for i, c in enumerate(self[0]):
      if i > 0: s += ", "
      s += c.type.get_type_str() + " " + c.gen_js(0)
    
    s += ") {\n"
    
    for c in self[1:]:
      s += c.gen_js(tlevel+1)
      if not s.endswith("\n"): s += "\n"
      
    s += t + "}\n\n"
    
    return s

class CppCode (Node):
  def __init__(self, code):
    Node.__init__(self)
    self.code = code
  
  def gen_js(self, tlevel):
    return self.code
    