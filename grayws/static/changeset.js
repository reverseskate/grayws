console.log(json)

function prettyResource(resource) {
  if (resource != undefined) {
    additional_keys = Object.keys(resource).filter(function(d) { return d != 'Type' && d!= 'Properties'; })
    res = {}
    res['Type'] = resource.Type
    res['Properties'] = resource.Properties
    additional_keys.forEach(function(d) {
      res[d] = resource[d];
    })
    return res }
}

function templateSnippet(resource, resource_list) {
  obj = {}
  obj[resource] = prettyResource(resource_list[resource])
  snippet = JSON.stringify(obj, null, 2).replace(/(^.*{\s*)|(\s*}.*$)/g,'').replace(/^\s{2}/gm, '')
  return snippet;
}

parameters = json['processed']['parameters']
table = d3.select(".content").append("table").attr("class", "changes");
headers = table.append("th").attr("class", "headers")

headers.append("td").attr("width", 50).attr("class", "header").attr("class", "action").text("Action");
headers.append("td").attr("width", 450).attr("class", "header").attr("class", "type").text("Type");
headers.append("td").attr("width", 450).attr("class", "header").attr("class", "resource").text("Resource");
//headers.append("td").attr("width", 450).text("Changes");
headers.append("td").attr("width", 100).attr("class", "replacement").text("Replacement");

// Sort by Modified first, then Add and Remove
rows = table.selectAll("tr")
  .data(
    json['processed']['changes'].filter(function(d) { return d.Action == 'Modify' }).concat(
      json['processed']['changes'].filter(function(d) { return d.Action != 'Modify' }).sort(
        function(x,y) { return d3.ascending(x.Action, y.Action) })))
  .enter()
  .append("tr").attr("class", "changes");

// Append a table for each change set with three rows
rows.append("td").attr("colspan", 4).attr("class", "container").append("table").attr("class", "change-set");
// Append the change set description row
rows.select("table").append("tr").attr("class", "change-set");
rows.select("table").select("tr.change-set").append("td").text(function(d) { return d.Action; }).attr("width", 52).attr("class", "action");
rows.select("table").select("tr.change-set").append("td").text(function(d) { return d.ResourceType; } ).attr("width", 452).attr("class", "type");
rows.select("table").select("tr.change-set").append("td").attr("class", "logical-id").text(function(d) { return d.LogicalResourceId; } ).attr("width", 452).attr("class", "resource");
rows.select("table").select("tr.change-set").append("td").attr("width", 100).attr("class", "replacement").text(function(d) { return d.Replacement; });

// Append the change set reasons row
rows.select("table").filter(function(d) { return d.Action == 'Modify'; }).append("tr").attr("class", "reasons");
rows.select("table").select("tr.reasons").append("td");
rows.select("table").select("tr.reasons").append("td").attr("class", "details").attr("colspan", 2).attr("width", 906);
// Append the change set compare row
rows.select("table").append("tr").attr("class", "compare");
rows.select("table").select("tr.compare").append("td").text("Compare");
rows.select("table").select("tr.compare").append("td").attr("class", "old").attr("width", 450).append("pre").text(function(d) { 
  return templateSnippet(d.LogicalResourceId, json['orig']);
});
rows.select("table").select("tr.compare").append("td").attr("class", "new").attr("width", 450).append("pre").text(function(d) { 
  return templateSnippet(d.LogicalResourceId, json['new']);
});

changes = rows.select("table").select("tr.reasons").selectAll("td.details").select("td.details")

changes.data(function(d) { return d.Details; }) 
  .enter()
  .select("td.details")
  .append("li")
  .text(function(d) { return d; });