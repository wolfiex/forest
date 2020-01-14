import copy
import bokeh.models
import bokeh.layouts
import numpy as np
from typing import Iterable
from forest import rx
from forest.redux import Action, State, Store
from forest.observe import Observable
from forest.db.util import autolabel


SET_FIGURES = "SET_FIGURES"
LAYERS_ON_ADD = "LAYERS_ON_ADD"
LAYERS_ON_REMOVE = "LAYERS_ON_REMOVE"
LAYERS_ON_VISIBLE_STATE = "LAYERS_ON_VISIBLE_STATE"
LAYERS_SET_LABEL = "LAYERS_SET_LABEL"
LAYERS_SET_VISIBLE = "LAYERS_SET_VISIBLE"


def set_figures(n: int) -> Action:
    return {"kind": SET_FIGURES, "payload": n}


def on_add() -> Action:
    return {"kind": LAYERS_ON_ADD}


def on_remove() -> Action:
    return {"kind": LAYERS_ON_REMOVE}


def on_visible_state(visible_state) -> Action:
    return {"kind": LAYERS_ON_VISIBLE_STATE, "payload": visible_state}


def set_label(index: int, label: str) -> Action:
    """Set i-th layer label"""
    return {"kind": LAYERS_SET_LABEL, "payload": {"index": index, "label": label}}


def set_visible(payload) -> Action:
    return {"kind": LAYERS_SET_VISIBLE, "payload": payload}


def middleware(store: Store, action: Action) -> Iterable[Action]:
    """Action generator given current state and action"""
    yield action


def reducer(state: State, action: Action) -> State:
    """Combine state and action to produce new state"""
    state = copy.deepcopy(state)
    kind = action["kind"]
    if kind == SET_FIGURES:
        state["figures"] = action["payload"]
    elif kind == LAYERS_ON_ADD:
        labels = state.get("layers", [])
        labels.append(None)
        state["layers"] = labels
    elif kind == LAYERS_ON_REMOVE:
        labels = state.get("layers", [])
        state["layers"] = labels[:-1]
    elif kind == LAYERS_SET_LABEL:
        index = action["payload"]["index"]
        label = action["payload"]["label"]
        labels = state.get("layers", [])

        # Pad labels with None for each missing element
        missing_elements = (index + 1) - len(labels)
        if missing_elements > 0:
            labels += missing_elements * [None]
        labels[index] = label
        state["layers"] = labels
    elif kind == LAYERS_SET_VISIBLE:
        visible = state.get("visible", {})
        visible.update(action["payload"])
        state["visible"] = visible
    return state


def _connect(view, store):
    stream = (rx.Stream()
                .listen_to(store)
                .map(view.to_props)
                .filter(lambda x: x is not None)
                .distinct())
    stream.map(lambda props: view.render(*props))


class Counter:
    """Reactive layer counter component"""
    def __init__(self):
        self.div = bokeh.models.Div(text="Hello, world")
        self.layout = bokeh.layouts.row(self.div)

    def connect(self, store):
        _connect(self, store)
        return self

    @staticmethod
    def to_props(state):
        return (len(state.get("layers", [])),)

    def render(self, n):
        self.div.text = f"Rows: {n}"


class FigureUI(Observable):
    """Controls how many figures are currently displayed"""
    def __init__(self):
        self.labels = [
            "Single figure",
            "Side by side",
            "3 way comparison"]
        self.select = bokeh.models.Select(
            options=self.labels,
            value="Single figure",
            width=350,
        )
        self.select.on_change("value", self.on_change)
        self.layout = bokeh.layouts.column(
            self.select,
        )
        super().__init__()

    def on_change(self, attr, old, new):
        n = self.labels.index(new) + 1 # Select 0-indexed
        self.notify(set_figures(n))


class FigureRow:
    def __init__(self, figures):
        self.figures = figures
        self.layout = bokeh.layouts.row(*figures,
                sizing_mode="stretch_both")
        self.layout.children = [self.figures[0]]  # Trick to keep correct sizing modes

    def connect(self, store):
        stream = (rx.Stream()
                    .listen_to(store)
                    .map(self.to_props)
                    .filter(lambda x: x is not None)
                    .distinct())
        stream.map(lambda props: self.render(*props))

    def to_props(self, state):
        try:
            return (state["figures"],)
        except KeyError:
            pass

    def render(self, n):
        if int(n) == 1:
            self.layout.children = [
                    self.figures[0]]
        elif int(n) == 2:
            self.layout.children = [
                    self.figures[0],
                    self.figures[1]]
        elif int(n) == 3:
            self.layout.children = [
                    self.figures[0],
                    self.figures[1],
                    self.figures[2]]


class LeftCenterRight:
    # TODO: Inline this class into Controls
    def __init__(self, controls):
        self.controls = controls

    def connect(self, store):
        stream = (rx.Stream()
                    .listen_to(store)
                    .map(self.to_props)
                    .filter(lambda x: x is not None)
                    .distinct())
        stream.map(lambda props: self.render(*props))

    def to_props(self, state):
        try:
            return (state["figures"],)
        except KeyError:
            pass

    def render(self, n):
        if int(n) == 1:
            self.controls.labels = ["Show"]
        elif int(n) == 2:
            self.controls.labels = ["L", "R"]
        elif int(n) == 3:
            self.controls.labels = ["L", "C", "R"]


class Controls(Observable):
    """Collection of user interface components to manage layers"""
    def __init__(self, menu):
        self.defaults = {
            "label": "Model/observation",
            "flags": [False, False, False]
        }
        self.buttons = {
            "add": bokeh.models.Button(label="Add", width=50),
            "remove": bokeh.models.Button(label="Remove", width=50)
        }
        self.buttons["add"].on_click(self.on_click_add)
        self.buttons["remove"].on_click(self.on_click_remove)
        self.columns = {
            "rows": bokeh.layouts.column(),
            "buttons": bokeh.layouts.column(
                bokeh.layouts.row(self.buttons["add"], self.buttons["remove"])
            )
        }
        self.layout = bokeh.layouts.column(
            self.columns["rows"],
            self.columns["buttons"]
        )

        # TODO: remove the following variables
        self.menu = menu
        self.models = {}
        self.flags = {}

        self._labels = ["Show"]

        self.groups = []
        self.dropdowns = []

        # self.add_row()
        super().__init__()

    def connect(self, store):
        """Connect component to store"""
        _connect(self, store)
        return self

    @staticmethod
    def to_props(state) -> tuple:
        """Select data from state that satisfies self.render(*props)"""
        return (state.get("layers", []),)

    def render(self, labels):
        """Display latest application state in user interface

        :param n: integer representing number of rows
        """
        print(self.flags)
        self.models = dict(enumerate(labels))  # TODO: remove this

        n = len(labels)
        nrows = len(self.columns["rows"].children) # - 1
        if n > nrows:
            for _ in range(n - nrows):
                self.add_row()
        if n < nrows:
            for _ in range(nrows - n):
                self.remove_row()

        # Set dropdown labels
        for label, dropdown in zip(labels, self.dropdowns):
            if label is None:
                dropdown.label = self.defaults["label"]
            else:
                dropdown.label = label

    def on_click_add(self):
        """Event-handler when Add button is clicked"""
        self.notify(on_add())

    def on_click_remove(self):
        """Event-handler when Remove button is clicked"""
        self.notify(on_remove())

    def select(self, name):
        """Select particular layers and visibility states

        .. note:: Called in main.py to select first layer
        """
        return
        self.groups[0].active = [0]
        dropdown = self.dropdowns[0]
        for k, v in dropdown.menu:
            if k == name:
                dropdown.value = v

    @property
    def labels(self):
        return self._labels

    @labels.setter
    def labels(self, labels):
        self._labels = labels
        for g in self.groups:
            g.labels = labels

    def add_row(self):
        """Add a bokeh.layouts.row with a dropdown and radiobuttongroup"""
        i = self.rows

        irow = len(self.columns["rows"].children)
        dropdown = bokeh.models.Dropdown(
                menu=self.menu,
                label=self.defaults["label"],
                width=230,)
        dropdown.on_change('value', self.on_label(irow))
        self.dropdowns.append(dropdown)

        group = bokeh.models.CheckboxButtonGroup(
                labels=self.labels,
                width=50)
        group.on_change("active", self.on_radio(i))
        self.groups.append(group)

        row = bokeh.layouts.row(dropdown, group)
        self.columns["rows"].children.append(row)

    def remove_row(self):
        """Remove a row from self.column"""
        if len(self.columns["rows"].children) > 1:
            i = self.rows # - 1
            self.flags.pop(i, None)
            self.dropdowns.pop(-1)
            self.groups.pop(-1)
            self.columns["rows"].children.pop(-1)

    @property
    def rows(self):
        return len(self.columns["rows"].children) - 1

    def on_label(self, irow):
        """Notify listeners of set_label action"""
        def wrapper(attr, old, new):
            if old != new:
                self.notify(set_label(irow, new))
        return wrapper

    def on_radio(self, i):
        """Factory to create radiogroup callback with row number baked in

        This handler performs reducer logic that could be implemented
        elsewhere

        :returns: callback with (attr, old, new) signature
        """
        def wrapper(attr, old, new):
            if i not in self.flags:
                self.flags[i] = list(self.defaults["flags"])

            flags = self.flags[i]
            for j in old:
                if j not in new:
                    flags[j] = False
            for j in new:
                if j not in old:
                    flags[j] = True
            self._render()
        return wrapper

    def _render(self):
        """This is not a render method"""
        self.notify(on_visible_state(self.combine(self.models, self.flags)))

    @staticmethod
    def combine(models, flags):
        """Combine model selection and visiblity settings into a single dict

        Handles case where multiple dropdowns refer to the same layer
        but may have different radio button choices

        :returns: dict
        """
        agg = {}
        for k in set(models.keys()).intersection(
                set(flags.keys())):
            if models[k] in agg:
                agg[models[k]].append(flags[k])
            else:
                agg[models[k]] = [flags[k]]
        combined = {}
        for k, v in agg.items():
            if len(agg[k]) > 1:
                combined[k] = np.logical_or(*agg[k]).tolist()
            else:
                combined[k] = agg[k][0]
        return combined


class Artist(object):
    """Applies visible and render logic to viewers and renderers


    This could easily be broken into two classes, one responsible
    for maintaining ``renderer.visible`` and one for calling
    ``viewer.render(state)``


    .. note:: This should be middleware that applies logic
              given current state and an action
    """
    def __init__(self, viewers, renderers):
        self.viewers = viewers
        self.renderers = renderers
        self.visible_state = None
        self.state = None

    def on_visible(self, action):
        """

        Uses current visible layers and incoming visible state to toggle
        on/off GlyphRenderers

        """
        # Ignore actions for now
        # TODO: Refactor to use application state or state_to_props
        kind = action["kind"]
        if kind != LAYERS_ON_VISIBLE_STATE:
            return

        visible_state = action["payload"]

        if self.visible_state is not None:
            # Hide deselected states
            lost_items = (
                    set(self.flatten(self.visible_state)) -
                    set(self.flatten(visible_state)))
            for key, i, _ in lost_items:
                self.renderers[key][i].visible = False

        # Sync visible states with menu choices
        states = set(self.flatten(visible_state))
        hidden = [(i, j) for i, j, v in states if not v]
        visible = [(i, j) for i, j, v in states if v]
        for i, j in hidden:
            self.renderers[i][j].visible = False
        for i, j in visible:
            self.renderers[i][j].visible = True

        self.visible_state = dict(visible_state)
        self.render()

    @staticmethod
    def flatten(state):
        items = []
        for key, flags in state.items():
            items += [(key, i, f) for i, f in enumerate(flags)]
        return items

    def on_state(self, app_state):
        """On application state handler"""
        # print("Artist: {}".format(app_state))
        self.state = app_state
        self.render()

    def render(self):
        """

        Notify visible viewers to render themselves given most
        recently received application state

        """
        if self.visible_state is None:
            return
        if self.state is None:
            return
        for name in self.visible_state:
            viewer = self.viewers[name]
            viewer.render(self.state)
