
//mapObjKey = document.getElementsByClassName("folium-map")[0].id;
//L = this.window.L;
//L = window['0'].L

//let keyss = Object.keys(window);
//let mapObjKey = keyss.filter(name => name.startsWith("map"));
//const mapObj = this.window.frameElement.contentWindow[mapObjKey];


//mapObj.zoomIn();
//document.write("Toto napsal extern� Java Script");

function onMapClick(e) {
	
	let keyss = Object.keys(window);
	let mapObjKey = keyss.filter(name => name.startsWith("map"));
	const mapObj = this.window.frameElement.contentWindow[mapObjKey];


  map.on("click", addMarker);

  function addMarker(e) {
    // ustawiamy aby marker był przesuwalny
    const marker = new L.marker(e.latlng, {
      //draggable: true,
    }).addTo(map);

    var lat = (e.latlng.lat);
    var lng = (e.latlng.lng);
    var newLatLng = new L.LatLng(lat, lng);
    // alert(newLatLng);
    document.getElementById('clk_lat1').innerHTML = lat;
    document.getElementById('clk_lng1').innerHTML = lng;
  }
}
main = document.getElementById('main');
main.addEventListener('click', onMapClick);