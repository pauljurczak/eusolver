#!/usr/bin/env python3
# exprs.py ---
#
# Filename: exprs.py
# Author: Abhishek Udupa
# Created: Wed Aug 19 15:47:31 2015 (-0400)
#
#
# Copyright (c) 2015, Abhishek Udupa, University of Pennsylvania
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by The University of Pennsylvania
# 4. Neither the name of the University of Pennsylvania nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#

# Code:

"""Implements an expression type, along with a manager to create
expressions as needed
"""

import utils
import sys
import collections
from enum import IntEnum
import exprtypes

if __name__ == '__main__':
    utils.print_module_misuse_and_exit()

class ExpressionKinds(IntEnum):
    """Expression Kinds
    variable_expression: An expression representing a typed variable.
    constant_expression: An expression representing a typed constant.
    function_expression: An expression representing a function application.
    """
    variable_expression = 1
    formal_parameter_expression = 2
    constant_expression = 3
    function_expression = 4


_VariableExpression = collections.namedtuple('VariableExpression',
                                             ['expr_kind', 'variable_info'])

_FormalParameterExpression = collections.namedtuple('FormalParameterExpression',
                                                    ['expr_kind',
                                                     'unknown_function_info',
                                                     'parameter_type',
                                                     'parameter_position'])

_ConstantExpression = collections.namedtuple('ConstantExpression',
                                             ['expr_kind', 'value_object'])

_FunctionExpression = collections.namedtuple('FunctionExpression',
                                             ['expr_kind', 'function_info', 'children'])

Value = collections.namedtuple('Value', ['value_object', 'value_type'])

def VariableExpression(variable_info):
    return _VariableExpression(ExpressionKinds.variable_expression, variable_info)

def ConstantExpression(value_object):
    return _ConstantExpression(ExpressionKinds.constant_expression, value_object)

def FunctionExpression(function_info, children):
    return _FunctionExpression(ExpressionKinds.function_expression,
                               function_info, children)

def FormalParameterExpression(unknown_function_info, parameter_type, parameter_position):
    return _FormalParameterExpression(ExpressionKinds.formal_parameter_expression,
                                      unknown_function_info, parameter_type,
                                      parameter_position)

def value_to_string(the_value):
    if (the_value.value_type.type_code == exprtypes.TypeCodes.boolean_type):
        if (the_value.value_object == True):
            return 'true'
        else:
            return 'false'
    elif (the_value.value_type.type_code == exprtypes.TypeCodes.integer_type):
        return str(the_value.value_object)
    elif (the_value.value_type.type_code == exprtypes.TypeCodes.bit_vector_type):
        return utils.bitvector_to_string(the_value.value_object, the_value.value_type.size)


class VariableInfo(object):
    __slots__ = ['variable_type', 'variable_eval_offset',
                 'variable_name', 'synthesis_ctx']
    _undefined_offset = 1000000000

    def __init__(self, variable_type, variable_name,
                 variable_eval_offset = _undefined_offset,
                 synthesis_ctx = None):
        self.variable_name = variable_name
        self.variable_type = variable_type
        self.variable_eval_offset = variable_eval_offset
        self.synthesis_ctx = None

    def __str__(self):
        return ('VariableInfo(%s, %s, %s)' % (str(self.variable_type),
                                              self.variable_name,
                                              str(self.variable_eval_offset)))


def _constant_to_string(constant_type, constant_value):
    if (constant_type == exprtypes.BoolType() or
        constant_type == exprtypes.IntType()):
        return str(constant_value)
    else:
        return utils.bitvector_to_string(constant_value, constant_type.size)


def expression_to_string(expr):
    """Returns a string representation of an expression"""

    if (expr.expr_kind == ExpressionKinds.variable_expression):
        return expr.variable_info.variable_name
    elif (expr.expr_kind == ExpressionKinds.formal_parameter_expression):
        return '_arg_%d' % expr.parameter_position
    elif (expr.expr_kind == ExpressionKinds.constant_expression):
        return _constant_to_string(expr.value_object.value_type,
                                   expr.value_object.value_object)
    else:
        retval = '(' + expr.function_info.function_name
        for child in expr.children:
            retval += ' '
            retval += expression_to_string(child)
        retval += ')'
        return retval


def get_expression_type(expr):
    """Returns the type of the expression."""
    if (expr.expr_kind == ExpressionKinds.variable_expression):
        return expr.variable_info.variable_type
    elif (expr.expr_kind == ExpressionKinds.formal_parameter_expression):
        return expr.parameter_type
    elif (expr.expr_kind == ExpressionKinds.constant_expression):
        return expr.value_object.value_type
    elif (expr.expr_kind == ExpressionKinds.function_expression):
        return expr.function_info.range_type
    else:
        raise basetypes.UnhandledCaseError('Odd expression kind: %s' % expr.expr_kind)

def get_expression_size(expr):
    """Returns the (syntactic) size of the expression."""
    if (expr.expr_kind == ExpressionKinds.variable_expression or
        expr.expr_kind == ExpressionKinds.constant_expression or
        expr.expr_kind == ExpressionKinds.formal_parameter_expression):
        return 1
    elif (expr.expr_kind == ExpressionKinds.function_expression):
        retval = 1
        for child in expr.children:
            retval += get_expression_size(child)
        return retval
    else:
        raise basetypes.UnhandledCaseError('Odd expression kind: %s' % expr.expr_kind)

def substitute(expr, old_term, new_term, syn_ctx):
    if (expr == old_term):
        return new_term
    kind = expr.expr_kind
    if (kind == ExpressionKinds.function_expression):
        subst_children = [substitute(x, old_term, new_term, syn_ctx)
                          for x in expr.children]
        return syn_ctx.make_function_expr(expr.function_info, *subst_children)
    else:
        return expr

#
# exprs.py ends here
