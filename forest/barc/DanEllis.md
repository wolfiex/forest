# Changes to Forrest Code 
## Dan Ellis 

### Issues

### TODO
- bart reads all possible plots. Often only one is displayed. 
It is worth reading the number displayed from FigureUI(Observable) in `layers.py` and only showing that many toolbars.



### Notes 
- Run command: `forest --dev --config-file nwcsaftest.yml --show; pkill -9 python
`
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
 
#### 0. Pull request into Forest #319
https://github.com/MetOffice/forest/pull/319

A local server self-termination switch for exiting python on closure of browser window and freeing up the port. 
Correspondance and changes shown in the pull request thread and commits. 
 
#### 1. Barc Logo
 - image added to `static`
 - `main.py` edited to remove label and add `barc_btn` class. 
 - `static/style.css` edited to add relevant styling for button and parent classes. 
 
#### 2 SideBar styling and width 
 - `main.py` callback for width styling
 - `static/style.css` for colour 
 
#### 3. Remove location sensetive references. 
The barc configuration required for forest and the config file to be run within the forest repository (e.g. for finding the wind barb png file). This has been fixed by reading the absolute location of the library and using that to reference the images. 

- barc/toolbar.py line 119:

 `wind.__file__.replace('__init__.py','barb.png')`
 
#### 4. Toolabar labels  - see TODO
Added descriptors for each barc toolbar and styling. 'Paragraph' `<p>`  elements at the end of barc/toolbar.py.

#### 5. 

