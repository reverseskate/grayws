var settings = {
  "Parameter": {
    "color": "blue",
    "scale": .8
  },
  "Resource": {
    "color": "white",
    "scale": 1
  },
  "Output": {
    "color": "black",
    "scale": .7
  }  
}

var resource_states = {
  "CREATE_IN_PROGRESS": {
    "color": "yellow"
  }, 
  CREATE_FAILED: {
    color: "red"
  },
  CREATE_COMPLETE: {
    "color": "green"
  },
  DELETE_IN_PROGRESS: {
    color: "yellow"
  },
  DELETE_FAILED: {
    color: "red"
  },
  DELETE_COMPLETE: {
    color: "green"
  },
  DELETE_SKIPPED: {
    color: "orange"
  },
  UPDATE_IN_PROGRESS: {
    color: "yellow"
  },
  UPDATE_FAILED: {
    color: "orange"
  },
  UPDATE_COMPLETE: {
    color: "green"
  }
}

function resource_state(stack) {
  console.log("refresh")
  d3.json("/stack/" + stack + "/json/resources/").then(function(resources) {
    resources.forEach(function(d) {
      d3.select("circle." + d.LogicalResourceId).attr("class", d3.select("circle." + d.LogicalResourceId).attr("class").replace("incomplete", d.ResourceStatus))
        .attr("stroke-width", node_size * settings["Resource"]["scale"] * .1)
//        .attr("stroke", function(d) { return resource_states[d.ResourceStatus]["color"]; })
    })

/*
    first_event = d3.max(events.filter(function(d) { return d.ResourceStatusReason == "User Initiated" && d.ResourceType == "AWS::CloudFormation::Stack" }), function(d) { return d.Timestamp; })
    current_events = events.filter(function(d) { return d.Timestamp >= first_event && d.ResourceType != "AWS::CloudFormation::Stack"; })
    current_events.forEach(function(d) {    
      d3.select("circle." + d.LogicalResourceId).attr("class", d3.select("circle." + d.LogicalResourceId).attr("class").replace("incomplete", "complete")).attr("stroke-width", node_size * settings["Resource"]["scale"] * .1)
    })
*/
  })
}

var deps = []

function check_icon(image_url) {
    var http = new XMLHttpRequest();

    http.open('HEAD', image_url, false);
    http.send();
    
    if (http.status == 200) {
      image = image_url
    } else {
      image = "/static/icons/404.png"
    }
  return image
}

function find_refs(resource) {
  obj = {
    "resource": resource.key,
    "dependencies": []    
  }
  properties = d3.keys(resource.value.Properties)
  properties.forEach(function(property) {
    config = resource.value.Properties[property]
    if (Array.isArray(config)) {
    } else if (typeof(config) === 'object') {
      if (['Ref', 'Fn::GetAtt'].some(function(d) { return d == d3.keys(config)[0] })) {
        obj['dependencies'].push({
          "property": property,
          "type": d3.keys(config)[0],
          "dependency": d3.values(config)[0]
        })
      }
    }
  })
  return obj;
}

d3.entries(json.Resources).forEach(function(resource) {
  if (!d3.keys(json.Resources[resource.key]).includes("_grayws")) {
     json.Resources[resource.key]._grayws = {
       dependencies: [],
       depended_by: []
     }
  }
  resource_deps = find_refs(resource)
  if (resource_deps.dependencies.length > 0) {
    deps.push(resource_deps)
    json.Resources[resource.key]._grayws.dependencies = resource_deps.dependencies
    resource_deps.dependencies.forEach(function(dep) {
      if (d3.keys(json.Resources).includes(dep.dependency)) {
        if (d3.keys(json.Resources[dep.dependency]).includes("_grayws")) { 
          if (d3.keys(json.Resources[dep.dependency]._grayws).includes("depended_by")) {
            json.Resources[dep.dependency]._grayws.depended_by.push(resource.key)
          } else {
            json.Resources[dep.dependency]._grayws.depended_by = [resource.key]
          }
        } else {
          json.Resources[dep.dependency]._grayws = {
            "depended_by": [resource.key]
          }
        }
      } else if (d3.keys(json.Parameters).includes(dep.dependency)) {
        if (d3.keys(json.Parameters[dep.dependency]).includes("_grayws")) { 
          if (d3.keys(json.Parameters[dep.dependency]._grayws).includes("depended_by")) {
            json.Parameters[dep.dependency]._grayws.depended_by.push(resource.key)
          } else {
            json.Parameters[dep.dependency]._grayws.depended_by = [resource.key]
          }
        } else {
          json.Parameters[dep.dependency]._grayws = {
            "depended_by": [resource.key]
          }
        }
      }
    })
  }
});

positions = {}

paths = []

var grayws_nodes = d3.keys(json.Parameters).map(function(d) { return { id: d, type: "Parameter" }}).concat( 
  d3.entries(json.Resources).map(function(d) { return { id: d.key, type: "Resource", resource: d.value.Type }})).concat(
  d3.keys(json.Outputs).map(function(d) { return { id: "Output_" + d, type: "Output" }}))

var grayws_links = []

var parameters = d3.entries(json.Parameters).sort(function(a,b) {
  function sort_value(key) {
    if (d3.keys(key.value).includes('_grayws')) {
      sort_by = key.value._grayws.depended_by.join()
    } else {
      sort_by = ""
    }
    return sort_by
  }
  return d3.descending(sort_value(a), sort_value(b));
});

var resources = d3.entries(json.Resources).sort(function(a,b) {
  if (!d3.keys(a.value._grayws).includes('dependencies')) {
    a.value._grayws.dependencies = []
  }
  if (!d3.keys(b.value._grayws).includes('dependencies')) {
    b.value._grayws.dependencies = []
  }
  return d3.descending(a.value._grayws.dependencies.join(), b.value._grayws.dependencies.join());
});

/*
var dependent_counts = d3.set(d3.values(resources).map(function(resource) { 
  return resource.value._grayws.depended_by.length;
})).values().sort().map(String)

var spacing_increment = 1000/dependent_counts.length

sorted_resources = resources.sort(function(a,b) {
  function dependencies_average_index(key) {
    index = 0
    key.value._grayws.dependencies.forEach(function(dep) {
      if (d3.keys(json.Parameters).includes(dep.dependency)) {
        index += (parameters.map(function(d) { return d.key }).indexOf(dep.dependency) + 1)
      } else {
        index += (resources.map(function(d) { return d.key }).indexOf(dep.dependency) + 1)
      }
    })
    return index/key.value._grayws.dependencies.length
  }
  return d3.ascending(dependencies_average_index(a), dependencies_average_index(b));
});

parameters.forEach(function(parameter, i) {
  positions[parameter.key] = { x: 1000, y: 60 * i }  
});

resources.forEach(function(resource, i) {
  positions[resource.key] = { x: spacing_increment * dependent_counts.indexOf(String(resource.value._grayws.depended_by.length)), y: 50 * i + 60 }
});
*/

resources.forEach(function(resource, i) {
  if (d3.keys(resource.value._grayws).includes('dependencies')) {
    resource.value._grayws.dependencies.forEach(function(dep) {
/*
      paths.push({
        dep: dep.dependency,
        source: [ positions[resource.key].x + 70, positions[resource.key].y + 15 ],
        target: [ positions[dep.dependency].x, positions[dep.dependency].y + 15 ]
      })
*/
      if (Array.isArray(dep.dependency)) {
        grayws_links.push({
          source: resource.key,
          target: dep.dependency[0],
          value: 1
        })
      } else {
        grayws_links.push({
          source: resource.key,
          target: dep.dependency,
          value: 1
        })
      }  
  })
}
});

var outputs = d3.entries(json.Outputs)

output_links = outputs.map(function(d) {
  if (d3.keys(d.value.Value).includes('Ref')) {
    return { 
      source: "Output_" + d.key,
      target: d.value.Value.Ref
    };
  } else if (d3.keys(d.value.Value).includes('GetAtt')) {
    return { 
      source: "Output_" + d.key,
      target: d.value.Value['Fn::GetAtt'][0]
    }; 
  }
})

grayws_links = grayws_links.concat(output_links)

grayws_links = grayws_links.filter(function(d) { return d != undefined && !d.target.includes("AWS::") })


viz = d3.select('div.content').append('svg')
  .attr("width", "100%")
  .attr("height", 700)

// Horizontal Tree
/*
  
viz.selectAll('rect.parameter')
  .data(parameters)
  .enter()
  .append('rect')
  .attr('class', 'parameter')
  .attr('id', function(d) {return d.key;})
  .attr("x", function(d) { return positions[d.key].x })
  .attr("y", function(d) { return positions[d.key].y })
  .attr("width", 100)
  .attr("height", 30);

viz.selectAll('rect.resource')
  .data(d3.entries(json.Resources))
  .enter()
  .append('rect')
  .attr('class', 'resource')
  .attr('id', function(d) {return d.key;})
  .attr("x", function(d) { return positions[d.key].x })
  .attr("y", function(d) { return positions[d.key].y })
  .attr("width", 70)
  .attr("height", 30) //function(d) { return d3.entries(d.value.Properties).length * 30; });
  
viz.selectAll('path.link')
    .data(paths)
    .enter()
    .append('path')
    .attr('d', d3.linkHorizontal().source(function(d) { return d.source }).target(function(d) { return d.target }))
    .attr('class', 'link')
    .attr('stroke', 'blue')
    .attr('fill', 'none')
*/

// tree layout

/*

var roots = resources.filter(function(resource) {
  return resource.value._grayws.depended_by.length == 0;
})

tree_data = {
  "name": "stack",
  "children": []
}

roots.forEach(function(root) {
  tree_data.children.push({
    "name": root.key,
    "children": root.value._grayws.dependencies.map(function(dep) {
      if (d3.hierarchy(tree_data).descendants().map(function(d) { return d.data.name; }).indexOf(dep.dependency) === -1) {
        console.log("Not in array") 
        return {
          "name": dep.dependency,
          "value": dep.type
          };
        } else {
          return {};
        }
    })
  })
})

var hierarchies = roots.map(function(root) {
  return {
    "name": root.key,
    "children": root.value._grayws.dependencies.map(function(dep) {
      return {
        "name": dep.dependency,
        "value": dep.type,
        "children": [
          {
            "name": "foo",
            "type": "bar"
          },
          {
            "name": "bar",
            "type": "baz"
          }
        ]
      }
    })
  }  
})


var test_hier = d3.hierarchy(tree_data)


var treeLayout = d3.tree()
  .size([800,600])
*/
  
//treeLayout(test_hier)

/*
d3.select('svg').append('g')
d3.select('svg g').append('g').attr('class', 'nodes')
d3.select('svg g').append('g').attr('class', 'links')

// Nodes
d3.select('svg g.nodes')
  .selectAll('circle.node')
  .data(test_hier.descendants())
  .enter()
  .append('circle')
  .classed('node', true)
  .attr('cx', function(d) {return d.x;})
  .attr('cy', function(d) {return d.y;})
  .attr('r', 12)
  .attr('fill', 'none')
  .attr('stroke-width', 3);

// Links
d3.select('svg g.links')
  .selectAll('line.link')
  .data(test_hier.links())
  .enter()
  .append('line')
  .classed('link', true)
  .attr('stroke', 'green')
  .attr('stroke-width', 1)
  .attr('x1', function(d) {return d.source.x;})
  .attr('y1', function(d) {return d.source.y;})
  .attr('x2', function(d) {return d.target.x;})
  .attr('y2', function(d) {return d.target.y;});
*/

// force directed experiment

var node_size = 25

var defs = viz.append("defs")

var simulation = d3.forceSimulation()
  .force("link", d3.forceLink().id(function(d) { return d.id; }))
  .force("charge", d3.forceManyBody(-30).distanceMax(1))
  .force("center", d3.forceCenter(500, node_size * 12))
  .force("collision", d3.forceCollide().radius(node_size * 2));

var link = viz.append("g")
  .attr("class", "links")
  .selectAll("line")
  .data(grayws_links)
  .enter().append("line")
  .attr("stroke-width", 2)
  .attr("stroke", "purple");

var backgrounds = viz.append("g")
  .attr("class", "nodes")
  .selectAll("circle.background")
  .data(grayws_nodes)
  .enter().append("circle")
  .attr("r", function(d) { return node_size * settings[d.type]["scale"] * .9; })
  .attr("fill", "white");

var node = viz.append("g")
  .attr("class", "nodes")
  .selectAll("circle.node")
  .data(grayws_nodes)
  .enter().append("circle")
  .style("fill", function(d) { 
    return "url(#" + d.id + ")"
  })
  .attr("class", function(d) { return d.type + " node incomplete " + d.id; })
  .attr("r", function(d) { return node_size * settings[d.type]["scale"] * .9; })
  .attr("stroke", function(d) { return settings[d.type]["color"]; })
  .attr("stroke-width", function(d) { return node_size * settings[d.type]["scale"] * .1; })

var icon = defs.selectAll("icon")
  .data(grayws_nodes)
  .enter()
  .append("pattern")
  .attr("id", function(d) { return d.id })
  .attr("width", 1)
  .attr("height", 1)
  .attr("patternUnits", "objectBoundingBox")
  .append("image")
  .attr("xlink:href", function(d) { 
    if (d.type == "Resource") {
      if (d.resource.includes("Association") || d.resource.includes("Attachment")) {
        return "/static/icons/Association.svg"
      } else {
        return check_icon("/static/icons/" + d.resource.replace(/::/g, "_") + ".svg")
      }
    } else if (d.type == "Parameter") {
      return "/static/icons/Parameter.svg"
    } else if (d.type == "Output") {
      return "/static/icons/Output.svg"  
    }
  })
  .attr("width", node_size * .9 * 2)
  .attr("height", node_size * .9 * 2)
  .attr("x", 0)
  .attr("y", 0)

/*
var midpoint = viz.append("g")
  .attr("class", "nodes")
  .selectAll("circle")
  .data(grayws_links)
  .enter().append("circle")
  .attr("r", 1)
  .attr("fill", "yellow")
*/

/*
  .attr("xlink:href", function(d) { 
    if (d.type == "Resource") {
      return check_icon("/static/icons/" + d.resource.replace(/::/g, "_") + ".svg")
    } else {
      return "/static/icons/404.png"
    }
  })
  .attr("width", node_size * .9 * 2)
  .attr("height", node_size * .9 * 2)
  .attr("x", node_size * .9)
  .attr("y", node_size * .9)
  */

var label = node.append("text")
    .attr('x', 4)
    .attr('y', 3)
    .text(function(d) { return d.type + ": " + d.id; });

function simulate() {
  simulation
      .nodes(grayws_nodes)
      .on("tick", ticked)
      .tick(25)
      .on("end", swell)

  simulation.force("link")
      .links(grayws_links);

  function ticked() {
    link
      .attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

    backgrounds
      .attr("cx", function(d) { return d.x; })         
      .attr("cy", function(d) { return d.y; });

    node
      .attr("cx", function(d) { return d.x; }) 
      .attr("cy", function(d) { return d.y; });

/*
    midpoint
      .attr("cx", function(d) { return d.x = (d.source.x + d.target.x)/2; })
      .attr("cy", function(d) { return d.y = (d.source.y + d.target.y)/2; })
*/
  }
}

resource_state(stack)

simulate()

function swell() {

  // Animate In Progress
  in_progress =  d3.selectAll(".CREATE_COMPLETE, .UPDATE_IN_PROGRESS, .DELETE_IN_PROGRESS") 

  in_progress
    .attr("stroke-width", function(d) { return node_size * settings[d.type]["scale"] * .1; }) 
    .transition()
    .duration(2000)   
    .attr("stroke-width", function(d) { return node_size * settings[d.type]["scale"] * .3; }) 
    .transition()
    .duration(2000)
    .attr("stroke-width", function(d) { return node_size * settings[d.type]["scale"] * .1; })
    .transition()
    .duration(2000);
//    .on("end", swell());
  }

//swell()
//swell()

 
