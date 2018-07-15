//console.log(json)

// d3.select(".content")
//   .selectAll("div")
//   .data(json)
//     .enter()
//     .append("div")
//     .style("width", "200px")
//     .style("height", "100px")
//     .text(function(d) { return d['name']; });
    
    
var data = [30, 86, 168, 281, 303, 365];

d3.select(".content")
  .selectAll("div")
  .data(data)
    .enter()
    .append("div")
    .style("width", function(d) { return d + "px"; })
    .text(function(d) { return d; });