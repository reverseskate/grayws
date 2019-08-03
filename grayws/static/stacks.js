table = d3.select(".content")
  .append("table")
  .attr("class", "stack-list")

table.append("th").text("Stack")
table.append("th").text("Status")
table.append("th").text("In Sync")
table.append("th").text("Created")
table.append("th").text("Updated")

rows = d3.select("table.stack-list")
  .selectAll("row")
  .data(json)
  .enter()
  .append("tr")

rows.append("td")
  .attr("class", "name")
  .append("a")
  .attr("href", function(d) { return d.link; })
  .attr("class", "stack-link")
  .text(function(d,i) { return d.name; })

rows.append("td")
  .attr("class", "status")
  .text(function(d) { return d.status.replace('_', ' ') })

rows.append("td")
  .attr("class", "drift")
  .text(function(d) { if (d.drift == 'IN_SYNC') {
      return '√';
    } else if (d.drift == 'NOT_CHECKED') {
      return '?';
    } else {
      return 'X';
    }
})

rows.append("td")
  .attr("class", "created")
  .text(function(d) { return d.created })

rows.append("td")
  .attr("class", "updated")
  .text(function(d) { return d.updated })


;
