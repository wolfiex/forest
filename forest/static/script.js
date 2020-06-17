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
get_figures();

var frontClass = {
    warm: "WW",
    cold: "CC",
    convoluted: "WC"
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
    [
        ...document.querySelectorAll('div[class="bk bk-toolbar bk-below"]')
    ].forEach((d, i) => {
        d.style.visibility = i < document.n ? "visible" : "hidden";
    });

    // add svg elements to all canvas grids
    document.svgs = document.canvases.map((d, i) => {
        var parent = d.parentElement.parentElement;
        var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", parent.style.width);
        svg.setAttribute("height", parent.style.height);
        svg.style["background-color"] = "red";
        try {
            parent.querySelector("svg").remove();
        } catch (e) {}
        parent.appendChild(svg);
        return svg;
    });

    // load libraries
    var scriptTag = document.createElement("script");
    scriptTag.src = "/forest/static/d3.min.js";
    document.body.appendChild(scriptTag);
}



function draw_front(x, y, id, class, svg_n) {
    // the function used for drawing weather fronts
    svg = d3.select(document.svgs[svg_n]);
    var line = d3.line().curve(d3.curveBasis);
    
    var textPath = svg
        .append("defs")
        .append("path")
        .attr("id", "textPath" + id);


    var text4path = svg
        .append("text")
        .append("textPath")
        .attr("xlink:href", "#textPath" + id);
    
    text4path.attr('class',checked)
    text4path.text(frontClass[checked].repeat(100))
    textPath.attr("d", line);
}
