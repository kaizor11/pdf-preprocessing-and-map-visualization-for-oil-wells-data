// this main.js includes a lot of code from openlayers documentation examples glued together and modified
// essentially, we want to show oil fields (implemented as OL Features) marked with an oil barrel icon
// and user can click on icons to view pertinent info about each field
// e.g. see https://openlayers.org/en/latest/examples/icon.html

import './style.css';
import {Map, View} from 'ol';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import {fromLonLat} from 'ol/proj';
import Overlay from 'ol/Overlay';
import Point from 'ol/geom/Point.js';
import {Style, Icon} from 'ol/style';
import Feature from 'ol/Feature.js';
import VectorLayer from 'ol/layer/Vector.js';
import VectorSource from 'ol/source/Vector.js';
//import mysqlPromise from "mysql2/promise.js"

const iconStyle = new Style({
  image: new Icon({
    anchor: [0.5, 46],
    anchorXUnits: 'fraction',
    anchorYUnits: 'pixels',
    src: 'icons/oil-icon.png', //oil icon provided w/out attribution requirement from https://uxwing.com/oil-icon/
  }),
});

// plot an example point
const iconFeature = new Feature({
  geometry: new Point(fromLonLat([-102.397386,48.057353])),
  name: 'CHALMERS 5300 31-19H',
  operator: 'OASIS PETROLEUM NORTH AMERICA LLC',
  api: '33-053-03472',
  status: 'Abandoned',
  closest_city: "Williston",
  first_prod_date: "November 1986",
  last_prod_date: "December 2025",
});
iconFeature.setStyle(iconStyle);

// send features to vectorlayer
const vectorSource = new VectorSource({
  features: [iconFeature],
});
const vectorLayer = new VectorLayer({
  source: vectorSource,
});

const map = new Map({
  target: document.getElementById('map'),
  layers: [
    new TileLayer({
      source: new OSM()
    })
  ],
  view: new View({
    center: fromLonLat([-100, 40]),
    zoom: 5
  })
});

map.addLayer(vectorLayer);


const element = document.getElementById('popup');
// popup for click position
const popup = new Overlay({
  element: element,
  positioning: 'bottom-center',
  stopEvent: false,
});
map.addOverlay(popup);

let popover;
function disposePopover() {
  if (popover) {
    popover.dispose();
    popover = undefined;
  }
}

// popup on click
map.on('singleclick', function (evt) {
  const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature) {
    return feature;
  });
  disposePopover();
  if (!feature) {
    return;
  }
  popup.setPosition(evt.coordinate);

  // get the info from oil-well feature for popup
  popover = new bootstrap.Popover(element, {
    placement: 'top',
    html: true,
    content: '<p>Name: <code>' + feature.get('name') + '</code></p>' + 
    '<p>Operator: <code>' + feature.get('operator') + '</code></p>' + 
    '<p>API: <code>' + feature.get('api') + '</code></p>' +
    '<p>Status: <code>' + feature.get('status') + '</code></p>' + 
    '<p>Closest City: <code>' + feature.get('closest_city') + '</code></p>' +
    '<p>First Production Date: <code>' + feature.get('first_prod_date') + '</code></p>' +
    '<p>Last Production Date: <code>' + feature.get('last_prod_date') + '</code></p>' 
  });
  popover.show();
});

// change mouse cursor when over marker
map.on('pointermove', function (e) {
  const hit = map.hasFeatureAtPixel(e.pixel);
  map.getTargetElement().style.cursor = hit ? 'pointer' : '';
});
// Close the popup when the map is moved
map.on('movestart', disposePopover);