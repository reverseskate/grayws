console.log(json)

table = d3.select(".content").append("table");
headers = table.append("tr").attr("class", "headers")

headers.append("td").attr("width", 300).text("Name");
headers.append("td").attr("width", 200).text("Execution Status");
headers.append("td").attr("width", 200).text("Creation Status");
headers.append("td").attr("width", 300).text("Timestamp");
headers.append("td").attr("width", 100).text("Compare");


rows = table.selectAll("tr.change-set")
  .data(json['change_sets'])
  .enter()
  .append("tr")
  .attr("class", "change-set");

rows.append("td")
  .append("a")
  .attr("href", function(d) { return "set/" + d['name']; })
  .text(function(d) { return d['name']; } );
rows.append("td").text(function(d) { return d['exec_status']; });
rows.append("td").text(function(d) { return d['status']; });
rows.append("td").text(function(d) { return d['created']; });
rows.append("td").append("input").attr("type", "checkbox");


