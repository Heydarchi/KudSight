// === ui.js ===
import * as THREE from 'https://esm.sh/three';
import { loadGraphData, Graph, originalGraphData } from './graph.js';
// Start Change: Import clearSelection
import { getSelectedNodeIds, clearSelection } from './panel.js';
// End Change

let currentGraphFile = 'data.json'; // Keep track of the currently loaded file
let saveTimeout;

export function setCurrentGraphFile(filename) {
  currentGraphFile = filename;
}

export function autoSavePositions() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    const positions = {};
    Graph.graphData().nodes.forEach(node => {
      positions[node.id] = { x: node.x, y: node.y, z: node.z };
    });

    const baseName = currentGraphFile.replace(/\.json$/, '');
    const saveAs = baseName + '.pos.json';

    fetch('/save-pos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: saveAs, data: positions })
    })
      .then(res => res.json())
      .then(res => {
        if (res.status !== 'ok') {
          console.warn('Auto-save failed:', res.message);
        }
      })
      .catch(err => console.error('Auto-save error:', err));
  }, 1000);
}

// --- Function to update dropdown ---
function updateGraphDataDropdown(files) {
  const graphDataFileSelect = document.getElementById('graphDataFile');
  graphDataFileSelect.innerHTML = ''; // Clear existing options
  if (files && files.length > 0) {
    files.forEach(file => {
      const option = document.createElement('option');
      option.value = file;
      option.textContent = file;
      graphDataFileSelect.appendChild(option);
    });
  } else {
    // Handle case with no files
    const option = document.createElement('option');
    option.textContent = 'No data files found';
    option.disabled = true;
    graphDataFileSelect.appendChild(option);
  }
}

// --- Function to fetch and update file list ---
function loadJsonFileList() {
  fetch('/list-json')
    .then(response => response.json())
    .then(files => {
      // Use the new update function
      updateGraphDataDropdown(files);
      // After updating, if there's a value, load it (for initial load)
      const jsonSelect = document.getElementById('graphDataFile');
      if (jsonSelect.value) {
        loadGraphData(jsonSelect.value);
      }
    })
    .catch(err => console.error('Error fetching JSON file list:', err));
}

document.addEventListener('DOMContentLoaded', () => {
  const folderInput = document.getElementById('folderPath');
  const status = document.getElementById('status');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const cameraInfo = document.getElementById('cameraInfo');

  const resetCamBtn = document.getElementById('resetCamBtn');
  const zoomInBtn = document.getElementById('zoomInBtn');
  const zoomOutBtn = document.getElementById('zoomOutBtn');
  const tiltUpBtn = document.getElementById('tiltUpBtn');
  const tiltDownBtn = document.getElementById('tiltDownBtn');
  const orbitLeftBtn = document.getElementById('orbitLeftBtn');
  const orbitRightBtn = document.getElementById('orbitRightBtn');
  const rollLeftBtn = document.getElementById('rollLeftBtn');
  const rollRightBtn = document.getElementById('rollRightBtn');

  const tiltStep = 10;
  const orbitStep = 10;
  const rollStep = 0.05;

  const refreshBtn = document.getElementById('refreshButton'); // Use new ID
  const jsonSelect = document.getElementById('graphDataFile'); // Use new ID
  const focusSelectedBtn = document.getElementById('focusSelectedBtn');
  const showAllBtn = document.getElementById('showAllBtn');
  // Start Change: Get clear selection button
  const clearSelectionBtn = document.getElementById('clearSelectionBtn');
  // End Change

  analyzeBtn.addEventListener('click', () => {
    const folderPath = folderInput.value.trim();
    if (!folderPath) {
      status.textContent = 'Please enter a folder path.';
      return;
    }

    status.textContent = 'Analyzing...';
    analyzeBtn.disabled = true; // Disable button during analysis
    refreshBtn.disabled = true; // Disable refresh too

    // Use FormData for sending folder path
    const formData = new FormData();
    formData.append('folderPath', folderPath);

    fetch('/upload', {
      method: 'POST',
      body: formData // Send FormData object
    })
      .then(res => res.json())
      .then(res => {
        if (res.status === 'ok') {
          status.textContent = 'Analysis complete. Updating file list...';
          // --- Start Change: Update dropdown from analyze response ---
          updateGraphDataDropdown(res.files);
          // Automatically load the newest file (first in the sorted list)
          if (res.files && res.files.length > 0) {
            loadGraphData(res.files[0]);
          }
          // --- End Change ---
          status.textContent = ''; // Clear status
        } else {
          status.textContent = `Error: ${res.message}`;
        }
      })
      .catch(err => {
        status.textContent = 'Request failed.';
        console.error(err);
      })
      .finally(() => {
        analyzeBtn.disabled = false; // Re-enable button
        refreshBtn.disabled = false; // Re-enable refresh
      });
  });

  resetCamBtn.addEventListener('click', () => {
    const cam = Graph.camera();

    // Reset camera position
    Graph.cameraPosition({ x: 0, y: 0, z: 300 }, { x: 0, y: 0, z: 0 }, 1000);

    // Reset "up" vector (clears roll/tilt)
    cam.up.set(0, 1, 0);
  });

  zoomInBtn.addEventListener('click', () => Graph.camera().position.z -= 50);
  zoomOutBtn.addEventListener('click', () => Graph.camera().position.z += 50);
  tiltUpBtn.addEventListener('click', () => Graph.camera().position.y += tiltStep);
  tiltDownBtn.addEventListener('click', () => Graph.camera().position.y -= tiltStep);

  orbitLeftBtn.addEventListener('click', () => rotateCamera(orbitStep));
  orbitRightBtn.addEventListener('click', () => rotateCamera(-orbitStep));
  rollLeftBtn.addEventListener('click', () => Graph.camera().up.applyAxisAngle(new THREE.Vector3(0, 0, 1), rollStep));
  rollRightBtn.addEventListener('click', () => Graph.camera().up.applyAxisAngle(new THREE.Vector3(0, 0, 1), -rollStep));

  function rotateCamera(degrees) {
    const cam = Graph.camera();
    const angle = degrees * (Math.PI / 180);
    const { x, z } = cam.position;
    const r = Math.sqrt(x * x + z * z);
    const theta = Math.atan2(z, x) + angle;
    cam.position.x = r * Math.cos(theta);
    cam.position.z = r * Math.sin(theta);
  }

  setInterval(() => {
    const cam = Graph.camera();
    cameraInfo.textContent = `Camera: x=${cam.position.x.toFixed(1)}, y=${cam.position.y.toFixed(1)}, z=${cam.position.z.toFixed(1)} | up: (${cam.up.x.toFixed(2)}, ${cam.up.y.toFixed(2)}, ${cam.up.z.toFixed(2)})`;
  }, 500);

  // --- Refresh Button Listener ---
  refreshBtn.addEventListener('click', loadJsonFileList);

  // --- Dropdown Change Listener ---
  jsonSelect.addEventListener('change', () => {
    const selectedFile = jsonSelect.value;
    if (selectedFile) {
      loadGraphData(selectedFile); // Load selected graph
    }
  });

  // --- Filter Button Listeners ---
  focusSelectedBtn.addEventListener('click', () => {
    const selectedIds = getSelectedNodeIds(); // Get array of selected IDs

    // --- Start Revert to Client-Side Filtering ---
    if (selectedIds.length === 0 || !originalGraphData) {
        alert("Please select one or more items from the list first, or ensure graph data is loaded.");
        return;
    }

    const selectedIdsSet = new Set(selectedIds); // Use a Set for efficient lookup
    const linksToShow = [];

    console.log("Client-Side Filtering - Selected IDs Set:", selectedIdsSet);
    console.log("Client-Side Filtering - Checking links in original data (count):", originalGraphData.links.length);

    // Filter links: Keep only those where BOTH source and target are selected
    originalGraphData.links.forEach((link, index) => {
        // --- Start Change: Access .id property of source/target objects ---
        // Ensure link.source and link.target are objects with an 'id' property
        const sourceId = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;
        // --- End Change ---

        const sourceSelected = selectedIdsSet.has(sourceId);
        const targetSelected = selectedIdsSet.has(targetId);

        // Log the check for debugging
        console.log(
            `Client-Side Filtering - Link[${index}]: Checking "${sourceId}" (type: ${typeof sourceId}) -> "${targetId}" (type: ${typeof targetId}). ` +
            `Source in set? ${sourceSelected}. Target in set? ${targetSelected}`
        );

        if (sourceSelected && targetSelected) {
            console.log(`Client-Side Filtering - Adding link:`, link);
            linksToShow.push(link);
        }
    });

    // Filter nodes: Keep only the selected nodes
    const filteredNodes = originalGraphData.nodes.filter(node => selectedIdsSet.has(node.id));

    console.log("Client-Side Filtering - Filtered Nodes:", filteredNodes);
    console.log("Client-Side Filtering - Filtered Links:", linksToShow);

    // Create the filtered data object
    const filteredData = {
        nodes: filteredNodes,
        links: linksToShow,
        analysisSourcePath: originalGraphData.analysisSourcePath // Keep original path info
    };

    console.log(`Client-Side Filtering - Focusing on ${selectedIds.length} selected node(s) and links between them.`);
    Graph.graphData(filteredData); // Update graph with the filtered data
    // --- End Revert to Client-Side Filtering ---
  });

  showAllBtn.addEventListener('click', () => {
    if (originalGraphData) {
        console.log("Showing all nodes and links.");
        Graph.graphData(originalGraphData); // Reload original full data
        // Start Change: Clear selection when showing all
        clearSelection();
        // End Change
    } else {
        alert("No graph data loaded to show.");
    }
  });

  // Start Change: Add listener for Clear Selection button
  clearSelectionBtn.addEventListener('click', () => {
    clearSelection();
  });
  // End Change

  // --- Initial Load ---
  loadJsonFileList(); // Load file list and potentially the first graph on page load
});
