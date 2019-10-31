function pretty_json(input) {
  try { 
    to_json = JSON.parse(input)
    snippet = JSON.stringify(to_json, null, 2).replace(/(^.*{\s*)|(\s*}.*$)/g,'').replace(/^\s{2}/gm, '')
  } catch(e) { 
    snippet = input
    console.log(input, 'not json')
  } 
  return snippet
}

function templateSnippet(resource, resource_list) {
  obj = {}
  obj[resource] = prettyResource(resource_list[resource])
  snippet = JSON.stringify(obj, null, 2).replace(/(^.*{\s*)|(\s*}.*$)/g,'').replace(/^\s{2}/gm, '')
  return snippet;
}

function nested_table(rows, row_class, table_class) {
// Append a table for each change set with three rows
rows.append("td").attr("class", row_class).append("table").attr("class", table_class).attr("width", "100%");
// Append the change set description row
rows.select("table").append("tr").attr("class", table_class);
}

var info_table = d3.select(".info").append("table").attr("width", "100%");
var info_headers = info_table.append("tr").attr("class", "headers");
info_headers.append("td").attr("width", "33%").attr("colspan", 2).text("Parameters")
info_headers.append("td").attr("width", "33%").attr("colspan", 2).text("Outputs")
info_headers.append("td").attr("width", "33%").attr("colspan", 2).text("Tags")

var info_rows = info_table.selectAll("tr.info")
  .data(json['info'])
  .enter()
  .append("tr")
  .attr("class", "info");

info_rows.append("td").text(function(d) { return d.ParameterKey })
info_rows.append("td").text(function(d) { return d.ParameterValue })
info_rows.append("td").text(function(d) { return d.OutputKey })
info_rows.append("td").text(function(d) { return d.OutputValue })
info_rows.append("td").text(function(d) { return d.Key })
info_rows.append("td").text(function(d) { return d.Value }) 

var set_table = d3.select(".change_sets").append("table");
var set_headers = set_table.append("tr").attr("class", "headers")

set_headers.append("td").attr("width", 300).text("Name");
set_headers.append("td").attr("width", 200).text("Execution Status");
set_headers.append("td").attr("width", 200).text("Creation Status");
set_headers.append("td").attr("width", 300).text("Timestamp");
set_headers.append("td").attr("width", 100).text("Compare");

var set_rows = set_table.selectAll("tr.change-set")
  .data(json['change_sets'])
  .enter()
  .append("tr")
  .attr("class", "change-set");

set_rows.append("td")
  .append("a")
  .attr("href", function(d) { return "set/" + d['name']; })
  .text(function(d) { return d['name']; } );
set_rows.append("td").text(function(d) { return d['exec_status']; });
set_rows.append("td").text(function(d) { return d['status']; });
set_rows.append("td").text(function(d) { return d['created']; });
set_rows.append("td").append("input").attr("type", "checkbox");

var drift_table = d3.select(".drift").append("table").attr("width", "100%");

var drift_rows = drift_table.selectAll("tr.container")
  .data(json['drifts'])
  .enter()
  .append("tr")
  .attr("class", "container")

nested_table(drift_rows, "container", "drift")

drift_rows.select("table").select("tr")
  .append("td")
  .text(function(d) { return "Resource " + d['StackResourceDriftStatus'] + ": "; })
  .append("span")
  .attr("class", "resource")
  .text(function(d) { return d['LogicalResourceId'] + " (" + d['ResourceType'] + ")"})

var difference_rows = drift_rows.select("table").selectAll("tr.differences")
  .data(function(d) { return d.PropertyDifferences })
  .enter()
  .append("tr").attr("class", "differences")

var difference_items = difference_rows.append("td").attr("class", "difference")

difference_items.append("li")
  .attr("class","property")
  .text("Property:")
  .append("span")
  .attr("class", "code")
  .text(function(d) { return d.PropertyPath; });
difference_items.append("li")
  .attr("class","expected")
  .text("Expected:")
  .append("pre")
  .text(function(d) { return pretty_json(d.ExpectedValue) });
difference_items.append("li")
  .attr("class","actual")
  .text("Actual:")
  .append("pre")
  .text(function(d) { return pretty_json(d.ActualValue); });
