"""
.. module:: scoped_variable_list
   :platform: Unix, Windows
   :synopsis: A module that holds the controller to list and edit all scoped_variables of a state.

.. moduleauthor:: Sebastian Brunner


"""

import gtk
import gobject

from rafcon.statemachine.states.library_state import LibraryState

from rafcon.mvc.controllers.utils.tree_view_controller import ListViewController
from rafcon.mvc.models.container_state import ContainerStateModel

from rafcon.mvc.utils.comparison import compare_variables
from rafcon.utils import log

logger = log.get_logger(__name__)


class ScopedVariableListController(ListViewController):
    """Controller handling the scoped variable list

    :param rafcon.mvc.models.state.StateModel model: The state model, holding state data.
    :param rafcon.mvc.views.scoped_variables_list.ScopedVariablesListView view: The GTK view showing the list of scoped
        variables.
    """
    NAME_STORAGE_ID = 0
    DATA_TYPE_NAME_STORAGE_ID = 1
    DEFAULT_VALUE_STORAGE_ID = 2
    ID_STORAGE_ID = 3
    MODEL_STORAGE_ID = 4

    def __init__(self, model, view):
        """Constructor"""
        super(ScopedVariableListController, self).__init__(model, view, view.get_top_widget(),
                                                           self.get_new_list_store(), logger)

        self.next_focus_column = {}
        self.prev_focus_column = {}

        if self.model.get_sm_m_for_state_m() is not None:
            self.observe_model(self.model.get_sm_m_for_state_m())
        else:
            logger.warning("State model has no state machine model -> state model: {0}".format(self.model))

    @staticmethod
    def get_new_list_store():
        return gtk.ListStore(str, str, str, int, gobject.TYPE_PYOBJECT)

    def register_view(self, view):
        """Called when the View was registered"""
        super(ScopedVariableListController, self).register_view(view)

        view['name_col'].add_attribute(view['name_text'], 'text', self.NAME_STORAGE_ID)
        if not isinstance(self.model.state, LibraryState):
            view['name_text'].set_property("editable", True)
        view['data_type_col'].add_attribute(view['data_type_text'], 'text', self.DATA_TYPE_NAME_STORAGE_ID)
        if not isinstance(self.model.state, LibraryState):
            view['data_type_text'].set_property("editable", True)
        if view['default_value_col'] and view['default_value_text']:
            view['default_value_col'].add_attribute(view['default_value_text'], 'text', self.DEFAULT_VALUE_STORAGE_ID)
            if not isinstance(self.model.state, LibraryState):
                view['default_value_text'].set_property("editable", True)
            self._apply_value_on_edited_and_focus_out(view['default_value_text'],
                                                      self.apply_new_scoped_variable_default_value)

        self._apply_value_on_edited_and_focus_out(view['name_text'], self.apply_new_scoped_variable_name)
        self._apply_value_on_edited_and_focus_out(view['data_type_text'], self.apply_new_scoped_variable_type)

        if isinstance(self.model, ContainerStateModel):
            self.reload_scoped_variables_list_store()

    def register_actions(self, shortcut_manager):
        """Register callback methods for triggered actions

        :param rafcon.mvc.shortcut_manager.ShortcutManager shortcut_manager: Shortcut Manager Object holding mappings
            between shortcuts and actions.
        """
        if not isinstance(self.model.state, LibraryState):
            shortcut_manager.add_callback_for_action("delete", self.remove_action_callback)
            shortcut_manager.add_callback_for_action("add", self.add_action_callback)

    def get_state_machine_selection(self):
        # print type(self).__name__, "get state machine selection"
        sm_selection = self.model.get_sm_m_for_state_m().selection
        return sm_selection, sm_selection.scoped_variables

    @ListViewController.observe("selection", after=True)
    def state_machine_selection_changed(self, model, prop_name, info):
        if "scoped_variables" == info['method_name']:
            self.update_selection_sm_prior()

    @ListViewController.observe("scoped_variables", after=True)
    def scoped_variables_changed(self, model, prop_name, info):
        # store port selection
        path_list = None
        if self.view is not None:
            model, path_list = self.view.get_top_widget().get_selection().get_selected_rows()
        selected_data_port_ids = [self.list_store[path[0]][self.ID_STORAGE_ID] for path in path_list] if path_list else []
        self.reload_scoped_variables_list_store()
        # recover port selection
        if selected_data_port_ids:
            [self.select_entry(selected_data_port_id, False) for selected_data_port_id in selected_data_port_ids]

    def on_add(self, widget, data=None):
        """Create a new scoped variable with default values"""
        if isinstance(self.model, ContainerStateModel):
            num_data_ports = len(self.model.state.scoped_variables)
            data_port_id = None
            for run_id in range(num_data_ports + 1, 0, -1):
                try:
                    data_port_id = self.model.state.add_scoped_variable("scoped_%s" % run_id, "int", 0)
                    break
                except ValueError as e:
                    if run_id == num_data_ports:
                        logger.warn("The scoped variable couldn't be added: {0}".format(e))
                        return False
            self.select_entry(data_port_id)
            return True

    def remove_core_element(self, model):
        """Remove respective core element of handed scoped variable model

        :param ScopedVariableModel model: Scoped variable model which core element should be removed
        :return:
        """
        assert model.scoped_variable.parent is self.model.state
        self.model.state.remove_scoped_variable(model.scoped_variable.data_port_id)

    def apply_new_scoped_variable_name(self, path, new_name):
        """Applies the new name of the scoped variable defined by path

        :param str path: The path identifying the edited variable
        :param str new_name: New name
        """
        data_port_id = self.list_store[path][self.ID_STORAGE_ID]
        try:
            if self.model.state.scoped_variables[data_port_id].name != new_name:
                self.model.state.scoped_variables[data_port_id].name = new_name
        except TypeError as e:
            logger.error("Error while changing port name: {0}".format(e))

    def apply_new_scoped_variable_type(self, path, new_variable_type_str):
        """Applies the new data type of the scoped variable defined by path

        :param str path: The path identifying the edited variable
        :param str new_variable_type_str: New data type as str
        """
        data_port_id = self.list_store[path][self.ID_STORAGE_ID]
        try:
            if self.model.state.scoped_variables[data_port_id].data_type.__name__ != new_variable_type_str:
                self.model.state.scoped_variables[data_port_id].change_data_type(new_variable_type_str)
        except ValueError as e:
            logger.error("Error while changing data type: {0}".format(e))

    def apply_new_scoped_variable_default_value(self, path, new_default_value_str):
        """Applies the new default value of the scoped variable defined by path

        :param str path: The path identifying the edited variable
        :param str new_default_value_str: New default value as string
        """
        data_port_id = self.get_list_store_row_from_cursor_selection()[self.ID_STORAGE_ID]
        try:
            if str(self.model.state.scoped_variables[data_port_id].default_value) != new_default_value_str:
                self.model.state.scoped_variables[data_port_id].default_value = new_default_value_str
        except (TypeError, AttributeError) as e:
            logger.error("Error while changing default value: {0}".format(e))

    def on_right_click_menu(self):
        pass

    def reload_scoped_variables_list_store(self):
        """Reloads the scoped variable list store from the data port models"""

        if isinstance(self.model, ContainerStateModel):
            tmp = self.get_new_list_store()
            for sv_model in self.model.scoped_variables:
                data_type = sv_model.scoped_variable.data_type
                # get name of type (e.g. ndarray)
                data_type_name = data_type.__name__
                # get module of type, e.g. numpy
                data_type_module = data_type.__module__
                # if the type is not a builtin type, also show the module
                if data_type_module != '__builtin__':
                    data_type_name = data_type_module + '.' + data_type_name
                tmp.append([sv_model.scoped_variable.name, data_type_name,
                            sv_model.scoped_variable.default_value, sv_model.scoped_variable.data_port_id, sv_model])
            tms = gtk.TreeModelSort(tmp)
            tms.set_sort_column_id(0, gtk.SORT_ASCENDING)
            tms.set_sort_func(0, compare_variables)
            tms.sort_column_changed()
            tmp = tms
            self.list_store.clear()
            for elem in tmp:
                self.list_store.append(elem)
        else:
            raise RuntimeError("The reload_scoped_variables_list_store function should be never called for "
                               "a non Container State Model")

