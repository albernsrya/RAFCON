from weakref import ref

from gaphas.item import Element, NW, NE, SW, SE
from gaphas.connector import Position

from gaphas.util import text_align, text_set_font, text_extents

from awesome_tool.mvc.views.gap.constraint import EqualDistributionConstraint, KeepRectangleWithinConstraint
from awesome_tool.mvc.views.gap.ports import IncomeView, OutcomeView, InputPortView, OutputPortView
from awesome_tool.mvc.views.gap.scope import ScopedVariableView

from awesome_tool.mvc.models.state import StateModel

class StateView(Element):
    """ A State has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """

    def __init__(self, state_m, size):
        super(StateView, self).__init__(size[0], size[1])
        assert isinstance(state_m, StateModel)

        self._state_m = ref(state_m)

        self.min_width = 0.0001
        self.min_height = 0.0001
        self.width = size[0]
        self.height = size[1]

        self._left_center = Position((0, self.height / 2.))
        self._right_center = Position((self.width, self.height / 2.))
        self.constraint(line=(self._left_center, (self._handles[NW].pos, self._handles[SW].pos)), align=0.5)
        self.constraint(line=(self._right_center, (self._handles[NE].pos, self._handles[SE].pos)), align=0.5)

        self._income = IncomeView()
        self.constraint(line=(self._income.pos, (self._handles[NW].pos, self._left_center)), align=0.5)

        self._outcomes = []
        self._outcomes_distribution = EqualDistributionConstraint((self._handles[NE].pos, self._right_center))

        self._inputs = []
        self._inputs_distribution = EqualDistributionConstraint((self._handles[SW].pos, self._left_center))

        self._outputs = []
        self._outputs_distribution = EqualDistributionConstraint((self._handles[SE].pos, self._right_center))

        self._scoped_variables = []

    def setup_canvas(self):
        canvas = self.canvas
        parent = canvas.get_parent(self)

        solver = canvas.solver
        solver.add_constraint(self._outcomes_distribution)
        solver.add_constraint(self._inputs_distribution)
        solver.add_constraint(self._outputs_distribution)

        if parent is not None:
            assert isinstance(parent, StateView)
            self_nw_abs = canvas.project(self, self.handles()[NW].pos)
            self_se_abs = canvas.project(self, self.handles()[SE].pos)
            parent_nw_abs = canvas.project(parent, parent.handles()[NW].pos)
            parent_se_abs = canvas.project(parent, parent.handles()[SE].pos)
            constraint = KeepRectangleWithinConstraint(parent_nw_abs, parent_se_abs, self_nw_abs, self_se_abs)
            solver.add_constraint(constraint)

        # Registers local constraints
        super(StateView, self).setup_canvas()

    @property
    def state_m(self):
        return self._state_m()

    def draw(self, context):
        c = context.cairo
        c.set_line_width(0.5)
        nw = self._handles[NW].pos
        c.rectangle(nw.x, nw.y, self.width, self.height)
        if context.hovered:
            c.set_source_rgba(.8, .8, 1, .8)
        else:
            c.set_source_rgba(1, 1, 1, .8)
        c.fill_preserve()
        c.set_source_rgb(0, 0, 0.8)
        c.stroke()

        name = self.state_m.state.name
        c.set_source_rgba(0, 0, 0, 1)
        padding = min(self.width / 30, self.height / 30, 2)
        font_name = 'DIN Next LT Pro'
        size = 12
        def font_string():
            return font_name + " " + str(size)
        while text_extents(c, name, font_string(), padding)[0] > (self.width * 0.7) - 2 * padding:
            size -= 0.25
        text_set_font(c, font_string())
        text_align(c, nw.x, nw.y, name, 1, 1, padding, padding)

        self._income.draw(context, self)

        for outcome in self._outcomes:
            outcome.draw(context, self)

        for input in self._inputs:
            input.draw(context, self)

        for output in self._outputs:
            output.draw(context, self)

    def connect_to_income(self, item, handle):
        self._connect_to_port(self._income.port, item, handle)

    def connect_to_outcome(self, outcome_id, item, handle):
        outcome_v = self.outcome_port(outcome_id)
        self._connect_to_port(outcome_v.port, item, handle)

    def connect_to_input_port(self, port_id, item, handle):
        port_v = self.input_port(port_id)
        self._connect_to_port(port_v.port, item, handle)

    def connect_to_output_port(self, port_id, item, handle):
        port_v = self.output_port(port_id)
        self._connect_to_port(port_v.port, item, handle)

    def connect_to_scoped_variable_input(self, scoped_variable_id, item, handle):
        scoped_variable_v = self.scoped_variable(scoped_variable_id)
        c = scoped_variable_v.input_port.constraint(self.canvas, item, handle, scoped_variable_v)
        self.canvas.connect_item(item, handle, scoped_variable_v, scoped_variable_v.input_port, c)

    def connect_to_scoped_variable_output(self, scoped_variable_id, item, handle):
        scoped_variable_v = self.scoped_variable(scoped_variable_id)
        c = scoped_variable_v.output_port.constraint(self.canvas, item, handle, scoped_variable_v)
        self.canvas.connect_item(item, handle, scoped_variable_v, scoped_variable_v.output_port, c)

    def _connect_to_port(self, port, item, handle):
        c = port.constraint(self.canvas, item, handle, self)
        self.canvas.connect_item(item, handle, self, port, c)

    def income_port(self):
        return self._income

    def outcome_port(self, outcome_id):
        for outcome in self._outcomes:
            if outcome.outcome_id == outcome_id:
                return outcome
        raise AttributeError("Outcome with id '{0}' not found in state".format(outcome_id, self.state_m.state.name))

    def input_port(self, port_id):
        return self._data_port(self._inputs, port_id)

    def output_port(self, port_id):
        return self._data_port(self._outputs, port_id)

    def scoped_variable(self, scoped_variable_id):
        return self._data_port(self._scoped_variables, scoped_variable_id)

    def _data_port(self, port_list, port_id):
        for port in port_list:
            if port.port_id == port_id:
                return port
        raise AttributeError("Port with id '{0}' not found in state".format(port_id, self.state_m.state.name))

    def add_outcome(self, outcome_m):
        outcome_v = OutcomeView(outcome_m)
        self._outcomes.append(outcome_v)
        self._ports.append(outcome_v.port)
        self._handles.append(outcome_v.handle)
        self._outcomes_distribution.add_point(outcome_v.pos, outcome_v.sort)

    def add_input_port(self, port_m):
        input_port_v = InputPortView(port_m)
        self._inputs.append(input_port_v)
        self._ports.append(input_port_v.port)
        self._handles.append(input_port_v.handle)
        self._inputs_distribution.add_point(input_port_v.pos, input_port_v.sort)

    def add_output_port(self, port_m):
        output_port_v = OutputPortView(port_m)
        self._outputs.append(output_port_v)
        self._ports.append(output_port_v.port)
        self._handles.append(output_port_v.handle)
        self._outputs_distribution.add_point(output_port_v.pos, output_port_v.sort)

    def add_scoped_variable(self, scoped_variable_m, size):
        scoped_variable_v = ScopedVariableView(scoped_variable_m, size)
        self._scoped_variables.append(scoped_variable_v)

        canvas = self.canvas
        canvas.add(scoped_variable_v, self)

        self_nw_abs = canvas.project(self, self.handles()[NW].pos)
        self_se_abs = canvas.project(self, self.handles()[SE].pos)
        scoped_nw_abs = canvas.project(scoped_variable_v, scoped_variable_v.handles()[NW].pos)
        scoped_se_abs = canvas.project(scoped_variable_v, scoped_variable_v.handles()[SE].pos)
        constraint = KeepRectangleWithinConstraint(self_nw_abs, self_se_abs, scoped_nw_abs, scoped_se_abs)
        solver = canvas.solver
        solver.add_constraint(constraint)

        return scoped_variable_v