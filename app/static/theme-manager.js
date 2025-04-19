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
    background: isDarkTheme ? '#ffffff' : '#ffffff', // White background in both themes
    stroke: isDarkTheme ? '#000000' : '#000000',     // Black stroke in both themes
    title: isDarkTheme ? '#000000' : '#000000',      // Black title in both themes
    attribute: isDarkTheme ? '#007bff' : '#0056b3',  // Blue attributes (darker in light mode)
    method: isDarkTheme ? '#e44c1a' : '#c13a10'      // Orange methods (darker in light mode)
  };
}

// Update UI elements based on theme
export function updateUiForTheme(theme) {
  // This function could be expanded to handle other theme-dependent UI elements
  const isDark = theme === THEMES.DARK;
  
  // Update form elements styling if needed
  document.querySelectorAll('.form-radio').forEach(radio => {
    radio.style.accentColor = isDark ? '#4f46e5' : '#6366f1';
  });
  
  // Update graph node colors if the graph is initialized
  if (window.Graph) {
    // Implementation would depend on how the graph is initialized
    console.log(`Theme changed to ${theme}, graph should update if visible`);
  }
}