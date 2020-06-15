# Changes to Forrest Code 
## Dan Ellis 

### Issues
As I can’t add issues to your branch, it is worth noting that the barc configuration requires for forest and the config file to be run within the forest repository (e.g. for finding the wind barb png file). It may be worth linking these with the library path e.g. `__file__` rather than directly. (edited) 





### Notes 
- Bokeh can only update free draw arrays in server mode (app) and not within normal usage - this makes testing difficult

- Any files required by app need to be in the `forest/static` folder

- app referenced files are already read from `localhost/forest/static`, and therefore do not need this extension. Just add the file as `.static` is your root directory

- for element styling, use `static/style.css`

- elements do not have ids in bokeh. You therefore need to assign them a *class* often using the `css_classes` argument. Even after doing this, elements are often nested within several divs which contain them. Use your web browser to explore them. your css will likely be along the lines of `div.<classname> div <elementtype>`

- JS code that is run on loading of forest can be found in `static/style.css`. This is your only chance at using vanilla js without the need of callbacks. 

- all other js code can be applied as part of a bokeh callback function.

```
callback = bokeh.models.CustomJS(code="""
     do something;
 """)
 
 var.js_on_event('load|click|mouseover etc.', callback)
 
 ```
 
 - bokeh uses websockets to communicate, and therefore data needs to be serialisable (although all text already is)
 
 - also forest's bokeh uses node to create the server, so node packages are a possiblility, although I have not looked at this in too much detail. 
 
 
 
 
 
 ### Changes to Forest Code
 
 #### 1. Barc Logo
 - image added to `static`
 - `main.py` edited to remove label and add `barc_btn` class. 
 - `static/style.css` edited to add relevant styling for button and parent classes. 
 