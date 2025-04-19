// === ui.js ===
import * as THREE from 'https://esm.sh/three';
import { loadGraphData, Graph, originalGraphData } from './graph.js';
import { getSelectedNodeIds, clearSelection } from './panel.js';
import { styleFormElements } from './tailwind-helpers.js';
import { initTheme, toggleTheme, THEMES, updateUiForTheme, getNodeColorScheme } from './theme-manager.js';
import { initAnimations } from './animations.js';

let currentGraphFile = null; // Start with null
let currentViewMode = '3d'; // Default view mode
let saveTimeout;

// --- Get references to new elements ---
const viewMode3DRadio = document.getElementById('viewMode3D');
const viewModeUMLRadio = document.getElementById('viewModeUML');
const graphContainer = document.getElementById('graph-container');
const umlImageContainer = document.getElementById('uml-image-container');
const umlImage = document.getElementById('uml-image');
const rightPanel = document.getElementById('right-panel'); // Camera controls

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

// --- Function to set the view mode ---
function setViewMode(mode) {
  currentViewMode = mode;
  if (mode === '3d') {
    graphContainer.classList.remove('hidden');
    rightPanel.classList.remove('hidden'); // Show camera controls
    umlImageContainer.classList.add('hidden');
    // If graph data exists, ensure it's rendered
    if (originalGraphData) {
        // Update graph with current theme colors after switching views
        const isDarkTheme = document.documentElement.classList.contains('dark');
        const colors = getNodeColorScheme(isDarkTheme);
        
        if (Graph) {
          Graph
            .linkColor(colors.linkColor)
            .linkDirectionalArrowColor(colors.arrowColor)
            .backgroundColor(colors.bgColor)
            .graphData(Graph.graphData()); // Re-trigger rendering with current data
        }
    } else if (currentGraphFile) {
        loadContentForFile(currentGraphFile); // Load graph if file selected but no data yet
    }
  } else if (mode === 'uml') {
    graphContainer.classList.add('hidden');
    rightPanel.classList.add('hidden'); // Hide camera controls
    umlImageContainer.classList.remove('hidden');
    // Load the UML image if a file is selected
    if (currentGraphFile) {
        loadContentForFile(currentGraphFile);
    } else {
        umlImage.src = ''; // Clear image if no file selected
        umlImage.alt = 'Select an analysis result to view UML diagram.';
    }
  }
}

// --- Function to load content based on mode and file ---
function loadContentForFile(filename) {
    setCurrentGraphFile(filename); // Update the current file tracking

    if (currentViewMode === '3d') {
        // Load 3D graph data (uses the existing loadGraphData function)
        loadGraphData(filename);
    } else if (currentViewMode === 'uml') {
        // Construct PNG filename and load image
        const baseName = filename.replace(/\.json$/, '');
        const pngFilename = baseName + '.png'; // Assumes .png is generated alongside .puml
        const pngPath = '/out/' + pngFilename;

        // Check if image exists before setting src to avoid 404 console errors (optional but cleaner)
        fetch(pngPath, { method: 'HEAD' })
            .then(res => {
                if (res.ok) {
                    umlImage.src = pngPath;
                    umlImage.alt = `UML Diagram for ${filename}`;
                } else {
                    umlImage.src = '';
                    umlImage.alt = `UML Diagram PNG not found for ${filename} (Expected: ${pngFilename})`;
                }
            })
            .catch(err => {
                console.error("Error checking/loading UML image:", err);
                umlImage.src = '';
                umlImage.alt = 'Error loading UML diagram.';
            });
        // Also ensure the panel is updated with metadata from the JSON
        // Fetch JSON just for panel setup if needed, but avoid full graph load
        fetch('/out/' + filename)
            .then(res => res.json())
            .then(data => {
                if (data) setupPanel(data); // Update panel even in UML mode
            }).catch(err => console.error("Error loading JSON for panel in UML mode:", err));
    }
}

// --- Function to fetch and update file list ---
function loadJsonFileList() {
  return fetch('/list-json')
    .then(response => response.json())
    .then(files => {
      updateGraphDataDropdown(files);
      const jsonSelect = document.getElementById('graphDataFile');
      // Load the content for the initially selected file (respecting current view mode)
      if (jsonSelect.value) {
        loadContentForFile(jsonSelect.value);
      } else {
        // No files available, clear content areas
        Graph.graphData({ nodes: [], links: [] }); // Clear graph
        setupPanel({ nodes: [], links: [] }); // Clear panel
        umlImage.src = '';
        umlImage.alt = 'No analysis results found.';
        setCurrentGraphFile(null);
      }
    })
    .catch(err => {
      console.error('Error fetching JSON file list:', err);
      // Handle error state in UI
      updateGraphDataDropdown([]);
      Graph.graphData({ nodes: [], links: [] });
      setupPanel({ nodes: [], links: [] });
      umlImage.src = '';
      umlImage.alt = 'Error loading analysis results.';
      setCurrentGraphFile(null);
    });
}

document.addEventListener('DOMContentLoaded', () => {
  // Initialize theme first
  const currentTheme = initTheme();
  updateUiForTheme(currentTheme);
  
  // Apply Tailwind styles to form elements after theme is set
  styleFormElements();
  
  // Initialize animations
  initAnimations();

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
  const clearSelectionBtn = document.getElementById('clearSelectionBtn');

  analyzeBtn.addEventListener('click', () => {
    const folderPath = folderInput.value.trim();
    if (!folderPath) {
      status.textContent = 'Please enter a folder path.';
      return;
    }

    status.innerHTML = '<span class="inline-flex items-center"><svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Analyzing...</span>';
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
          updateGraphDataDropdown(res.files);
          // Automatically load the newest file (first in the sorted list)
          if (res.files && res.files.length > 0) {
            loadContentForFile(res.files[0]);
          }
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
  refreshBtn.addEventListener('click', () => {
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = '<span class="animate-spin inline-block mr-1">⟳</span> Loading...';
    
    loadJsonFileList().finally(() => {
      refreshBtn.disabled = false;
      refreshBtn.innerHTML = '<span class="inline-block mr-1">⟳</span> Refresh';
    });
  });

  // --- Dropdown Change Listener ---
  jsonSelect.addEventListener('change', () => {
    const selectedFile = jsonSelect.value;
    if (selectedFile) {
      loadContentForFile(selectedFile);
    }
  });

  // --- Filter Button Listeners ---
  focusSelectedBtn.addEventListener('click', () => {
    if (currentViewMode !== '3d') return; // Only works in 3D mode
    const selectedIds = getSelectedNodeIds(); // Get array of selected IDs

    if (selectedIds.length === 0 || !originalGraphData) {
        alert("Please select one or more items from the list first, or ensure graph data is loaded.");
        return;
    }

    const selectedIdsSet = new Set(selectedIds); // Use a Set for efficient lookup
    const linksToShow = [];

    // Filter links: Keep only those where BOTH source and target are selected
    originalGraphData.links.forEach((link) => {
        const sourceId = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

        const sourceSelected = selectedIdsSet.has(sourceId);
        const targetSelected = selectedIdsSet.has(targetId);

        if (sourceSelected && targetSelected) {
            linksToShow.push(link);
        }
    });

    // Filter nodes: Keep only the selected nodes
    const filteredNodes = originalGraphData.nodes.filter(node => selectedIdsSet.has(node.id));

    // Create the filtered data object
    const filteredData = {
        nodes: filteredNodes,
        links: linksToShow,
        analysisSourcePath: originalGraphData.analysisSourcePath // Keep original path info
    };

    Graph.graphData(filteredData); // Update graph with the filtered data
  });

  showAllBtn.addEventListener('click', () => {
    if (currentViewMode !== '3d') return; // Only works in 3D mode
    if (originalGraphData) {
        Graph.graphData(originalGraphData); // Reload original full data
        clearSelection();
    } else {
        alert("No graph data loaded to show.");
    }
  });

  clearSelectionBtn.addEventListener('click', () => {
    clearSelection();
  });

  // --- View Mode Change Listeners ---
  viewMode3DRadio.addEventListener('change', () => {
    if (viewMode3DRadio.checked) {
      setViewMode('3d');
      // Add animation to the switch for better feedback
      document.querySelectorAll('#view-mode-switcher label').forEach(label => {
        label.classList.add('transition-all');
      });
    }
  });

  viewModeUMLRadio.addEventListener('change', () => {
    if (viewModeUMLRadio.checked) {
      setViewMode('uml');
      // Add animation to the switch for better feedback
      document.querySelectorAll('#view-mode-switcher label').forEach(label => {
        label.classList.add('transition-all');
      });
    }
  });

  // Theme toggle button with improved animation
  const themeToggleBtn = document.getElementById('themeToggle');
  themeToggleBtn.addEventListener('click', () => {
    const newTheme = toggleTheme();
    updateUiForTheme(newTheme);
    
    // Add ripple effect to the toggle button
    const ripple = document.createElement('span');
    ripple.classList.add('absolute', 'inset-0', 'rounded-full', 'opacity-30', 
      newTheme === THEMES.DARK ? 'bg-gray-400' : 'bg-blue-300');
    themeToggleBtn.appendChild(ripple);
    
    // Remove ripple after animation
    setTimeout(() => {
      ripple.remove();
    }, 300);
    
    // Update graph or UML view based on current mode
    if (currentViewMode === '3d' && Graph) {
      const isDark = newTheme === THEMES.DARK;
      const colors = getNodeColorScheme(isDark);
      
      // Update graph colors
      Graph
        .linkColor(colors.linkColor)
        .linkDirectionalArrowColor(colors.arrowColor)
        .backgroundColor(colors.bgColor);
      
      if (originalGraphData) {
        // Force a full refresh of the graph to update all node appearances
        const currentData = Graph.graphData();
        Graph.graphData({ nodes: [], links: [] }); // Clear
        setTimeout(() => {
          Graph.graphData(currentData); // Reload with same data to force full refresh
        }, 10);
      }
    }
  });

  // --- Initial Load ---
  setViewMode(currentViewMode); // Set initial view based on default
  loadJsonFileList(); // Load file list and potentially the first graph on page load
});
