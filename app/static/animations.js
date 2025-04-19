/**
 * UI Animation Utilities for KudSight
 */

// Add subtle entrance animation to elements
export function addEntranceAnimation(element, delay = 0) {
  if (!element) return;
  
  // Set initial state
  element.style.opacity = '0';
  element.style.transform = 'translateY(10px)';
  element.style.transition = `opacity 0.3s ease ${delay}ms, transform 0.3s ease ${delay}ms`;
  
  // Trigger animation in the next frame
  requestAnimationFrame(() => {
    setTimeout(() => {
      element.style.opacity = '1';
      element.style.transform = 'translateY(0)';
    }, 10);
  });
}

// Add ripple effect to button clicks
export function addRippleEffect(button) {
  if (!button) return;
  
  button.addEventListener('click', (e) => {
    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ripple = document.createElement('span');
    ripple.classList.add('ripple-effect');
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    
    button.appendChild(ripple);
    
    setTimeout(() => {
      ripple.remove();
    }, 600);
  });
  
  // Add necessary style for ripple if not already in CSS
  if (!document.querySelector('#ripple-style')) {
    const style = document.createElement('style');
    style.id = 'ripple-style';
    style.textContent = `
      .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background-color: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple 0.6s linear;
        pointer-events: none;
      }
      
      @keyframes ripple {
        to {
          transform: scale(4);
          opacity: 0;
        }
      }
      
      .btn, button:not(.no-ripple) {
        position: relative;
        overflow: hidden;
      }
    `;
    document.head.appendChild(style);
  }
}

// Apply animations to the UI
export function initAnimations() {
  // Add entrance animations to main UI sections with staggered timing
  const sections = [
    document.getElementById('controls'),
    document.getElementById('side-panel'),
    document.getElementById('content-area'),
    document.getElementById('right-panel')
  ];
  
  sections.forEach((section, index) => {
    if (section) {
      addEntranceAnimation(section, index * 100);
    }
  });
  
  // Add ripple effect to all buttons
  document.querySelectorAll('button:not(.no-ripple)').forEach(button => {
    addRippleEffect(button);
  });
}