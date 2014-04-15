import ply.yacc as yacc
import sys, os, os.path
import traceback

# Get the token map from the lexer.  This is required.
from config import glob

from ast import *
from lex import tokens, StringLit, HexInt
from ply.lex import LexToken, Lexer

from parse import *
import parse as jsp

template_parser = yacc.yacc(debug=False, tabmodule="template_parsetab", start='template_validate')

def template_parse(s):
  from lex import tmp_lexer
  push_state()
  ret = template_parser.parse(s, lexer=tmp_lexer)
  pop_state()
  
  return ret

def template_validate(s):
  from lex import tmp_lexer
  
  jsp.push_state()
  glob.g_validate_mode = True
  ret = template_parser.parse(s, lexer=tmp_lexer)
  jsp.pop_state()
  
  return ret != None
