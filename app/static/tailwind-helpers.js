/**
 * Tailwind CSS Helper Utilities
 * Functions to help with dynamic class manipulation when using Tailwind
 */

import { THEMES } from './theme-manager.js';

// Adds Tailwind classes to an element
export function addTailwindClasses(element, classes) {
  if (!element) return;
  
  // Split classes string by spaces and add each class
  classes.split(' ').forEach(cls => {
    if (cls.trim()) {
      element.classList.add(cls.trim());
    }
  });
}

// Removes Tailwind classes from an element
export function removeTailwindClasses(element, classes) {
  if (!element) return;
  
  // Split classes string by spaces and remove each class
  classes.split(' ').forEach(cls => {
    if (cls.trim()) {
      element.classList.remove(cls.trim());
    }
  });
}

// Toggle Tailwind classes on an element
export function toggleTailwindClasses(element, classes, force) {
  if (!element) return;
  
  // Split classes string by spaces and toggle each class
  classes.split(' ').forEach(cls => {
    if (cls.trim()) {
      element.classList.toggle(cls.trim(), force);
    }
  });
}

// Apply Tailwind styles to item list elements with theme awareness
export function styleItemList(listElement) {
  if (!listElement) return;
  
  const isDarkTheme = document.documentElement.classList.contains('dark');
  
  // Add base styling to the list container with theme-specific classes
  const borderColor = isDarkTheme ? 'border-gray-700' : 'border-gray-300';
  addTailwindClasses(listElement, `rounded overflow-hidden border ${borderColor}`);
  
  // Style all list items with theme awareness
  const items = listElement.querySelectorAll('li');
  items.forEach(item => {
    const hoverBg = isDarkTheme ? 'hover:bg-gray-700' : 'hover:bg-gray-200';
    const borderB = isDarkTheme ? 'border-gray-700' : 'border-gray-300';
    addTailwindClasses(item, `py-1.5 px-2 border-b ${borderB} last:border-b-0 cursor-pointer transition-colors ${hoverBg}`);
  });
}

// Helper for styling form elements consistently with theme awareness
export function styleFormElements() {
  const isDarkTheme = document.documentElement.classList.contains('dark');
  
  // Style all select dropdowns
  document.querySelectorAll('select').forEach(select => {
    const bg = isDarkTheme ? 'bg-gray-700' : 'bg-gray-100';
    const border = isDarkTheme ? 'border-gray-600' : 'border-gray-300';
    const text = isDarkTheme ? 'text-gray-200' : 'text-gray-800';
    addTailwindClasses(select, `w-full ${bg} border ${border} rounded px-2 py-1.5 ${text}`);
  });
  
  // Style all buttons
  document.querySelectorAll('button:not(.custom-styled)').forEach(button => {
    // Skip if it's the theme toggle button (which has its own styling)
    if (button.id === 'themeToggle') return;
    
    const bg = isDarkTheme ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300';
    const text = isDarkTheme ? 'text-gray-200' : 'text-gray-800';
    addTailwindClasses(button, `${bg} ${text} py-1.5 px-3 rounded transition-colors`);
  });
}

// Listen for theme changes to update styled elements
window.addEventListener('themechange', () => {
  styleItemList(document.getElementById('itemList'));
  styleFormElements();
});
