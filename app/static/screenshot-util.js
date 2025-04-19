/**
 * Utility functions for taking screenshots of content
 */

// Take a screenshot of an element and trigger download
export function captureScreenshot(element, filename = 'kudsight-screenshot.png') {
  if (!element) {
    console.error('Element not found for screenshot');
    return;
  }
  
  // Show capture animation
  showCaptureAnimation(element);
  
  // Check if we're in 3D mode by checking the container ID
  const is3DGraph = element.id === 'graph-container';
  
  if (is3DGraph) {
    // For 3D graph, we use the renderer's extract capability
    capture3DGraph(filename);
  } else {
    // For standard content like UML images, use html2canvas
    captureHTMLElement(element, filename);
  }
}

// Show a brief animation to indicate screenshot is being taken
function showCaptureAnimation(element) {
  const flashElement = document.createElement('div');
  flashElement.className = 'screenshot-flash';
  flashElement.style.position = 'absolute';
  flashElement.style.top = '0';
  flashElement.style.left = '0';
  flashElement.style.width = '100%';
  flashElement.style.height = '100%';
  flashElement.style.backgroundColor = 'white';
  flashElement.style.opacity = '0';
  flashElement.style.pointerEvents = 'none';
  flashElement.style.zIndex = '1000';
  flashElement.style.animation = 'screenshot-flash 0.5s ease-out';
  
  // Add animation style if not already added
  if (!document.getElementById('screenshot-flash-style')) {
    const style = document.createElement('style');
    style.id = 'screenshot-flash-style';
    style.textContent = `
      @keyframes screenshot-flash {
        0% { opacity: 0; }
        10% { opacity: 0.3; }
        100% { opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }
  
  element.appendChild(flashElement);
  
  // Remove the flash element after animation
  setTimeout(() => {
    element.removeChild(flashElement);
  }, 500);
}

// Capture a 3D canvas
function capture3DGraph(filename) {
  try {
    // Access the Graph object via window
    if (!window.Graph) {
      console.error('3D Graph not available');
      showScreenshotError('3D Graph not available');
      return;
    }
    
    // Access the renderer directly from the Graph object
    const renderer = window.Graph.renderer();
    
    if (!renderer || !renderer.domElement) {
      console.error('3D renderer not available');
      showScreenshotError('3D renderer not available');
      return;
    }
    
    // Force a render to ensure the most current state is captured
    window.Graph.renderer().render(window.Graph.scene(), window.Graph.camera());
    
    // Capture the canvas content - use preserveDrawingBuffer option if needed
    try {
      const dataURL = renderer.domElement.toDataURL('image/png');
      // Trigger download
      downloadImage(dataURL, filename);
    } catch (err) {
      console.error('Error capturing canvas:', err);
      
      // Fallback to html2canvas if direct canvas capture fails
      const graphElement = document.getElementById('3d-graph');
      if (graphElement) {
        console.log('Falling back to html2canvas for 3D graph');
        captureHTMLElement(graphElement, filename);
      } else {
        showScreenshotError('Failed to capture 3D screenshot');
      }
    }
  } catch (error) {
    console.error('Error capturing 3D screenshot:', error);
    showScreenshotError('Failed to capture 3D screenshot');
  }
}

// Capture a standard HTML element (like UML image)
function captureHTMLElement(element, filename) {
  // Use html2canvas library
  if (!window.html2canvas) {
    // If html2canvas is not loaded, load it dynamically
    loadHTML2Canvas().then(() => {
      processHTMLCapture(element, filename);
    }).catch(error => {
      console.error('Failed to load html2canvas:', error);
      showScreenshotError('Failed to load screenshot library');
    });
  } else {
    processHTMLCapture(element, filename);
  }
}

// Process HTML capture using html2canvas
function processHTMLCapture(element, filename) {
  window.html2canvas(element, {
    backgroundColor: getComputedStyle(element).backgroundColor || '#ffffff',
    scale: 2, // Higher quality
    logging: false,
    useCORS: true,
    allowTaint: true, // Allow tainted canvas
    foreignObjectRendering: true // Try to use foreignObject rendering
  }).then(canvas => {
    try {
      const dataURL = canvas.toDataURL('image/png');
      downloadImage(dataURL, filename);
    } catch (error) {
      console.error('Error processing canvas:', error);
      showScreenshotError('Failed to process screenshot');
    }
  }).catch(error => {
    console.error('html2canvas error:', error);
    showScreenshotError('Failed to capture screenshot');
  });
}

// Dynamically load html2canvas library
function loadHTML2Canvas() {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://html2canvas.hertzen.com/dist/html2canvas.min.js';
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// Trigger download of the image
export function downloadImage(dataURL, filename) {
  const link = document.createElement('a');
  link.href = dataURL;
  link.download = filename;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  
  // Remove the link after download is triggered
  setTimeout(() => {
    document.body.removeChild(link);
    // Show success message
    showScreenshotSuccess();
  }, 100);
}

// Download a file with any content
export function downloadFile(content, filename, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  
  // Clean up
  setTimeout(() => {
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showFileDownloadSuccess(filename);
  }, 100);
}

// Show a success message for screenshot
function showScreenshotSuccess() {
  // Use the toast component from ui-components.js if available
  if (typeof window.showToast === 'function') {
    window.showToast('Screenshot saved', 'success');
  } else {
    alert('Screenshot saved successfully');
  }
}

// Show a success message for file download
function showFileDownloadSuccess(filename) {
  const shortName = filename.length > 25 ? filename.substring(0, 22) + '...' : filename;
  
  // Use the toast component from ui-components.js if available
  if (typeof window.showToast === 'function') {
    window.showToast(`Downloaded ${shortName}`, 'success');
  } else {
    alert(`Downloaded ${filename} successfully`);
  }
}

// Show an error message
function showScreenshotError(message) {
  // Use the toast component from ui-components.js if available
  if (typeof window.showToast === 'function') {
    window.showToast(`Screenshot error: ${message}`, 'error');
  } else {
    alert(`Screenshot error: ${message}`);
  }
}
