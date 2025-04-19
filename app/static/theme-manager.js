/**
 * Theme Manager for KudSight
 * Handles switching between light and dark themes
 */

// Theme constants
export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark'
};

// Get the saved theme from localStorage or use system preference as fallback
export function getInitialTheme() {
  // Check if a theme preference is stored
  const savedTheme = localStorage.getItem('kudSight-theme');
  
  if (savedTheme) {
    return savedTheme;
  }
  
  // Use system preference as fallback
  return window.matchMedia('(prefers-color-scheme: dark)').matches 
    ? THEMES.DARK 
    : THEMES.LIGHT;
}

// Apply a theme by toggling the 'dark' class on the html element
export function applyTheme(theme) {
  if (theme === THEMES.DARK) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
  
  // Store the theme preference
  localStorage.setItem('kudSight-theme', theme);
  
  // Dispatch an event so other components can react to the theme change
  window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
}

// Toggle between light and dark theme
export function toggleTheme() {
  const isDark = document.documentElement.classList.contains('dark');
  const newTheme = isDark ? THEMES.LIGHT : THEMES.DARK;
  applyTheme(newTheme);
  return newTheme;
}

// Initialize theme on page load
export function initTheme() {
  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);
  return initialTheme;
}

// Update node appearance based on current theme (for 3D graph)
export function getNodeColorScheme(isDarkTheme = true) {
  return {
    // White background for nodes in both themes, but with different border colors
    background: '#ffffff',
    
    // Use darker border in light mode for contrast
    stroke: isDarkTheme ? '#000000' : '#333333',
    
    // Text color for the title is black in both themes
    title: '#000000',
    
    // Attribute color is blue (darker blue in light mode for better contrast)
    attribute: isDarkTheme ? '#007bff' : '#0056b3',
    
    // Method color is orange/red (darker in light mode for contrast)
    method: isDarkTheme ? '#e44c1a' : '#c13a10',
    
    // Link/arrow colors - much darker in light mode for visibility
    linkColor: isDarkTheme ? '#ffffff' : '#333333',    // White in dark mode, darker gray in light mode
    arrowColor: isDarkTheme ? '#ffffff' : '#333333',   // White in dark mode, darker gray in light mode
    
    // Graph background color - use a slightly darker background in light mode for better contrast
    bgColor: isDarkTheme ? '#111827' : '#f0f0f0',      // Dark blue in dark mode, light gray in light mode
    
    // 3D Node size (slightly larger in dark mode)
    nodeSize: isDarkTheme ? 40 : 38,
    
    // Node shadow for better visibility against background
    shadowColor: isDarkTheme ? 'rgba(0,0,0,0.8)' : 'rgba(0,0,0,0.2)',
    shadowBlur: isDarkTheme ? 10 : 15
  };
}

// Update UI elements based on theme
export function updateUiForTheme(theme) {
  const isDark = theme === THEMES.DARK;
  
  // Update graph background and visualization
  updateGraphColors(isDark);
}

// Update graph colors based on theme
function updateGraphColors(isDark) {
  if (window.Graph) {
    try {
      // Update graph background color
      const graphElement = document.getElementById('3d-graph');
      if (graphElement) {
        const colors = getNodeColorScheme(isDark);
        
        // Update graph link and arrow colors
        window.Graph
          .linkColor(colors.linkColor)
          .linkDirectionalArrowColor(colors.arrowColor)
          .backgroundColor(colors.bgColor);
        
        // If there's a scene, update the background
        const scene = window.Graph.scene();
        if (scene) {
          scene.background = new THREE.Color(colors.bgColor);
        }
      }
    } catch (e) {
      console.error('Error updating graph colors:', e);
    }
  }
}