// === graph.js ===
import * as THREE from 'https://esm.sh/three';
import { setupPanel } from './panel.js';
import { autoSavePositions, setCurrentGraphFile } from './ui.js';
import { getNodeColorScheme } from './theme-manager.js';

export const ARROW_SIZE = 6;
export const ARROW_COLOR = '#ffffff';
export const LINK_WIDTH = 0.5;
export const LINK_COLOR = '#ffffff';

// Add variable to store original data
export let originalGraphData = null;

export const Graph = ForceGraph3D()(document.getElementById('3d-graph'))
  .nodeThreeObject(createUMLNode)
  .nodeLabel(getNodeLabel)
  .linkLabel(getLinkLabel)
  .linkDirectionalArrowLength(ARROW_SIZE)
  .linkDirectionalArrowColor(ARROW_COLOR)
  .linkDirectionalArrowRelPos(1)
  .linkWidth(LINK_WIDTH)
  .linkColor(LINK_COLOR)
  .onNodeDragEnd(node => {
    node.fx = node.x;
    node.fy = node.y;
    node.fz = node.z;
    autoSavePositions();
  });

export function loadGraphData(filename = 'data.json') {
  setCurrentGraphFile(filename);
  originalGraphData = null; // Reset original data on new load

  fetch('/out/' + filename)
    .then(res => res.json())
    .then(data => {
      const baseName = filename.replace(/\.json$/, '');
      const posFile = baseName + '.pos.json';

      fetch('/out/' + posFile)
        .then(posRes => {
          if (!posRes.ok) throw new Error('No position file');
          return posRes.json();
        })
        .then(posData => {
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
        })
        .catch(() => {
          console.warn(`No position file found for ${filename}`);
        })
        .finally(() => {
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
        });
    })
    .catch(err => console.error('Error loading', filename, ':', err));
}

// Update the createUMLNode function to respect current theme
function createUMLNode(node) {
  const canvas = document.createElement('canvas');
  canvas.width = 480;
  canvas.height = 280;
  const ctx = canvas.getContext('2d');
  const marginLeft = 20;
  
  // Get color scheme based on current theme
  const isDarkTheme = document.documentElement.classList.contains('dark');
  const colors = getNodeColorScheme(isDarkTheme);

  ctx.fillStyle = colors.background;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
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
    side: THREE.DoubleSide
  });
  const geometry = new THREE.PlaneGeometry(40, 20);
  return new THREE.Mesh(geometry, material);
}

function getNodeLabel(node) {
  return `
    <div>
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
  return `
    <div>
      ${link.source.id} → ${link.target.id}<br/>
      Relation: ${link.relation}
    </div>`;
}

// Listen for theme changes to update graph node styling
window.addEventListener('themechange', (e) => {
  // If we have graph data loaded, refresh the graph to update node styles
  if (originalGraphData) {
    Graph.refresh(); // This will re-render nodes with new styling
  }
});