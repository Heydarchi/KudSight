/**
 * Tailwind CSS Helper Utilities
 * Functions to help with dynamic class manipulation when using Tailwind
 */

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

// Apply Tailwind styles to item list elements
export function styleItemList(listElement) {
  if (!listElement) return;
  
  // Add base styling to the list container
  addTailwindClasses(listElement, 'rounded overflow-hidden border border-gray-700');
  
  // Style all list items
  const items = listElement.querySelectorAll('li');
  items.forEach(item => {
    addTailwindClasses(item, 'py-1.5 px-2 border-b border-gray-700 last:border-b-0 cursor-pointer transition-colors hover:bg-gray-700');
  });
}

// Helper for styling form elements consistently
export function styleFormElements() {
  // Style all select dropdowns
  document.querySelectorAll('select').forEach(select => {
    addTailwindClasses(select, 'w-full bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-gray-200');
  });
  
  // Style all buttons
  document.querySelectorAll('button:not(.custom-styled)').forEach(button => {
    addTailwindClasses(button, 'bg-gray-700 hover:bg-gray-600 text-gray-200 py-1.5 px-3 rounded transition-colors');
  });
}
