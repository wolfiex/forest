import bokeh.models
from bokeh.models import ColumnDataSource
from bokeh.core.properties import value
from bokeh.models.tools import PolyDrawTool, PointDrawTool, ToolbarBox
from forest import wind, data

class BARC:
    def __init__(self, figure):
        self.figure = figure
        self.polyLine()


    def polyLine(self):
        source1 = ColumnDataSource(data.EMPTY)
        render_line =  self.figure.multi_line(
            xs="xs",
            ys="ys",
            source=source1,
            alpha=0.3,
            color="red", level="overlay")
        render_line1 = self.figure.circle(
                [],
                [],
            alpha=0.3,
            color="red", level="overlay")
        tool2 = PolyDrawTool(
                    renderers=[render_line], 
                    vertex_renderer=render_line1,
                    )

        source_text_stamp = ColumnDataSource(data.EMPTY)
        source_text_stamp.add([],"datasize")
        source_text_stamp.add([],"fontsize")
        source_text_stamp.add([],"colour")
        #render_text_stamp = self.figure.circle(x="xs",y="ys",legend_label="X", source=source);
        starting_font_size = 30 #in pixels 
        starting_colour = "orange" #in CSS-type spec 
        '''glyph = bokeh.models.Text(
                x="xs", 
                y="ys", 
                text=value("🌧"),  
                text_color="colour",
                text_font_size="fontsize")'''
        #glyph.text_font_size = '%spx' % starting_font_size

        source_barb = ColumnDataSource(data.EMPTY)
        render_barb = self.figure.barb(
                x="xs", 
                y="ys", 
                u=-50,
                v=-50,
                source=source_barb
                )

        #render_text_stamp = self.figure.add_glyph(source_text_stamp, glyph)
        render_text_stamp = self.figure.text_stamp(
                x="xs", 
                y="ys", 
                source=source_text_stamp,
                text=value("🌧"),  
                text_color="colour",
                text_font_size="fontsize"
                )
                
        source_text_stamp.js_on_change('data', 
            bokeh.models.CustomJS(args=dict(datasource = render_text_stamp.data_source, starting_font_size=starting_font_size, figure=self.figure, starting_colour=starting_colour), code="""
                for(var g = 0; g < datasource.data['fontsize'].length; g++)
                {
                    if(!datasource.data['colour'][g])
                    {
                        datasource.data['colour'][g] = starting_colour;
                    }

                    if(!datasource.data['fontsize'][g])
                    {
                        datasource.data['fontsize'][g] = starting_font_size +'px';
                    }

                    //calculate initial datasize
                    if(!datasource.data['datasize'][g])
                    {
                        var starting_font_proportion = starting_font_size/(figure.inner_height);
                        datasource.data['datasize'][g] = (starting_font_proportion * (figure.y_range.end - figure.y_range.start));
                    }
                }
                """)
        )
        self.figure.y_range.js_on_change('start',
            bokeh.models.CustomJS(args=dict(render_text_stamp=render_text_stamp, glyph=render_text_stamp.glyph, figure=self.figure, starting_font_size=starting_font_size),code="""

            for(var g = 0; g < render_text_stamp.data_source.data['fontsize'].length; g++)
            {
                 render_text_stamp.data_source.data['fontsize'][g] = (((render_text_stamp.data_source.data['datasize'][g])/ (figure.y_range.end - figure.y_range.start))*figure.inner_height) + 'px';
            }
            glyph.change.emit();
            """)
        )
        #render_text_stamp = bokeh.models.renderers.GlyphRenderer(data_source=ColumnDataSource(dict(x=x, y=y, text="X")), glyph=bokeh.models.Text(x="xs", y="ys", text="text", angle=0.3, text_color="fuchsia"))
        tool3 = PointDrawTool(
                    renderers=[render_text_stamp],
                    )
        tool4 = PointDrawTool(
                    renderers=[render_barb],
                    custom_icon = 'forest/wind/barb.png'
                    )

        barc_tools = [tool2,tool3, tool4]
        #self.figure.tools = barc_tools
        self.figure.add_tools(*barc_tools)
    
    def ToolBar(self):
        toolBarBox = ToolbarBox(
            toolbar = self.figure.toolbar,
            toolbar_location = "above"
        )
        return toolBarBox
