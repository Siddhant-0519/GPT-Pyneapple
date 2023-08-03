import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, GeoJSON, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet'; // Import leaflet
import 'leaflet/dist/leaflet.css';
import FileSelector from './FileSelector.js';
import QueryInput from './QueryInput.js';
import {ColorMap} from './ColorMap.js';

// This component will receive the geoJSON data as a prop and update the map bounds when it changes
function GeoJSONLayer({ data }) {
  const map = useMap();
  const layerRef = useRef(null);

  useEffect(() => {
    if (data) {
      // If there is a previous layer, remove it
      if (layerRef.current) {
        layerRef.current.remove();
      }

      // Create the new layer
      const geojsonLayer = L.geoJson(data);

      // Add the new layer to the map
      geojsonLayer.addTo(map);

      // Fit the map view to the layer bounds
      const bounds = geojsonLayer.getBounds();
      map.fitBounds(bounds);

      // Keep track of the new layer
      layerRef.current = geojsonLayer;
    }
  }, [data, map]);

  // console.log("Plot Labels are: ",plotLabels);
  return data ? <GeoJSON data={data} /> : null;
}

const MapComponent = () => {
  const [geoJSON, setGeoJSON] = useState(null);

  useEffect(() => {
    console.log('GeoJSON state:', geoJSON); // Log geoJSON state whenever it changes
    // console.log("Plot Labels are: ",plotLabels);
  }, [geoJSON]);

  // useEffect(() => {
  //   console.log("PlotLabels:", plotLabels);
  // }, [plotLabels]);

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ flex: '0 0 20%', padding: '10px' }}>
        <FileSelector setGeoJSON={setGeoJSON} />
        <QueryInput style={{ minHeight: '5em', width: '100%' }} onQuerySubmit={(query) => console.log(query)} />

      </div>
      <div style={{ flex: '1', position: 'relative' }}>
        <MapContainer center={[51.505, -0.09]} zoom={13} style={{ height: "100%", width: "100%" }}>
          <TileLayer // Add a TileLayer for the basemap
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
          />
          <GeoJSONLayer data={geoJSON}  />
        </MapContainer>
      </div>
    </div>
  );
};

export default MapComponent;



