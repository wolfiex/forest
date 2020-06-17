import bokeh.models
from bokeh.models import ColumnDataSource, Paragraph
from bokeh.models.glyphs import Text
from bokeh.core.properties import value
from bokeh.models.tools import PolyDrawTool, PointDrawTool, ToolbarBox,FreehandDrawTool
from forest import wind, data
from . import front

class BARC:
    ''' A class for the BARC features - more documentation needed. ''' 
    
    def __init__(self, figures):
        self.figures = figures
        ''' For each figure supplied (if multiple) ''' 
        print( '\n\n\n',figures)
        for figure in self.figures:
            barc_tools = [
                self.polyLine(figure),
                self.textStamp(figure),
                self.windBarb(figure)
                ]
            #self.figure.tools = barc_tools
            figure.add_tools(*barc_tools)
            

            
    


    def polyLine(self, figure):
        ''' Freehand Tool '''
        self.source_polyline = ColumnDataSource(data.EMPTY)
        render_line =  figure.multi_line(
            xs="xs",
            ys="ys",
            source=self.source_polyline,
            alpha=0.5,
            color="red", level="overlay")
        text = Text(x="xs", y="ys", text=value("abc"), text_color="red", text_font_size="12pt")
        render_line1 = figure.add_glyph(self.source_polyline,text)
        tool2 = FreehandDrawTool(
                    renderers=[render_line], 
                    )
        self.source_polyline.js_on_change('data', 
            bokeh.models.CustomJS(args=dict(datasource = render_line.data_source, starting_font_size="30px", figure=figure, starting_colour="red", text=Text()), code="""
            console.log(datasource.data);
                """)
        )
        # 
        # def line_change (attr,old,new):
        #     print('\n\n\n', self.source_polyline.data,attr,old,new)
        # 
        # self.source_polyline.on_change('data',line_change)
        
        return tool2



    def textStamp(self, figure):
        self.source_text_stamp = ColumnDataSource(data.EMPTY)
        self.source_text_stamp.add([],"datasize")
        self.source_text_stamp.add([],"fontsize")
        self.source_text_stamp.add([],"colour")
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

        #render_text_stamp = self.figure.add_glyph(self.source_text_stamp, glyph)
        render_text_stamp = figure.text_stamp(
                x="xs", 
                y="ys", 
                source=self.source_text_stamp,
                text=value("🌧"),  
                text_color="colour",
                text_font_size="fontsize"
                )
                
        self.source_text_stamp.js_on_change('data', 
            bokeh.models.CustomJS(args=dict(datasource = render_text_stamp.data_source, starting_font_size=starting_font_size, figure=figure, starting_colour=starting_colour), code="""
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
        figure.y_range.js_on_change('start',
            bokeh.models.CustomJS(args=dict(render_text_stamp=render_text_stamp, glyph=render_text_stamp.glyph, figure=figure, starting_font_size=starting_font_size),code="""

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
        return tool3

    def windBarb(self, figure):
        self.source_barb = ColumnDataSource(data.EMPTY)
        render_barb = figure.barb(
                x="xs", 
                y="ys", 
                u=-50,
                v=-50,
                source=self.source_barb
                )

        tool4 = PointDrawTool(
                    renderers=[render_barb],
                    custom_icon = wind.__file__.replace('__init__.py','barb.png')
                    )
                    
        return tool4

    def weatherFront(self,figure,i:int):
        ''' 
        The weatherfront function of barc

        Arguments:
            Figure - bokeh figure 
            i (int) - figure index / order
        
        Returns:
            List of custom toolbar elements
        '''
        
        # function to update plot ranges in js
        figure.x_range.js_on_change('start', front.range_change(figure,0)) 
        
        # add draw items to toolbar
        toolbars = []
        for front_type in 'warm cold convoluted'.split():
            toolbars.append( front.front(self,figure,front_type) )
        
        return toolbars

#####################################


    def ToolBar(self):
        toolBarBoxes = []
        for i, figure in enumerate(self.figures):
                
            ### label toolbars
            toolBarBoxes.append(
                Paragraph(
                text="""Toolbar: Figure %d"""%(i+1),
                width=200, height=18,
                css_classes=['barc_p']
                )
            )

            figure.add_tools(*self.weatherFront(figure,i))

            toolBarBoxes.append(
                 ToolbarBox(
                     toolbar = figure.toolbar,
                     toolbar_location = "below"
                 )
            )
            
            
            
            
            
            
        return toolBarBoxes
