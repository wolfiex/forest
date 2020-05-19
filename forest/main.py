import bokeh.plotting
import bokeh.models
import bokeh.events
import bokeh.colors
from bokeh.core.properties import value
import os
from forest import _profile as profile
from forest import (
        drivers,
        dimension,
        screen,
        tools,
        series,
        data,
        geo,
        colors,
        layers,
        db,
        keys,
        plugin,
        presets,
        redux,
        rx,
        navigate,
        wind,
        barc,
        parse_args)
import forest.components
from forest.components import tiles
import forest.config as cfg
import forest.middlewares as mws
from forest.db.util import autolabel


def main(argv=None):

    args = parse_args.parse_args(argv)
    data.AUTO_SHUTDOWN = args.auto_shutdown
    
    if len(args.files) > 0:
        if args.config_file is not None:
            raise Exception('--config-file and [FILE [FILE ...]] not compatible')
        config = cfg.from_files(args.files, args.file_type)
    else:
        config = cfg.Config.load(
                args.config_file,
                variables=cfg.combine_variables(
                    os.environ,
                    args.variables))

    # Feature toggles
    if "feature" in config.plugins:
        features = plugin.call(config.plugins["feature"].entry_point)
    else:
        features = config.features
    data.FEATURE_FLAGS = features

    # Full screen map
    viewport = config.default_viewport
    x_range, y_range = geo.web_mercator(
        viewport.lon_range,
        viewport.lat_range)
    figure = bokeh.plotting.figure(
        x_range=x_range,
        y_range=y_range,
        #output_backend = "svg",
        x_axis_type="mercator",
        y_axis_type="mercator",
        active_scroll="wheel_zoom")

    figures = [figure]
    for _ in range(2):
        f = bokeh.plotting.figure(
            x_range=figure.x_range,
            y_range=figure.y_range,
            x_axis_type="mercator",
            y_axis_type="mercator",
            active_scroll="wheel_zoom")
        figures.append(f)

    for f in figures:
        f.axis.visible = False
        f.toolbar.logo = None
        f.toolbar_location = None
        f.min_border = 0

    figure_row = layers.FigureRow(figures)

    color_mapper = bokeh.models.LinearColorMapper(
            low=0,
            high=1,
            palette=bokeh.palettes.Plasma[256])

    # Convert config to datasets
    datasets = {}
    datasets_by_pattern = {}
    label_to_pattern = {}
    for group in config.file_groups:
        settings = {
            "label": group.label,
            "pattern": group.pattern,
            "locator": group.locator,
            "database_path": group.database_path,
            "directory": group.directory
        }
        dataset = drivers.get_dataset(group.file_type, settings)
        datasets[group.label] = dataset
        datasets_by_pattern[group.pattern] = dataset
        label_to_pattern[group.label] = group.pattern

    # Lakes
    for figure in figures:
        add_feature(figure, data.LAKES, color="lightblue")

    features = []
    for figure in figures:
        render2 = add_feature(figure, data.LAKES, color="lightblue")
        features += [
            add_feature(figure, data.COASTLINES),
            add_feature(figure, data.BORDERS)]

    # Disputed borders
    for figure in figures:
        add_feature(figure, data.DISPUTED, color="red")


    for figure in figures:
        source1 = bokeh.models.ColumnDataSource(data.EMPTY)
        render2 =  figure.multi_line(
            xs="xs",
            ys="ys",
            source=source1,
            alpha=0.3,
            color="red", level="overlay")
        render21 = figure.circle(
                [],
                [],
            alpha=0.3,
            color="red", level="overlay")
        tool2 = bokeh.models.tools.PolyDrawTool(
                    renderers=[render2], 
                    vertex_renderer=render21,
                    )

        source_text_stamp = bokeh.models.ColumnDataSource(data.EMPTY)
        source_text_stamp.add([],"datasize")
        source_text_stamp.add([],"fontsize")
        source_text_stamp.add([],"colour")
        #render_text_stamp = figure.circle(x="xs",y="ys",legend_label="X", source=source);
        starting_font_size = 30 #in pixels 
        '''glyph = bokeh.models.Text(
                x="xs", 
                y="ys", 
                text=value("🌧"),  
                text_color="colour",
                text_font_size="fontsize")'''
        #glyph.text_font_size = '%spx' % starting_font_size

        source_barb = bokeh.models.ColumnDataSource(data.EMPTY)
        render_barb = figure.barb(
                x="xs", 
                y="ys", 
                u=0,
                v=70,
                source=source_barb
                )

        #render_text_stamp = figure.add_glyph(source_text_stamp, glyph)
        render_text_stamp = figure.text_stamp(
                x="xs", 
                y="ys", 
                source=source_text_stamp,
                text=value("🌧"),  
                text_color="colour",
                text_font_size="fontsize"
                )
                

        figure.y_range.js_on_change('start',
        bokeh.models.CustomJS(args=dict(render_text_stamp=render_text_stamp, glyph=render_text_stamp.glyph, figure=figure, starting_font_size=starting_font_size),code="""

            for(var g = 0; g < render_text_stamp.data_source.data['fontsize'].length; g++)
            {
                 render_text_stamp.data_source.data['colour'][g] = "olive";
                 if(starting_font_size  == render_text_stamp.data_source.data['datasize'][g])
                 {
                    //calculate initial datasize
                    var starting_font_proportion = starting_font_size/(figure.inner_height);
                    render_text_stamp.data_source.data['datasize'][g] = (starting_font_proportion * (figure.y_range.end - figure.y_range.start));
                 }
                 render_text_stamp.data_source.data['fontsize'][g] = (((render_text_stamp.data_source.data['datasize'][g])/ (figure.y_range.end - figure.y_range.start))*figure.inner_height) + 'px';
                 console.log(render_text_stamp.data_source.data['fontsize'][g]);
            }
            glyph.change.emit();
            """)
        )
        #render_text_stamp = bokeh.models.renderers.GlyphRenderer(data_source=ColumnDataSource(dict(x=x, y=y, text="X")), glyph=bokeh.models.Text(x="xs", y="ys", text="text", angle=0.3, text_color="fuchsia"))
        tool3 = bokeh.models.tools.PointDrawTool(
                    renderers=[render_text_stamp],
                    empty_value=starting_font_size,
                    )
        tool4 = bokeh.models.tools.PointDrawTool(
                    renderers=[render_barb],
                    custom_icon = 'forest/wind/barb.png'
                    )

        barc_tools = [tool2,tool3, tool4]
        #figure.tools = barc_tools
        figure.add_tools(*barc_tools)
        #barc_toolbar=bokeh.models.tools.Toolbar(tools=barc_tools,logo=None)
    toolBarBox = bokeh.models.tools.ToolbarBox(
        toolbar = figures[0].toolbar,
        toolbar_location = "above"
        )

    toggle = bokeh.models.CheckboxGroup(
            labels=["Coastlines"],
            active=[0],
            width=135)

    def on_change(attr, old, new):
        if len(new) == 1:
            for feature in features:
                feature.visible = True
        else:
            for feature in features:
                feature.visible = False

    toggle.on_change("active", on_change)

    dropdown = bokeh.models.Dropdown(
            label="Color",
            menu=[
                ("Black", "black"),
                ("White", "white")],
            width=50)
    autolabel(dropdown)

    def on_change(event):
        for feature in features:
            feature.glyph.line_color = new

    dropdown.on_click(on_change)

    layers_ui = layers.LayersUI()

    div = bokeh.models.Div(text="", width=10)
    border_row = bokeh.layouts.row(
        bokeh.layouts.column(toggle),
        bokeh.layouts.column(div),
        bokeh.layouts.column(dropdown))


    # Add optional sub-navigators
    sub_navigators = {
        key: dataset.navigator() for key, dataset in datasets_by_pattern.items()
        if hasattr(dataset, "navigator")
    }
    navigator = navigate.Navigator(sub_navigators)

    # Pre-select menu choices (if any)
    initial_state = {}
    for pattern, _ in sub_navigators.items():
        initial_state = db.initial_state(navigator, pattern=pattern)
        break

    middlewares = [
        keys.navigate,
        db.InverseCoordinate("pressure"),
        db.next_previous,
        db.Controls(navigator),  # TODO: Deprecate this middleware
        colors.palettes,
        colors.middleware(),
        presets.Middleware(presets.proxy_storage(config.presets_file)),
        presets.middleware,
        layers.middleware,
        navigator,
        mws.echo,
    ]
    store = redux.Store(
        forest.reducer,
        initial_state=initial_state,
        middlewares=middlewares)

    # Colorbar user interface
    colorbar_ui = forest.components.ColorbarUI()
    colorbar_ui.connect(store)

    # Add time user interface
    time_ui = forest.components.TimeUI()
    time_ui.connect(store)

    # Connect MapView orchestration to store
    opacity_slider = forest.layers.OpacitySlider()
    source_limits = colors.SourceLimits().connect(store)
    factory_class = forest.layers.factory(color_mapper,
                                          figures,
                                          source_limits,
                                          opacity_slider)
    gallery = forest.layers.Gallery.from_datasets(datasets, factory_class)
    gallery.connect(store)

    # Connect layers controls
    layers_ui.add_subscriber(store.dispatch)
    layers_ui.connect(store)

    # Connect tools controls

    display_names = {
            "time_series": "Display Time Series",
            "profile": "Display Profile"
        }
    available_features = {k: display_names[k]
                          for k in display_names.keys() if data.FEATURE_FLAGS[k]}

    tools_panel = tools.ToolsPanel(available_features)
    tools_panel.connect(store)
    if toolBarBox:
        tools_panel.layout.children.append(toolBarBox)

    # Navbar components
    navbar = Navbar(show_diagram_button=len(available_features) > 0)
    navbar.connect(store)

    # Connect tap listener
    tap_listener = screen.TapListener()
    tap_listener.connect(store)

    # Connect figure controls/views
    figure_ui = layers.FigureUI()
    figure_ui.add_subscriber(store.dispatch)
    figure_row.connect(store)

    # Tiling picker
    if config.use_web_map_tiles:
        tile_picker = forest.components.TilePicker()
        for figure in figures:
            tile_picker.add_figure(figure)
        tile_picker.connect(store)

    # Connect color palette controls
    colors.ColorMapperView(color_mapper).connect(store)
    color_palette = colors.ColorPalette().connect(store)

    # Connect limit controllers to store
    user_limits = colors.UserLimits().connect(store)

    # Preset
    preset_ui = presets.PresetUI().connect(store)

    # Connect navigation controls
    controls = db.ControlView()
    controls.connect(store)

    # Add support for a modal dialogue
    if data.FEATURE_FLAGS["multiple_colorbars"]:
        view = forest.components.modal.Tabbed()
    else:
        view = forest.components.modal.Default()
    modal = forest.components.Modal(view=view)
    modal.connect(store)

    # Set default time series visibility
    store.dispatch(tools.on_toggle_tool("time_series", False))

    # Set default profile visibility
    store.dispatch(tools.on_toggle_tool("profile", False))

    # Set top-level navigation
    store.dispatch(db.set_value("patterns", config.patterns))

    # Pre-select first map_view layer
    for label, dataset in datasets.items():
        pattern = label_to_pattern[label]
        for variable in navigator.variables(pattern):
            spec = {"label": label,
                    "dataset": label,
                    "variable": variable,
                    "active": [0]}
            store.dispatch(forest.layers.save_layer(0, spec))
            break
        break

    # Set variable dimensions (needed by modal dialogue)
    for label, dataset in datasets.items():
        pattern = label_to_pattern[label]
        values = navigator.variables(pattern)
        store.dispatch(dimension.set_variables(label, values))

    # Select web map tiling
    if config.use_web_map_tiles:
        store.dispatch(tiles.set_tile(tiles.STAMEN_TERRAIN))
        store.dispatch(tiles.set_label_visible(True))

    # Organise controls/settings
    layouts = {}
    layouts["controls"] = [
        bokeh.models.Div(text="Layout:"),
        figure_ui.layout,
        bokeh.models.Div(text="Navigate:"),
        controls.layout,
        bokeh.models.Div(text="Compare:"),
        layers_ui.layout
    ]
    layouts["settings"] = [
        border_row,
        opacity_slider.layout,
        preset_ui.layout,
        color_palette.layout,
        user_limits.layout,
        bokeh.models.Div(text="Tiles:"),
    ]
    if config.use_web_map_tiles:
        layouts["settings"].append(tile_picker.layout)

    tabs = bokeh.models.Tabs(tabs=[
        bokeh.models.Panel(
            child=bokeh.layouts.column(*layouts["controls"]),
            title="Control"
        ),
        bokeh.models.Panel(
            child=bokeh.layouts.column(*layouts["settings"]),
            title="Settings")
        ])

    tool_figures = {}
    if data.FEATURE_FLAGS["time_series"]:
        # Series sub-figure widget
        series_figure = bokeh.plotting.figure(
                    plot_width=400,
                    plot_height=200,
                    x_axis_type="datetime",
                    toolbar_location=None,
                    border_fill_alpha=0)
        series_figure.toolbar.logo = None

        series_view = series.SeriesView.from_groups(
                series_figure,
                config.file_groups)
        series_view.add_subscriber(store.dispatch)
        series_args = (rx.Stream()
                    .listen_to(store)
                    .map(series.select_args)
                    .filter(lambda x: x is not None)
                    .distinct())
        series_args.map(lambda a: series_view.render(*a))
        series_args.map(print)  # Note: map(print) creates None stream

        tool_figures["series_figure"] = series_figure

    if data.FEATURE_FLAGS["profile"]:
        # Profile sub-figure widget
        profile_figure = bokeh.plotting.figure(
                    plot_width=300,
                    plot_height=450,
                    toolbar_location=None,
                    border_fill_alpha=0)
        profile_figure.toolbar.logo = None
        profile_figure.y_range.flipped = True

        profile_view = profile.ProfileView.from_groups(
                profile_figure,
                config.file_groups)
        profile_view.add_subscriber(store.dispatch)
        profile_args = (rx.Stream()
                    .listen_to(store)
                    .map(profile.select_args)
                    .filter(lambda x: x is not None)
                    .distinct())
        profile_args.map(lambda a: profile_view.render(*a))
        profile_args.map(print)  # Note: map(print) creates None stream

        tool_figures["profile_figure"] = profile_figure

    tool_layout = tools.ToolLayout(**tool_figures)
    tool_layout.connect(store)

    for f in figures:
        f.on_event(bokeh.events.Tap, tap_listener.update_xy)
        marker = screen.MarkDraw(f).connect(store)

    control_root = bokeh.layouts.column(
            tabs,
            name="controls")


    # Add key press support
    key_press = keys.KeyPress()
    key_press.add_subscriber(store.dispatch)

    document = bokeh.plotting.curdoc()
    document.title = "FOREST"
    document.add_root(control_root)
    document.add_root(
        bokeh.layouts.column(
            tools_panel.layout,
            tool_layout.layout,
            width=400,
            name="series"))
    document.add_root(
        bokeh.layouts.row(time_ui.layout, name="time"))
    for root in navbar.roots:
        document.add_root(root)
    document.add_root(colorbar_ui.layout)
    document.add_root(figure_row.layout)
    document.add_root(key_press.hidden_button)
    document.add_root(modal.layout)


class Navbar:
    """Collection of navbar components"""
    def __init__(self, show_diagram_button=True):
        self.headline = forest.components.Headline()
        self.headline.layout.name = "headline"

        self.buttons = {}
        # Add button to control left drawer
        key = "sidenav_button"
        self.buttons[key] = bokeh.models.Button(
            label="Settings",
            name=key)
        custom_js = bokeh.models.CustomJS(code="""
            openId("sidenav");
        """)
        self.buttons[key].js_on_click(custom_js)

        # Add button to control right drawer
        key = "diagrams_button"
        self.buttons[key] = bokeh.models.Button(
            label="Diagrams",
            css_classes=["float-right"],
            name=key)
        custom_js = bokeh.models.CustomJS(code="""
            openId("diagrams");
        """)
        self.buttons[key].js_on_click(custom_js)

        roots = [
            self.buttons["sidenav_button"],
            self.headline.layout,
        ]
        if show_diagram_button:
            roots.append(self.buttons["diagrams_button"])
        self.roots = roots

    def connect(self, store):
        self.headline.connect(store)


def any_none(obj, attrs):
    return any([getattr(obj, x) is None for x in attrs])


def add_feature(figure, data, color="black"):
    source = bokeh.models.ColumnDataSource(data)
    return figure.multi_line(
        xs="xs",
        ys="ys",
        source=source,
        color=color)


if __name__.startswith("bokeh"):
    main()
