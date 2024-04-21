// Javascript custom functions for the folium map

var {{this.get_name()}} = L.popup({maxWidth:500});

function latLngPop(e) {
    stations = ''
    ids=[];
    i = 0;
    latlon = e.latlng;
    lat = e.latlng['lat'];
    lon = e.latlng['lng'];
    
    // deactivate FOV layers, if active
    var sel100 = document.querySelector("#groundplot_007 > div.leaflet-control-container > div.leaflet-top.leaflet-right > div.leaflet-control-layers.leaflet-control-layers-expanded.leaflet-control > section > div.leaflet-control-layers-overlays > label:nth-child(3) > span > input")
    var sel70 = document.querySelector("#groundplot_007 > div.leaflet-control-container > div.leaflet-top.leaflet-right > div.leaflet-control-layers.leaflet-control-layers-expanded.leaflet-control > section > div.leaflet-control-layers-overlays > label:nth-child(4) > span > input")
    var sel25 = document.querySelector("#groundplot_007 > div.leaflet-control-container > div.leaflet-top.leaflet-right > div.leaflet-control-layers.leaflet-control-layers-expanded.leaflet-control > section > div.leaflet-control-layers-overlays > label:nth-child(5) > span > input")
    if (sel100.checked) { sel100.click(); }
    if (sel70.checked) { sel70.click(); }
    if (sel25.checked) { sel25.click(); }

    fovfg_i100.getLayers()[0].eachLayer(
        function(layer) { 
            if (layer.contains(latlon) ) {
                stations = stations + layer.feature.properties.station + ', ';
                ids.push(layer.feature.id);
                //layer.bindTooltip(layer.feature.properties.station, {
                //    sticky: true
                //});
                groundplot_007.addLayer(layer);
                i = i + 1;
            }
        }
    );
    if (stations.length > 0) { 
            stations = stations.slice(0,stations.length-2);
            txt = "lat=" + lat.toFixed(4) + ", lon=" + lon.toFixed(4) + "<br>"
            txt = txt + "Covered by " + i + " camera(s) at height of 100km:";
    } else {
        //txt = "No coverage";
        return;
    }
    {{this.get_name()}}.setLatLng(e.latlng).setContent(txt + "<br>" + stations).openOn({{this._parent.get_name()}})
}


function clearFOV(e) {
    if (e?.popup?._source?.feature?.geometry?.type in ["LineString","Point"]) {
        return;
    }
    var sel100 = document.querySelector("#groundplot_007 > div.leaflet-control-container > div.leaflet-top.leaflet-right > div.leaflet-control-layers.leaflet-control-layers-expanded.leaflet-control > section > div.leaflet-control-layers-overlays > label:nth-child(3) > span > input")
    var sel70 = document.querySelector("#groundplot_007 > div.leaflet-control-container > div.leaflet-top.leaflet-right > div.leaflet-control-layers.leaflet-control-layers-expanded.leaflet-control > section > div.leaflet-control-layers-overlays > label:nth-child(4) > span > input")
    var sel25 = document.querySelector("#groundplot_007 > div.leaflet-control-container > div.leaflet-top.leaflet-right > div.leaflet-control-layers.leaflet-control-layers-expanded.leaflet-control > section > div.leaflet-control-layers-overlays > label:nth-child(5) > span > input")
    groundplot_007.eachLayer(
        function(layer) {
            if (layer?.feature?.geometry?.type === 'MultiPolygon' && (ids.includes(layer?.feature?.id)) ) {
                if (!sel100.checked) {
                    groundplot_007.removeLayer(layer);
                }
            }
        }
    );
}


{{this._parent.get_name()}}.on('click', latLngPop);
{{this._parent.get_name()}}.on('popupclose', clearFOV);


                