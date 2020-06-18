// sidebar functions
let openId = function(id) {
    document.getElementById(id).style.width = "400px";
};
let closeId = function(id) {
    document.getElementById(id).style.width = "0";
};

//globals
document.bbox = []; // storage for figure ranges
document.fronts = []; // storage for weather fronts
document.n = 1; // number of figures
document.maxfig = 3;// update this manually if forrest allows more plots for comparison
get_figures();

var frontClass = {
    warm: "WW",
    cold: "CC",
    occluded: "WC",
    stationary: "Wc"
    
};

// functions

function get_figures() {
    // saves the figure locations in global set_variables
    document.canvases = [
        ...document.querySelectorAll('div[class="bk-root"] canvas')
    ];
    document.canvases = document.canvases
        .filter(function(_, index) {
            return index % 2 === 0;
        })
        .slice(0, document.n);

    // hide irrelevant menus
    try{ hide_menus() }catch (e){
        setTimeout(hide_menus, 2000);
    }

    
    console.log(document.n, 'figures')
    

    // add svg elements to all canvas grids
    document.svgs = document.canvases.map((d, i) => {
        
        var parent = d.parentElement;
        var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", parent.style.width);
        svg.setAttribute("height", parent.style.height);
        svg.setAttribute("transform", "scale(1,-1)")
        
        /// preserveAspectRatio="xMidYMid meet"
        
        try {
            parent.querySelector("svg").remove();
        } catch (e) {}
        parent.appendChild(svg);
        return svg;
    });



    // load libraries
    try{ get_d3() }catch (e){
        setTimeout(get_d3, 2000);
    }
}

function resize_svg( svg_n ){
    var svg = d3.select(document.svgs[svg_n]);
    var bounds = document.bbox[svg_n]
    
    if (bounds){
    
    w = Math.abs(bounds.x1 - bounds.x0)
    h = Math.abs(bounds.y1 - bounds.y0)
    
    svg.attr('viewBox',`${bounds.x0} ${bounds.y0} ${w} ${h}`)
    
    }
}


function draw_front(type, svg_n) {
    // the function used for drawing weather fronts
    // Font Available at https://github.com/cemac/WeatherFront
    // contact Dan Ellis (github: wolfiex) for support
    var svg = d3.select(document.svgs[svg_n]);
    resize_svg(svg_n)
    
    var line = d3.line().curve(d3.curveBasis);
    
    id = document.fronts[type].xs.length
    
    coords = document.fronts[type].xs[id-1].map(function(d,i){
        return [d,document.fronts[type].ys[id-1][i]]
    })
    
    var textPath = svg
        .append("defs")
        .append("path")
        .attr('class',type)
        //.style('stroke-width','20px!important')
        .attr("id", "textPath" + id)
        .attr("d", line(coords));;


    var text4path = svg
        .append("text")
        .append("textPath")
        .attr("id", "text4path" + id)
        .attr('class',type)
        .style('font-size','12em!important')
        .attr("xlink:href", "#textPath" + id)
        .text(frontClass[type].repeat(100));
        
        
    // var path = svg
    //     .append("path")
    //     .attr("id", "Path" + id)
    //     .attr('fill','none')
    //     .attr('class',type)
    //     .style('stroke-width','20px!important')
    //     .style('stroke','black');
    // 


    // path.attr("d", line(coords));
    
    console.log(coords,textPath.node(),text4path.node())
}




/// get functions ///
function get_d3(){
    if (typeof d3 == 'undefined') {
        var scriptTag = document.createElement("script");
        scriptTag.src = "/forest/static/d3.min.js";
        document.body.appendChild(scriptTag);
        console.log('d3.js loaded')
    }
}


function hide_menus(){
    // [...document.querySelectorAll('div[class="bk bk-toolbar bk-below"]')
    // ].forEach((d, i) => {
    //     d.style.visibility = 'hidden' //i < document.n ? "visible" : "hidden";
    // });

    for (var i = document.maxfig; i >= 0 ; i--) {
      [...document.querySelectorAll('.barc_g'+i)].forEach(function(d){
          d.style.visibility = i < document.n ? "visible" : "hidden";
          console.log(i,d)
      })
      
    }
}
