(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
  typeof define === 'function' && define.amd ? define(factory) :
  (global = global || self, global.Chart = factory());
}(this, function () { 'use strict';
var version="0.1";
const COLORMAP = [
[0x46/255,0x61/255,0xEE/255,1],
[0xEC/255,0x56/255,0x57/255,1],
[0xB0/255,0x8B/255,0xEB/255,1],
[0x8F/255,0xAA/255,0xBB/255,1],
[0x3E/255,0xA0/255,0xDD/255,1],
[0xF5/255,0xA5/255,0x2A/255,1],
[0x23/255,0xBF/255,0xAA/255,1],
[0xFA/255,0xA5/255,0x86/255,1],
[0xEB/255,0x8C/255,0xC6/255,1],
[0x00/255,0x00/255,0x00/255,1],
[0xFF/255,0x00/255,0x00/255,1],
[0x60/255,0x3C/255,0x28/255,1],
[0x00/255,0x00/255,0xFF/255,1],
[0x00/255,0xFF/255,0x00/255,1],
[0xCC/255,0x00/255,0x66/255,1],
[0xFF/255,0x00/255,0xFF/255,1],
[0x00/255,0xFF/255,0xFF/255,1],
[0x52/255,0x52/255,0x52/255,1],
[0xC0/255,0xC0/255,0x00/255,1],
[0x1D/255,0xA8/255,0x1A/255,1],
];
function colorArrayToRGB(colorArray) {
  const r = Math.round(colorArray[0] * 255);
  const g = Math.round(colorArray[1] * 255);
  const b = Math.round(colorArray[2] * 255);
  const a = colorArray[3];
  return a !== undefined ? `rgba(${r}, ${g}, ${b}, ${a})` : `rgb(${r}, ${g}, ${b})`;
}
function colorArrayToHexa(colorArray) {
  return '#' + colorArray
    .map(v => (v*255).toString(16).padStart(2, '0'))
    .join('');
}

var default_options = {
  class:{
    svg:"chart-extend",
    chart:"chart",
    xAxis:"x axis grid",
    yAxis:"y axis grid"
  },
  maxLines: 50,
  margin:{
    top: 10,
    right: 20,
    bottom: 10,
    left: 40
  },
  colorIndex: 0
  // margin:{
  //   top: 10,
  //   right: 20,
  //   bottom: 60,
  //   left: 40},    
};

var ru_RU = {
    "decimal": ",",
    "thousands": "\xa0",
    "grouping": [3],
    "currency": ["", " руб."],
    "dateTime": "%A, %e %B %Y г. %X",
    "date": "%d.%m.%Y",
    "time": "%H:%M:%S",
    "periods": ["AM", "PM"],
    "days": ["воскресенье", "понедельник", "вторник", "среда", "четверг", "пятница", "суббота"],
    "shortDays": ["вс", "пн", "вт", "ср", "чт", "пт", "сб"],
    "months": ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
    "shortMonths": ["Янв","Фев","Март","Апр","Май","Июн","Июл","Авг","Сен","Окт","Нбр","Дек"]
}
var RU = d3.locale(ru_RU);
/*
** Формат времени для оси Х
*/
var customTimeFormat =
RU.timeFormat.multi([
  [".%L", function(d) { return d.getMilliseconds(); }],
  ["%H:%M:%S", function(d) { return d.getSeconds(); }],
  ["%H:%M", function(d) { return d.getMinutes(); }],
  ["%H:%M", function(d) { return d.getHours(); }],
  ["%d/%m", function(d) { return d.getDay() && d.getDate() != 1; }],
  ["%d/%m", function(d) { return d.getDate() != 1; }],
  ["%B", function(d) { return d.getMonth(); }],
  ["%Y", function() { return true; }]
]);

function extend() {
  /*
  ** Функция для объединения объектов
  */
  arguments[0] = arguments[0] || {};
  for (var i = 1; i < arguments.length; i++)
  {
    for (var key in arguments[i])
    {
      if (arguments[i].hasOwnProperty(key))
      {
        if (typeof(arguments[i][key]) === 'object') {
          if ((arguments[i][key] instanceof Array)||(arguments[i][key].nodeType===1)) {
            arguments[0][key] = arguments[i][key];
          } else {
            arguments[0][key] = extend(arguments[0][key], arguments[i][key]);
          }
        } else {
          arguments[0][key] = arguments[i][key];
        }
      }
    }
  }
  return arguments[0];
}

function strtodate(str){
  /*
  ** Функция перевода строки в дату. Формат строки YYYY-MM-DD HH:mm:ss
  */
  return new Date(
    str.substr(0,4),
    str.substr(5,2)-1,
    str.substr(8,2),
    str.substr(11,2),
    str.substr(14,2),
    str.substr(17,2));
};

function requestFullScreen(element) {
  /*
  ** Функция для перехода в полный экран
  */
  if (document.webkitIsFullScreen) {
    document.webkitCancelFullScreen();
    return;
  }
    var requestMethod = element.requestFullScreen || element.webkitRequestFullScreen || element.mozRequestFullScreen || element.msRequestFullscreen;
    if (requestMethod) {
        requestMethod.call(element);
    } else if (typeof window.ActiveXObject !== "undefined") { // Older IE.
        var wscript = new ActiveXObject("WScript.Shell");
        if (wscript !== null) {
            wscript.SendKeys("{F11}");
        }
    }
};


function Chart(options,data){
  var $$ = this;
  $$.options = extend({},default_options,options);
  var o = $$.options,
    rect  =o.element.getBoundingClientRect();
  
  rect.height -=5;
  var  width = rect.width - o.margin.left - o.margin.right,
    height = rect.height - o.margin.top - o.margin.bottom;
  $$.canvas = d3.select(o.element).append('canvas').attr({
      "class":o.class.chart,
      "width": width,
      "height": height,
      "style":"transform:translate("+o.margin.left+"px,"+o.margin.top+"px);position:absolute"
  }).node();
  $$.canvas.width = width;
  $$.canvas.height = height;
  $$.gl = $$.canvas.getContext("webgl",{antialias: true, preserveDrawingBuffer: true},); //preserveDrawingBuffer=true для скриншота!
  $$.programInfo = twgl.createProgramInfo($$.gl, ["vs", "fs"]);  
  if (data!==undefined) {
    $$.init(data);
    $$._init = true
  } else {
    $$._init = false
  }
}

var initialDomain;  
Chart.prototype.init = function(data) {
  var $$ = this;
  var o = $$.options,
    rect  =o.element.getBoundingClientRect();
  rect.height -=5;
  var  width = rect.width - o.margin.left - o.margin.right,
    height = rect.height - o.margin.top - o.margin.bottom;
  $$.lines = [];
  $$.d3 = {};
  $$.initialDomain = data.domain;
  initialDomain=$$.initialDomain;
  // if ($$.initialDomain == null) {
  //   initialDomain=data.domain;
  //   $$.initialDomain = data.domain;
  // } else $$.initialDomain = initialDomain;  
  
  $$.uniforms = {
          u_resolution: [$$.initialDomain.x[1]-$$.initialDomain.x[0], $$.initialDomain.y[1]-$$.initialDomain.y[0]],
          u_translation: [0,$$.initialDomain.y[0]],
        };

  $$.d3.x=d3.time.scale()
    .range([0, width])
    .domain(data.domain.x);
  $$.d3.y=d3.scale.linear()
    .range([height,0])
    .domain(data.domain.y);
  $$.d3.zoom_x = d3.behavior.zoom()
    //.scaleExtent([0.2,10000])
    .x($$.d3.x)
    .on("zoom", function(){onzoom($$,"x");});
  $$.d3.zoom_y = d3.behavior.zoom()
    .y($$.d3.y)
    .on("zoom", function(){onzoom($$,"y");})
  $$.d3.xAxis=d3.svg.axis()
    .scale($$.d3.x)
    .innerTickSize(-height)
      .outerTickSize(-height)
    //.ticks(innerWidth<1000?4:10)
    .tickFormat(customTimeFormat);;
  $$.d3.yAxis=d3.svg.axis()
    .scale($$.d3.y)
    .innerTickSize(-width)
      .outerTickSize(-width)
    .orient("left");
  $$.d3.svg = d3.select(o.element).append("svg").attr({
      "class":o.class.svg,
      "width": rect.width,
      "height": rect.height,
      "viewBox":"0 0 "+rect.width+" "+rect.height
    });
  $$.d3.chartGroup = $$.d3.svg.append("g")
    .attr("transform","translate("+o.margin.left+","+o.margin.top+")");

  $$.tooltip = new Tooltip(o.element);
  $$.tooltip.cursor = $$.d3.chartGroup.append("line").attr({
    "y2":height,
    "transform":"translate(-"+o.margin.left+",0)",
    "class":"cursor"
  });
  $$.d3.chartGroup.append("g")
    .attr({
      "class": o.class.xAxis,
      "transform":"translate(0," + height + ")" 
    })
    .call($$.d3.xAxis)
    .append("rect")
    .attr({
      "class":"event-rect",
      "width":width,
      "height":o.margin.bottom,
      "data-for":"x",
      "zoom":"x",
    }).call($$.d3.zoom_x);
  $$.d3.chartGroup.append("g")
    .attr("class", o.class.yAxis)
    .call($$.d3.yAxis);
  $$.d3.chartGroup.append("rect").attr({
    "class":"event-rect",
    "width":width,
    "height":height,
    "data-for":"xy",
    "zoom":"x",
    }).call($$.d3.zoom_x)
    .on("mousemove",function(){
      mousemove($$);
    })
    .on("mouseenter",function(){
      $$.tooltip.div.style("display","block");
    })
    .on("mouseleave",function(){
      $$.tooltip.div.style("display","none");
    });  
  $$.d3.svg.append("rect").attr({
    "width":o.margin.left,
    "height":height,
    "class":"event-rect y",
    "data-for":"y",
    "y":o.margin.top,
    "zoom":"y",
    }).call($$.d3.zoom_y);

  
  $$.legend = d3.select(o.element).append("ul")
      .attr("class","legend")
      .on("click",function(evt){
        var li = d3.event.target;
        var id = li.getAttribute("data-id");
        for (var i = 0; i < $$.lines.length; i++) {
          if ($$.lines[i].id.toString()==id) {
            $$.lines[i].disabled=!$$.lines[i].disabled;
            break;
          }
        }
        li.classList.toggle("unchecked");
        $$.render();
        return;
      }).on("contextmenu",function(evt){
        var e =d3.event;
        e.preventDefault();
        contextmenu_close();
        contextmenu_legend.target = e.target;
        contextmenu_show(contextmenu_legend);
        // d3.event.preventDefault();
        // var li = d3.event.target;
        // $$.deleteLine(li.outerText)
        // $$.render();
      });
  $$.d3.svg.on("contextmenu",()=>{
    var e =d3.event;
    e.preventDefault();
    contextmenu_close();
    contextmenu_chart.target = e.target;
    contextmenu_show(contextmenu_chart);
  })
};

Chart.prototype.load = function(d){
  var $$ = this;

  var data = parse(d,$$);
  if (!$$._init){
    $$.init(data);
    $$._init = true;
  }
  if ($$.lines.length>$$.options.maxLines) {
    const err = new Error(`Построено больше ${$$.options.maxLines} линий на одном графике`)
    err.name = "TooManyLinesError"
    throw err
  }
  $$.lines.push(data);
  if (data.type=="lines"){
    $$.legend.append("li")
      .attr({
        "data-id":data.id,
        "title":d.tooltip
      }).style({
        "color":colorArrayToRGB(data.color)
      })
      .text(data.title);
  } else if (data.type=="discrete"){
    $$.legend.append("li")
      .attr({
        "data-id":data.id,
        "title":d.tooltip
      }).style({
        "color":colorArrayToRGB(data.color)
      }).text(data.title);      
  }
  $$.updateViewPort();
};

Chart.prototype.deleteLine = function (title){
  var $$ = this;
  var item_to_remove = undefined;
  for (var i=0;i<$$.lines.length;i++)
    if ($$.lines[i].title == title) {
      item_to_remove = i
      break
    }
  if (item_to_remove!=undefined) {
    var i = item_to_remove;
    var id = $$.lines[i].id
    d3.selectAll('[data-id="'+id+'"]').remove()
    $$.lines.splice(i,1)
    //$$.d3.lines.select('[data-id="'+id+'"]').remove()
    //$$.legend.select('[data-id="'+id+'"]').remove()
  }
}

Chart.prototype.destroy = function(){
  this.options.element.innerHTML = "";
}

Chart.prototype.updateViewPort = function(){
  var $$ = this;
  var a=[];
  var discreteIndex = 0;
  $$.lines.forEach(function(line){
    if (line.type=="discrete"){
      a.push(-2*discreteIndex+1);
      discreteIndex++;
      return;
    }
    a.push(line.domain.y[0]);
    a.push(line.domain.y[1]);
  });
  if (a.length==1) a.push(a[0]==0?1:0)
  var extent = d3.extent(a);
  if (extent[0]!=extent[1]){
    var h = (extent[1]-extent[0])*0.1;
    extent[1]+=h;
    extent[0]-=h;
  }
  $$.d3.zoom_y.y($$.d3.y.domain(extent));
  $$.d3.svg.select(".y.axis").call($$.d3.yAxis);
  $$.uniforms.u_resolution[1] = extent[1]-extent[0];
  $$.uniforms.u_translation[1] = extent[0];
  $$.render();
}

Chart.prototype.render = function(){
  var $$ = this;
  //console.trace(); //Для отладки вызовов
  twgl.resizeCanvasToDisplaySize($$.gl.canvas);
  $$.gl.viewport(0, 0, $$.gl.canvas.width, $$.gl.canvas.height);
  $$.gl.clearColor(0,0,0, 0);
  $$.gl.clear($$.gl.COLOR_BUFFER_BIT);
  $$.gl.useProgram($$.programInfo.program);
  var discreteIndex=0;
  $$.lines.forEach((l,i)=>{
    if (l.disabled){
      return
    }
    if (l.type=="lines"){
      $$.uniforms.u_color=l.color;
      twgl.setUniforms($$.programInfo, $$.uniforms);
      twgl.setBuffersAndAttributes($$.gl, $$.programInfo, l.bufferInfo);
      twgl.drawBufferInfo($$.gl, l.bufferInfo, $$.gl.LINE_STRIP);
    } else if (l.type=="discrete"){
      $$.uniforms.u_color=l.color;
      $$.uniforms.u_translation[1]+=discreteIndex*2; //Смещаем дискрет, не смотим на ось. Ось для линий.
      twgl.setUniforms($$.programInfo, $$.uniforms);
      twgl.setBuffersAndAttributes($$.gl, $$.programInfo, l.bufferInfo);
      twgl.drawBufferInfo($$.gl, l.bufferInfo, $$.gl.LINE_STRIP,2);
      twgl.drawBufferInfo($$.gl, l.bufferInfo, $$.gl.TRIANGLES,l.bufferInfo.numElements-2,2);
      $$.uniforms.u_translation[1]-=discreteIndex*2; //Возвращаем обратно
      discreteIndex++;
    }
  });
  
}

Chart.prototype.onresize = function(){
  const $$ = this;
  if (!$$.hasOwnProperty('d3')) return;
  const o = $$.options,
    rect  =o.element.getBoundingClientRect();

  rect.height -=5;
  var width = rect.width - o.margin.left - o.margin.right,
    height = rect.height - o.margin.top - o.margin.bottom;
  var x =  $$.d3.x.range([0, width]),
  y = $$.d3.y.range([height,0]);
  $$.d3.svg.attr("width", rect.width)
    .attr("height", rect.height)
    .attr("viewBox","0 0 "+rect.width+" "+rect.height);

  $$.d3.svg.select(".x.axis")
    .attr("transform", "translate(0," + height + ")")
    .call($$.d3.xAxis
      .scale(x)
      .innerTickSize(-height)
        .outerTickSize(-height)
    );
  $$.d3.svg.select(".y.axis").call(
    $$.d3.yAxis
      .scale(y)
      .innerTickSize(-width)
        .outerTickSize(-width)
  );
  $$.tooltip.cursor.attr("y2",height);
  $$.d3.zoom_x.x(x);
  $$.d3.zoom_y.y(y);
  $$.d3.svg.selectAll('[data-for*="x"]').attr("width",width);
  $$.d3.svg.selectAll('[data-for*="y"]').attr("height",height);
  $$.canvas.width = width;
  $$.canvas.height = height;
  $$.canvas.setAttribute("width",width+"px");
  $$.canvas.setAttribute("height",height+"px");
  $$.render();
}

Chart.prototype.zoom_to_x = function(domainx){
  var $$ = this;
  $$.d3.zoom_x.x($$.d3.x.domain(domainx));
  $$.d3.svg.select(".x.axis").call($$.d3.xAxis);


  var domainy = $$.d3.y.domain();
  $$.uniforms.u_resolution = [domainx[1]-domainx[0],domainy[1]-domainy[0]];
  $$.uniforms.u_translation = [domainx[0]-$$.initialDomain.x[0],domainy[0]];
  $$.render();
}

Chart.prototype.updateBufferInfo = function(line_index) {
  const $$ = this
  const data = this.lines[line_index]
  
  var first = data.data[0],
    last = data.data[data.data.length-1],
    timeDiff = $$.initialDomain===undefined ? first.d : $$.initialDomain.x[0];

  data.domain = {
    x:[first.d,last.d],
    y:[first.v,first.v]
  };

  var tmp = [];
  if (data.type=="discrete") { 
    tmp = [first.d-timeDiff,0, last.d-timeDiff,0];//Линия
    var firstdate = first.d.getTime();
    var tmpv = 0, tmpd = timeDiff;
    data.data.forEach(function(e){
      if ((tmpv==1)&&(e.v==0)){
        tmp.push(
          tmpd-timeDiff,0,
          tmpd-timeDiff,1,
          e.d-timeDiff,1,

          tmpd-timeDiff,0,
          e.d-timeDiff,0,
          e.d-timeDiff,1,
          );
          tmpv=0;
      }
      if ((e.v==1)&&(tmpv==0)) {
        tmpv = e.v;
        tmpd = e.d;
      };
      if (e.v<data.domain.y[0]) data.domain.y[0]=e.v;
      if (e.v>data.domain.y[1]) data.domain.y[1]=e.v;
    });
  } else {
    // tmp = [0,first.v]
    tmp = []
    var firstdate = first.d.getTime();
    if (data.interpolate=="linear"){ 
      data.data.forEach(function(e){
          tmp.push(e.d-timeDiff,e.v);
          if (e.v<data.domain.y[0]) data.domain.y[0]=e.v;
           if (e.v>data.domain.y[1]) data.domain.y[1]=e.v;
      });
    } else { //step-after
      var tmp2 = first.v;
      data.data.forEach(function(e){
          tmp.push(e.d-timeDiff,tmp2,e.d-timeDiff,e.v);
          tmp2=e.v;
          if (e.v<data.domain.y[0]) data.domain.y[0]=e.v;
           if (e.v>data.domain.y[1]) data.domain.y[1]=e.v;
      });
    }
    tmp.push(data.domain.x[1]-timeDiff,last.v);
    
  }
  var arrays = {
    a_position: {  size:2,  type:$$.gl.FLOAT,  data: new Float32Array(tmp),drawType:$$.gl.STREAM_DRAW}
  };
  delete data.bufferInfo
  data.bufferInfo = twgl.createBufferInfoFromArrays($$.gl, arrays);
}

Chart.prototype.updateColor = function(line_index,r,g,b){
  if (!this.lines[line_index]) return
  const line = this.lines[line_index]
  line.color = [r,g,b,1]
  let colorcss = colorArrayToRGB(line.color)
  this.legend.select(`li[data-id='${line.id}']`).style({
    "color":colorcss
  })
  this.render()

}
function onzoom($$, axis){
  var domainx = $$.d3.x.domain();
  var domainy = $$.d3.y.domain();

  $$.uniforms.u_resolution = [domainx[1]-domainx[0],domainy[1]-domainy[0]];
  $$.uniforms.u_translation = [domainx[0]-$$.initialDomain.x[0],domainy[0]];
  $$.render();
  if (axis=="x")
    $$.d3.svg.select(".x.axis").call($$.d3.xAxis);
  if (axis=="y")
    $$.d3.svg.select(".y.axis").call($$.d3.yAxis);  
} 

var dateOnCursor;

function mousemove($$) {
  var e  = d3.event,
  x = e.offsetX-$$.options.margin.left,
  width = parseFloat(e.target.getAttribute("width")),
  domain = $$.d3.x.domain(),
  t = new Date(domain[0].getTime()+Math.floor((domain[1]-domain[0])*x/(width))),
  rect = $$.tooltip.div.node().getBoundingClientRect();
  if ((dateOnCursor!==undefined)&&(Math.abs(t.getTime()-dateOnCursor.getTime())<(2*(domain[1]-domain[0])/width))) return;
  var newposition = {
    "left":null,
    "top":null,
    "right":null,
    "bottom":null
  }
  if ((e.x+rect.width+20) <window.innerWidth){
    newposition.left = (e.x)+"px"
  } else {
    newposition.left = (e.x-rect.width-40)+"px"
  }
  newposition.top = Math.min(Math.max((e.y-rect.height/2-10),0),(window.innerHeight-rect.height-20))+"px"
  
  $$.tooltip.div.style(newposition)

  $$.tooltip.cursor.attr({
    "x1":e.offsetX,
    "x2":e.offsetX
  });

  dateOnCursor = t;
  var cache = {}
  $$.tooltip.data  = $$.lines.map(function(line){
    //let x0 = Math.floor(line.data.length*((dateOnCursor-line.domain.x[0])/(line.domain.x[1]-line.domain.x[0])))
    //return { 
    //  title: line.title,
    //  value: line.data[find(line.data,Math.max(x0-2,0),Math.min(x0+2,line.data.length-1),dateOnCursor)]};
    //if (!cache.hasOwnProperty(line.data.length)) // Удалил. Нет нужды упрощать алгоритм. Бинарный поиск по сортированному итак быстро выполняется
    //  cache[line.data.length] = find(line.data,0,line.data.length-1,dateOnCursor)
    return { 
      title: line.title,
      color: colorArrayToRGB(line.color),
      value: line.data[find(line.data,0,line.data.length-1,dateOnCursor)]};
  });
  $$.tooltip.header.text(d3.time.format("%d-%m-%Y %H:%M:%S.%L")(dateOnCursor));
  $$.tooltip.update(); 
}


function find(arr,i0,i1,x){
  // Бинарный поиск
  if (i1-i0<=1){
    if (arr[i1].d<=x) return i1
    return i0;
  }
  var iNew = Math.floor((i1+i0)/2);
  if (arr[iNew].d<x) {
    return find(arr,iNew,i1,x)
  } else {
    return find(arr,i0,iNew,x);
  }
}

function parse(data,$$) {
  if (data.interpolate===undefined) data.interpolate = "linear";
  if (data.type===undefined) data.type = "lines";
  if (data.color===undefined){
    data.color = COLORMAP[$$.options.colorIndex]
    if (++$$.options.colorIndex>=COLORMAP.length-1) $$.options.colorIndex=0
  }

  data.disabled = false;
  var first = data.data[0],
    last = data.data[data.data.length-1],
    timeDiff = $$.initialDomain===undefined ? first.d : $$.initialDomain.x[0];

  data.id = new Date().getTime();
  data.domain = {
    x:[first.d,last.d],
    y:[first.v,first.v]
  };

  var tmp = [];
  if (data.type=="discrete") { 
    //Сначала рисуем линию на нуле от начала до конца, далее прямоугольники двумя треугольниками
    //Далее кладем в массив 2 треугольника по три координаты
    // ********************************
    // *                __            *
    // *               | /|           *
    // *    ___________|/_|______     * 
    // *[first]    [tmp2] [e]    last *
    // ********************************
    tmp = [first.d-timeDiff,0, last.d-timeDiff,0];//Линия
    var firstdate = first.d.getTime();
    var tmpv = 0, tmpd = timeDiff;
    data.data.forEach(function(e){
      if ((tmpv==1)&&(e.v==0)){
        tmp.push(
          tmpd-timeDiff,0,
          tmpd-timeDiff,1,
          e.d-timeDiff,1,

          tmpd-timeDiff,0,
          e.d-timeDiff,0,
          e.d-timeDiff,1,
          );
          tmpv=0;
      }
      if ((e.v==1)&&(tmpv==0)) {
        tmpv = e.v;
        tmpd = e.d;
      };
      if (e.v<data.domain.y[0]) data.domain.y[0]=e.v;
      if (e.v>data.domain.y[1]) data.domain.y[1]=e.v;
    });

  } else {
    // tmp = [0,first.v]
    tmp = []
    var firstdate = first.d.getTime();
    if (data.interpolate=="linear"){ 
      data.data.forEach(function(e){
          tmp.push(e.d-timeDiff,e.v);
          if (e.v<data.domain.y[0]) data.domain.y[0]=e.v;
           if (e.v>data.domain.y[1]) data.domain.y[1]=e.v;
      });      
    } else { //step-after
      var tmp2 = first.v;
      data.data.forEach(function(e){
          tmp.push(e.d-timeDiff,tmp2,e.d-timeDiff,e.v);
          tmp2=e.v;
          if (e.v<data.domain.y[0]) data.domain.y[0]=e.v;
           if (e.v>data.domain.y[1]) data.domain.y[1]=e.v;
      });
    }
    if (data.domain.y[0]===data.domain.y[1]){
      data.domain.y[0] = data.domain.y[0]*0.9;
      data.domain.y[1] = data.domain.y[1]*1.1;
      if (data.domain.y[0]===data.domain.y[1]){
        data.domain.y[0] = -0.1
        data.domain.y[0] = 0.1
      }
    }
    tmp.push(data.domain.x[1]-timeDiff,last.v);
    
  }
  var arrays = {
    a_position: {  size:2,  type:$$.gl.FLOAT,  data: new Float32Array(tmp),drawType:$$.gl.STREAM_DRAW}
  };
  data.bufferInfo = twgl.createBufferInfoFromArrays($$.gl, arrays);
  return data
}


function setLocale(locale){
 contextmenu_chart.currentLocale = locale 
 contextmenu_legend.currentLocale = locale
}

const contextmenu_legend = {
  target: null,
  currentLocale: 'en',
  locale: {
    'ru': ['Удалить','Переименовать','Линия/ступенчатый', 'Цвет','Применить формулу','Смещение по времени','Введите формулу', 'Смещение времени, мс', 'Новое имя'],
    'en': ['Delete','Rename', 'Line/Step', 'Color','Apply Formula','Time offset', 'Enter formula','Time offset, ms', 'Enter new name'],
  },
  items: {
    deleteLine:function(){
      const li = contextmenu_legend.target
      let line_id = li.dataset.id;
      let line
      for (let i=0; i<charts.length; i++) {
        for (let j=0;j<charts[i].lines.length;j++){
          if (line_id == charts[i].lines[j].id){
            line = charts[i].lines[j]
            d3.selectAll('[data-id="'+line_id+'"]').remove()
            charts[i].lines.splice(j,1)
            charts[i].render()
            break
          }
        }
        if (line!==undefined) break;
      }
    },
    rename:function() {
      const li = contextmenu_legend.target
      let line_id = li.dataset.id;
      let _line, _chart, line_index
      for (let i=0; i<charts.length; i++) {
        for (let j=0;j<charts[i].lines.length;j++){
          if (line_id == charts[i].lines[j].id){
            _chart = charts[i] 
            _line = charts[i].lines[j]
            let prompt_text = contextmenu_legend.locale[contextmenu_legend.currentLocale][8]
            let new_name = prompt(prompt_text, _line.title)
            if (new_name) {
              _line.title = new_name
              _chart.legend.select('[data-id="'+line_id+'"]').text(new_name)
            }
            return
          }
        }
        if (_line!==undefined) break;
      }
    },
    changeType: function(){
      const li = contextmenu_legend.target
      let line_id = li.dataset.id;
      let _line, _chart, line_index
      for (let i=0; i<charts.length; i++) {
        for (let j=0;j<charts[i].lines.length;j++){
          if (line_id == charts[i].lines[j].id){
            _chart = charts[i] 
            _line = charts[i].lines[j]
            line_index = j
            break
          }
        }
        if (_line!==undefined) break;
      }
      if (_line===undefined) return;
      if (_line.type!='lines') return
      if (_line.interpolate=='linear'){
        _line.interpolate='step-after'
      } else {
        _line.interpolate='linear'
      }
      _chart.updateBufferInfo(line_index)
      _chart.render()
    },
    changeColor:function(){
      const li = contextmenu_legend.target
      let line_id = li.dataset.id;
      let line
      for (let i=0; i<charts.length; i++) {
        for (let j=0;j<charts[i].lines.length;j++){
          if (line_id == charts[i].lines[j].id){
            line = charts[i].lines[j]
            break
          }
        }
        if (line!==undefined) break;
      }
      if (line===undefined) return;
      modal_app.color_picker.line = line

      modal_app.color_picker.model = colorArrayToHexa(line.color)
      modal_app.color_picker.saved = modal_app.color_picker.model
      modal_app.modal_color_picker = true
    },
    applyFormula:function(){
      const li = contextmenu_legend.target
      let line_id = li.dataset.id;
      let _line, _chart, line_index
      for (let i=0; i<charts.length; i++) {
        for (let j=0;j<charts[i].lines.length;j++){
          if (line_id == charts[i].lines[j].id){
            _chart = charts[i] 
            _line = charts[i].lines[j]
            line_index = j
            break
          }
        }
        if (_line!==undefined) break;
      }
      let prompt_text = contextmenu_legend.locale[contextmenu_legend.currentLocale][6]
      let formula = prompt(prompt_text, "v/10")
      if (!formula) return

      const buf = []
      try {
        _line.data.forEach((d)=>{
          let newValue = eval(formula.replaceAll('v',(d.v).toString()))
           if (!(typeof newValue === 'number' && Number.isFinite(newValue))){
            throw new Error("Result is not finite Number")
           }
          let o = Object.assign({}, d)
          o.v = newValue
          buf.push(o)  
        })
        _line.data = buf
        _chart.updateBufferInfo(line_index)
        _chart.render()
      } catch (err){
        app.addAlert(err)
      }

    },
    timeOffset:function(){
      const li = contextmenu_legend.target
      let line_id = li.dataset.id;
      let _line, _chart, line_index
      for (let i=0; i<charts.length; i++) {
        for (let j=0;j<charts[i].lines.length;j++){
          if (line_id == charts[i].lines[j].id){
            _chart = charts[i] 
            _line = charts[i].lines[j]
            line_index = j
            break
          }
        }
        if (_line!==undefined) break;
      }
      let prompt_text = contextmenu_legend.locale[contextmenu_legend.currentLocale][7]
      
      const buf = []
      try {
        let offset_ms = prompt(prompt_text, "0")
        if (!offset_ms) return
        offset_ms = parseFloat(offset_ms)

        _line.data.forEach((d)=>{
          let o = Object.assign({}, d)
          o.d = new Date(o.d.getTime()+offset_ms)
          buf.push(o)  
        })
        _line.data = buf
        _chart.updateBufferInfo(line_index)
        _chart.render()
      } catch (err){
        app.addAlert(err)
      }

    }
  }
}
const contextmenu_chart = {
  target: null,
  currentLocale: 'en',
  locale: {
    'ru': ['Удалить', 'Синхронизовать остальные','Исходный масштаб','Построить здесь'],
    'en': ['Delete', 'Align by time','Initial time scale','Draw here'],
  },
  items: {
    deleteChart:function(){
      if ((contextmenu_chart.target.nodeName=="rect")&&(contextmenu_chart.target.classList.contains("event-rect"))) {
        var e = contextmenu_chart.target.parentElement.parentElement.parentElement;
        var item_index = -1;
        charts.forEach((c,i)=>{
          if (c.options.element===e){
            c.destroy()
            e.remove();
            item_index = i;
          }
        });
        if (item_index!==-1) {
          charts.splice(item_index,1);
        }
      }
    },
    timeAlign:function(){
      if ((contextmenu_chart.target.nodeName=="rect")&&(contextmenu_chart.target.classList.contains("event-rect"))) {
          var e = contextmenu_chart.target.parentElement.parentElement.parentElement;
          var item_index = -1;
          charts.forEach((c,i)=>{
            if (c.options.element===e){
              item_index = i;
            }
          });
          if (item_index===-1){
            console.log('Что-то пошло не так');
            console.trace();
            return
          }
          charts.forEach((c,i)=>{
            if (item_index!==i){
              charts[i].zoom_to_x(charts[item_index].d3.x.domain());
            }
          })
      }
    },
    initialScale:function(){
      if ((contextmenu_chart.target.nodeName=="rect")&&(contextmenu_chart.target.classList.contains("event-rect"))) {
        var e = contextmenu_chart.target.parentElement.parentElement.parentElement;
        var item_index = -1;
        charts.forEach((c,i)=>{
          if (c.options.element===e){
            item_index = i;
          }
        });
        var $$ = charts[item_index],
          min,max,a=[];
        var discreteIndex = 0;
        $$.lines.forEach(function(line){
          if (line.type=="discrete"){
            a.push(-2*discreteIndex+1);
            discreteIndex++;
            return;
          }  
          a.push(line.domain.y[0]);
          a.push(line.domain.y[1]);
        });
        var extent = {
          x:$$.initialDomain.x,
          y:d3.extent(a)
        };
        if (extent.y[0]!=extent.y[1]){
          var h = (extent.y[1]-extent.y[0])*0.1;
          extent.y[1]+=h;
          extent.y[0]-=h;
        }
        $$.d3.zoom_y.y($$.d3.y.domain(extent.y));
        $$.zoom_to_x(extent.x);
      }
    },
    drawHere:function(){
      if ((contextmenu_chart.target.nodeName=="rect")&&(contextmenu_chart.target.classList.contains("event-rect"))) {
        if (app.tree_selected.length===0) return;
        var e = contextmenu_chart.target.parentElement.parentElement.parentElement;
        var item_index = -1;
        charts.forEach((c,i)=>{
          if (c.options.element===e){
            item_index = i;
          }
        });
        app.drawnum(item_index);
      }
    }
  }
}

function contextmenu_show(contextmenu){
  let div = d3.select('body').append("div")
    .attr("class","chart-contextmenu")
    .style({
      top: d3.event.clientY+"px",
      left: d3.event.clientX+"px",
    });
  let keys = Object.keys(contextmenu.items);
  div.append('ul')
    .selectAll("li")
    .data(keys)
    .enter()
    .append("li")
    .on('click', function(d){
      contextmenu.items[d]();
      contextmenu_close()
    })
    .text((d,i) => {
      return contextmenu.locale[contextmenu.currentLocale][i]
    });

  document.addEventListener('mousedown', contextmenu_close);
  document.addEventListener('keydown', contextmenu_close);
}
function contextmenu_close(evt){
  if (!(evt && evt.type=="mousedown" && evt.target.nodeName == "LI")){
    d3.select(".chart-contextmenu").remove()
    document.removeEventListener('mousedown', contextmenu_close);
    document.removeEventListener('keydown', contextmenu_close);
  }
  }

function Tooltip(appendTo){
  this.data=undefined;
  this.div = d3.select(appendTo).append("div").attr("class","tooltip");
  var table = this.div.append("table");
  this.header = table.append("caption");
  this.table = table.append("tbody");
  this.timestampFormat = d3.time.format("%H:%M:%S.%L");
}

Tooltip.prototype.update = function() {
  if (this.data===undefined) return;
  var table = this.table,
  timestampFormat = this.timestampFormat,
    buf='';
  this.data.forEach(function(d){
    buf +='<tr><td style="color: '+d.color+';">'+d.title+'</td><td>'+d.value.v+'</td><td>'+timestampFormat(d.value.d)+'</td></tr>'
  });  
  table.html(buf);
};

function reinit(){
  initialDomain = null;
}
//window.Chart = Chart;

//if ((new Date().getFullYear())!==2022) nw.Window.get().close();

return {
  Chart:Chart,
  setLocale,
  // menu:menus,
  reinit:reinit
}
}))


