'''
Data for Weather Front drawing on BARC  

'''
from bokeh.models import ColumnDataSource, CustomJS , Paragraph
from bokeh.models.tools import FreehandDrawTool
from forest import data

def mecator_2_percent(posn):
    ''' 
    Convert between EPSG:3857 WGS 84 / Pseudo-Mercator to a percentage of the lon lat map -180 to 180 and -90 to 90 map
    
    x = lon
    y = lat
    '''
    
    
    mlon = 20037508.34
    mlat = 31296372.44
    
    x = (np.array(posn['xs']) + mlon) / mlon
    y = (np.array(posn['ys']) + mlon) / mlon
    
    return [[x[i],y[i]] for i in range(len(x))]
    
def test(self,figure):
            return   Paragraph(
                    text="""eeeeee""",
                    width=200, height=18,
                    css_classes=['barc_p']
                    )




def callback(cdata,figure):
    
    
    #pts = mecator_2_percent(data)
    
    
    

    js = CustomJS(args=dict(datasource = cdata, figure=figure),
    code="""

        console.log(document.querySelectorAll('canvas'))
        console.log(datasource.data);


    """)


    return js
    
    
def front(self, figure, which:str):
        '''
        Freehand drawtool for weather fronts
        
        Arguments:
            Figure - bokeh figure
            Which:str - type of front
            
        Documentation of FreehandDrawTool
                
            Draw patch/multi-line
            Click and drag to start drawing and release the mouse button to finish drawing

            Delete patch/multi-line
            Tap a line or patch to select it then press BACKSPACE key while the mouse is within the plot area.

            To Delete multiple patches/lines at once:
            Delete selection
            Select patches/lines with SHIFT+tap (or another selection tool) then press BACKSPACE while the mouse is within the plot area.

        '''
        
        colours = {'warm':'red','cold':'blue','convoluted':'purple'}
        
        setattr(self, 'source_'+which , ColumnDataSource(data.EMPTY) )
        
        line =  figure.multi_line(
            xs="xs",
            ys="ys",
            source=getattr(self , 'source_'+which ),
            alpha=0.3,
            color=colours[which], level="overlay")
            
        drawfront = FreehandDrawTool(renderers=[line],custom_icon=__file__.replace('front.py','icons/barclogo.png'))
                    
        getattr(self , 'source_'+which ).js_on_change('data', callback(line.data_source,figure) )
        
        # def line_change (attr,old,new):
        #     print('\n\n\n', self.source_polyline.data,attr,old,new)
        # self.source_polyline.on_change('data',line_change)
        
        
        
        
        return drawfront