// Javascript custom functions for the station markers

var {{this.get_name()}} = L.popup({maxWidth:500});

function stationsPop(e) {
    stations = ''
    ids=[];
    i = 0;
    latlon = e.latlng;
    lat = e.latlng['lat'];
    lon = e.latlng['lng'];
    fovfg_008.getLayers()[0].eachLayer(
        function(layer) { 
            if (layer.contains(latlon) ) {
                stations = stations + layer.feature.properties.station + ', ';
                ids.push(layer.feature.id);
                groundplot_007.addLayer(layer);
                i = i + 1;
            }
        }
    );
    if (stations.length > 0) { 
            stations = stations.slice(0,stations.length-2);
            txt = "lat=" + lat.toFixed(4) + ", lon=" + lon.toFixed(4) + "<br>"
            txt = txt + "Covered by " + i + " camera(s):";
    } else {
        //txt = "No coverage";
        return;
    }
    {{this.get_name()}}.setLatLng(e.latlng).setContent(txt + "<br>" + stations).openOn({{this._parent.get_name()}})
}

{{this._parent.get_name()}}.on('click', stationsPop);



                