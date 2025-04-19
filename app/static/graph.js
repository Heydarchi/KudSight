// === graph.js ===
import * as THREE from 'https://esm.sh/three';
import { setupPanel } from './panel.js';
import { autoSavePositions, setCurrentGraphFile } from './ui.js';
import { getNodeColorScheme, THEMES } from './theme-manager.js';

// Export the Graph object to make it accessible to other modules
export let Graph;

// Add variable to store original data
export let originalGraphData = null;

// Update the createUMLNode function for better contrast in both themes
function createUMLNode(node) {
  const canvas = document.createElement('canvas');
  canvas.width = 480;
  canvas.height = 280;
  const ctx = canvas.getContext('2d');
  const marginLeft = 20;
  
  // Get color scheme based on current theme
  const isDarkTheme = document.documentElement.classList.contains('dark');
  const colors = getNodeColorScheme(isDarkTheme);

  // Set a shadow for better visibility against background
  ctx.shadowColor = colors.shadowColor;
  ctx.shadowBlur = colors.shadowBlur;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 0;
  
  // Fill white background and add contrast border
  ctx.fillStyle = colors.background;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  // Turn off shadow for the stroke
  ctx.shadowBlur = 0;
  ctx.strokeStyle = colors.stroke;
  ctx.lineWidth = 4;
  ctx.strokeRect(0, 0, canvas.width, canvas.height);

  ctx.font = 'bold 24px Arial';
  ctx.fillStyle = colors.title;
  ctx.textAlign = 'center';
  ctx.fillText(node.id, canvas.width / 2, 30);

  ctx.beginPath();
  ctx.moveTo(0, 40);
  ctx.lineTo(canvas.width, 40);
  ctx.stroke();

  let y = 60;
  ctx.textAlign = 'left';

  if (node.type === 'module') {
    ctx.font = '20px Arial';
    ctx.fillStyle = colors.attribute;
    ctx.fillText(`Version: ${node.version || 'N/A'}`, marginLeft, y);
    y += 26;
    ctx.fillText(`Classes: ${(node.classes || []).length}`, marginLeft, y);
  }

  if (node.type === 'class') {
    ctx.font = '20px Arial';
    ctx.fillStyle = colors.attribute;
    if (node.attributes) {
      node.attributes.forEach(attr => {
        ctx.fillText(attr, marginLeft, y);
        y += 26;
      });
    }

    ctx.fillStyle = colors.method;
    if (node.methods) {
      y += 10;
      node.methods.forEach(method => {
        ctx.fillText(method, marginLeft, y);
        y += 26;
      });
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.MeshBasicMaterial({
    map: texture,
    side: THREE.DoubleSide,
    transparent: true // Enable transparency
  });
  
  // Use theme-specific size for nodes
  const nodeSize = colors.nodeSize;
  const aspectRatio = canvas.height / canvas.width;
  const geometry = new THREE.PlaneGeometry(nodeSize, nodeSize * aspectRatio);
  
  return new THREE.Mesh(geometry, material);
}

// Update the initGraph function to ensure renderer is accessible
function initGraph() {
  const isDarkTheme = document.documentElement.classList.contains('dark');
  const colors = getNodeColorScheme(isDarkTheme);

  // Use theme-aware constants
  const ARROW_SIZE = 6;
  const ARROW_COLOR = colors.arrowColor;
  const LINK_WIDTH = isDarkTheme ? 0.5 : 1.0;
  const LINK_COLOR = colors.linkColor;

  // Create the graph instance with theme-aware settings
  Graph = ForceGraph3D({ 
    alpha: true,
    preserveDrawingBuffer: true // Important for screenshots
  })(document.getElementById('3d-graph'))
    .nodeThreeObject(createUMLNode)
    .nodeLabel(getNodeLabel)
    .linkLabel(getLinkLabel)
    .linkDirectionalArrowLength(ARROW_SIZE)
    .linkDirectionalArrowColor(ARROW_COLOR)
    .linkDirectionalArrowRelPos(1)
    .linkWidth(LINK_WIDTH)
    .linkColor(LINK_COLOR)
    .backgroundColor(colors.bgColor)
    .onNodeDragEnd(node => {
      node.fx = node.x;
      node.fy = node.y;
      node.fz = node.z;
      autoSavePositions();
    });

  // Make Graph globally available for other modules
  window.Graph = Graph;
  
  return Graph;
}

export function loadGraphData(filename = 'data.json') {
  // Initialize Graph if not already done
  if (!Graph) {
    initGraph();
  }
  
  setCurrentGraphFile(filename);
  originalGraphData = null; // Reset original data on new load

  fetch('/out/' + filename)
    .then(res => res.json())
    .then(data => {
      const baseName = filename.replace(/\.json$/, '');
      const posFile = baseName + '.pos.json';

      // First check if the position file exists to avoid 404 errors
      fetch('/out/' + posFile, { method: 'HEAD' })
        .then(headRes => {
          if (headRes.ok) {
            // Position file exists, fetch it
            return fetch('/out/' + posFile).then(res => res.json());
          } else {
            // Position file doesn't exist, continue without it
            throw new Error('No position file');
          }
        })
        .then(posData => {
          // Apply saved positions to nodes
          data.nodes.forEach(node => {
            const saved = posData[node.id];
            if (saved) {
              node.x = saved.x;
              node.y = saved.y;
              node.z = saved.z;
              node.fx = saved.x;
              node.fy = saved.y;
              node.fz = saved.z;
            }
          });
          console.log('Applied saved node positions from', posFile);
        })
        .catch((err) => {
          // Suppress 404 error message for pos files since they're optional
          console.log(`No position file found for ${filename}`);
        })
        .finally(() => {
          // Clean up data and prepare graph
          data.links = (data.links || []).filter(link =>
            link &&
            link.source && link.target && link.relation &&
            data.nodes.find(n => n.id === link.source) &&
            data.nodes.find(n => n.id === link.target)
          );
          
          // Store original data
          originalGraphData = data;
          Graph.graphData(data);
          setupPanel(data);
          const categorySelect = document.getElementById('categorySelect');
          if (categorySelect) {
            categorySelect.dispatchEvent(new Event('change'));
          }
          // Make originalGraphData globally available
          window.originalGraphData = originalGraphData;
        });
    })
    .catch(err => console.error('Error loading', filename, ':', err));
}

function getNodeLabel(node) {
  const isDarkTheme = document.documentElement.classList.contains('dark');
  const textColor = isDarkTheme ? 'white' : '#333';
  const bgColor = isDarkTheme ? '#1f2937' : 'white';
  const borderColor = isDarkTheme ? '#374151' : '#d1d5db';
  
  return `
    <div style="background-color: ${bgColor}; color: ${textColor}; padding: 8px; border-radius: 4px; border: 1px solid ${borderColor}; font-family: Arial, sans-serif;">
      <b>${node.package}</b><br/>
      <b>${node.id}</b><br/>
      Type: ${node.type}<br/>
      ${node.methods ? `Methods: ${node.methods.length}<br/>` : ''}
      Lines of Code: ${node.linesOfCode || 'N/A'}<br/>
      ${node.version ? `Version: ${node.version}<br/>` : ''}
      ${node.module ? `Module: ${node.module}<br/>` : ''}
    </div>`;
}

function getLinkLabel(link) {
  const isDarkTheme = document.documentElement.classList.contains('dark');
  const textColor = isDarkTheme ? 'white' : '#333';
  const bgColor = isDarkTheme ? '#1f2937' : 'white';
  const borderColor = isDarkTheme ? '#374151' : '#d1d5db';
  
  return `
    <div style="background-color: ${bgColor}; color: ${textColor}; padding: 8px; border-radius: 4px; border: 1px solid ${borderColor}; font-family: Arial, sans-serif;">
      ${link.source.id} → ${link.target.id}<br/>
      Relation: ${link.relation}
    </div>`;
}

// Listen for theme changes to update graph node styling
window.addEventListener('themechange', (e) => {
  // Theme-manager.js now handles the theme transition logic
  // We can remove the duplicated code here since updateUiForTheme
  // will call preserveCurrentView() which handles all the rendering logic
});

// Initialize graph on page load
document.addEventListener('DOMContentLoaded', () => {
  initGraph();
});