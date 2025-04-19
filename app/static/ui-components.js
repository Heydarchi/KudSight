/**
 * UI Components for KudSight
 * Reusable UI components for better user experience
 */

// Create and show a loading spinner
export function showLoadingSpinner(container, text = 'Loading...') {
  if (!container) return;
  
  const spinner = document.createElement('div');
  spinner.id = 'loading-spinner';
  spinner.className = 'flex items-center justify-center space-x-2';
  spinner.innerHTML = `
    <svg class="animate-spin h-5 w-5 text-primary-light dark:text-primary-dark" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
    <span>${text}</span>
  `;
  
  // Clear container and add spinner
  container.innerHTML = '';
  container.appendChild(spinner);
  
  // Return a function to remove the spinner
  return () => {
    if (spinner && spinner.parentNode === container) {
      container.removeChild(spinner);
    }
  };
}

// Create a notification toast
export function showToast(message, type = 'info', duration = 3000) {
  // Create container if it doesn't exist
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
    document.body.appendChild(toastContainer);
  }
  
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `px-4 py-2 rounded shadow-lg transform transition-all duration-300 flex items-center max-w-md`;
  
  // Set styles based on type
  switch (type) {
    case 'success':
      toast.classList.add('bg-green-500', 'text-white');
      break;
    case 'error':
      toast.classList.add('bg-red-500', 'text-white');
      break;
    case 'warning':
      toast.classList.add('bg-yellow-500', 'text-white');
      break;
    default:
      toast.classList.add('bg-blue-500', 'text-white');
  }
  
  // Set content
  toast.innerHTML = `
    <div class="mr-2">
      ${type === 'success' ? '✓' : type === 'error' ? '✕' : type === 'warning' ? '⚠' : 'ℹ'}
    </div>
    <div>${message}</div>
  `;
  
  // Add to container
  toastContainer.appendChild(toast);
  
  // Animate in
  setTimeout(() => {
    toast.classList.add('translate-y-0', 'opacity-100');
  }, 10);
  
  // Remove after duration
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => {
      if (toast.parentNode === toastContainer) {
        toastContainer.removeChild(toast);
      }
      // Remove container if empty
      if (toastContainer.children.length === 0) {
        document.body.removeChild(toastContainer);
      }
    }, 300);
  }, duration);
}

// Make showToast globally available for the screenshot-util.js
window.showToast = showToast;

// Export form validation helper
export function validateForm(form) {
  const errors = [];
  
  // Find all required inputs
  const requiredInputs = form.querySelectorAll('[required]');
  requiredInputs.forEach(input => {
    if (!input.value.trim()) {
      errors.push(`${input.name || 'Field'} is required`);
      input.classList.add('border-red-500');
    } else {
      input.classList.remove('border-red-500');
    }
  });
  
  return {
    valid: errors.length === 0,
    errors
  };
}