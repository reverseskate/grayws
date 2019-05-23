console.log(json)

table = d3.select('div.content')
  .append('table')
  
rows = table.selectAll('tr')
  .data(d3.values(json.Resources))
  .enter()
  .append("tr")
  
rows.append("td")
  .text(function(d) { return d.Type; })

rows.append("td")
  .append("img")
  .attr("src", function(d) { return "/static/icons/" + d.Type.replace(/::/g, "_") + ".svg"; })
  .attr("height", "40px")

console.log(json.Resources)
