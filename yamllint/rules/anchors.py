# Copyright (C) 2023 Adrien Vergé
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Use this rule to report duplicated anchors and aliases referencing undeclared
anchors.

.. rubric:: Options

* Set ``forbid-undeclared-aliases`` to ``true`` to avoid aliases that reference
  an anchor that hasn't been declared (either not declared at all, or declared
  later in the document).
* Set ``forbid-duplicated-anchors`` to ``true`` to avoid duplications of a same
  anchor.

.. rubric:: Default values (when enabled)

.. code-block:: yaml

 rules:
   anchors:
     forbid-undeclared-aliases: true
     forbid-duplicated-anchors: false

.. rubric:: Examples

#. With ``anchors: {forbid-undeclared-aliases: true}``

   the following code snippet would **PASS**:
   ::

    ---
    - &anchor
      foo: bar
    - *anchor

   the following code snippet would **FAIL**:
   ::

    ---
    - &anchor
      foo: bar
    - *unknown

   the following code snippet would **FAIL**:
   ::

    ---
    - &anchor
      foo: bar
    - <<: *unknown
      extra: value

#. With ``anchors: {forbid-duplicated-anchors: true}``

   the following code snippet would **PASS**:
   ::

    ---
    - &anchor1 Foo Bar
    - &anchor2 [item 1, item 2]

   the following code snippet would **FAIL**:
   ::

    ---
    - &anchor Foo Bar
    - &anchor [item 1, item 2]
"""


import yaml

from yamllint.linter import LintProblem


ID = 'anchors'
TYPE = 'token'
CONF = {'forbid-undeclared-aliases': bool,
        'forbid-duplicated-anchors': bool,
        'forbid-unused-anchors': bool}
DEFAULT = {'forbid-undeclared-aliases': True,
           'forbid-duplicated-anchors': False,
           'forbid-unused-anchors': False}


def check(conf, token, prev, next, nextnext, context):
    if conf['forbid-undeclared-aliases'] or conf['forbid-duplicated-anchors'] or conf['forbid-unused-anchors']:
        if isinstance(token, (yaml.StreamStartToken, yaml.DocumentStartToken, yaml.DocumentEndToken)):
            # context['anchors'] = set()
            context['anchors'] = list()
            # context['aliases'] = set()

    if (conf['forbid-undeclared-aliases'] and
            isinstance(token, yaml.AliasToken) and
            # token.value not in context['anchors']):
            not any(anchors['value'] == token.value for anchors in context['anchors'])):
        yield LintProblem(
            token.start_mark.line + 1, token.start_mark.column + 1,
            f'found undeclared alias "{token.value}"')

    if (conf['forbid-duplicated-anchors'] and
            isinstance(token, yaml.AnchorToken) and
            # token.value in context['anchors']):
            any(anchors['value'] == token.value for anchors in context['anchors'])):
        yield LintProblem(
            token.start_mark.line + 1, token.start_mark.column + 1,
            f'found duplicated anchor "{token.value}"')
        
    if (conf['forbid-unused-anchors']):
        if (isinstance(next, (yaml.DocumentStartToken, yaml.DocumentEndToken, yaml.StreamEndToken)) and
            len(context['anchors']) > 0):
            # Unused anchors can only be detected at the end of Document.
            # End of document can be either '...' (DocumentEndToken) or '---' (DocumentStartToken)
            # for multiple documents in same file
            # or end of stream containing a single/multiple documents.
            print("checking unused anchors")
            print(context['anchors'])
            # print(context['aliases'])
            for anchor in context['anchors']:
                if anchor['aliasCount'] == 0:
                    yield LintProblem(
                        anchor['line'], anchor['column'],
                        f'found unused anchor ' + anchor['value']
                    )
        elif(isinstance(token, yaml.AliasToken)):
            for anchor in context['anchors']:
                if anchor['value'] == token.value:
                    anchor['aliasCount'] += 1
                    break
            # Record the alias in the anchor.
            # It can be used to detect if an anchor
            # does not have an alias and reported as a problem.
            
            # matchingAnchor = next((anchor for anchor in context['anchors'] if anchor["value"] == token.value), None)

            # print("recording aliases " + token.value)
            # context['aliases'].add(token.value)

    if conf['forbid-undeclared-aliases'] or conf['forbid-duplicated-anchors'] or conf['forbid-unused-anchors']:
        if isinstance(token, yaml.AnchorToken) and not any(anchors['value'] == token.value for anchors in context['anchors']):
            anchor = {
                "value": token.value,
                "line": token.start_mark.line + 1,
                "column": token.start_mark.column + 1,
                "aliasCount": 0
            }
            # Keep record of the anchor
            context['anchors'].append(anchor)
        # if isinstance(token, yaml.AliasToken):
        #     context['aliases'].add(token.value)
        #     # alias = {
        #     #     "line": token.start_mark.line + 1,
        #     #     "column": token.start_mark.column + 1
        #     # }