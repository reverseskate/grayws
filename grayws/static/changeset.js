console.log(json)

table = d3.select(".content").append("table").attr("class", "changes");
headers = table.append("tr").attr("class", "headers")

headers.append("td").attr("width", 75).text("Action");
headers.append("td").attr("width", 175).text("Type");
headers.append("td").attr("width", 200).text("Resource");
headers.append("td").attr("width", 450).text("Changes");
headers.append("td").attr("width", 100).text("Replacement");

// Sort by Modified first, then Add and Remove
rows = table.selectAll("tr.change")
  .data(
    json['processed']['changes'].filter(function(d) { return d.Action == 'Modify' }).concat(
      json['processed']['changes'].filter(function(d) { return d.Action != 'Modify' }).sort(
        function(x,y) { return d3.ascending(x.Action, y.Action) })))
  .enter()
  .append("tr")
  .attr("class", "change-set");

rows.append("td").text(function(d) { return d.Action; } );
rows.append("td").text(function(d) { return d.ResourceType; } );
rows.append("td").attr("class", "logical-id").text(function(d) { return d.LogicalResourceId; } );
rows.append("td").attr("class", "changes");
rows.append("td").text(function(d) { return d.Replacement; });

changes = rows.selectAll("td.changes");
console.log(changes)

changes.data(function(d) { return d.Details; }) 
  .enter()
  .select("td.changes")
  .append("li")
  .text(function(d) { return d; });