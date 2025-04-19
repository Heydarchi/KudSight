import { addTailwindClasses, removeTailwindClasses, styleItemList } from './tailwind-helpers.js';

let selectedNodeIds = new Set();

export function setupPanel(graphData) {
    const oldCategorySelect = document.getElementById('categorySelect');
    const itemList = document.getElementById('itemList');
    const itemDetails = document.getElementById('itemDetails');

    // Prevent duplicate event listeners by replacing the old select element
    const newCategorySelect = oldCategorySelect.cloneNode(true);
    oldCategorySelect.parentNode.replaceChild(newCategorySelect, oldCategorySelect);

    function updateItemList(category) {
      itemList.innerHTML = ''; // Clear the list display
      selectedNodeIds.clear(); // Clear the selection set
      clearDetails(); // Clear the details panel display

      // Add rounded corners to the item list container
      styleItemList(itemList);

      const filtered = graphData.nodes.filter(node => node.type === category);

      if (filtered.length === 0) {
        // Add a message when no items are found
        const li = document.createElement('li');
        li.textContent = 'No items found';
        addTailwindClasses(li, 'py-2 px-2 text-gray-400 italic text-center');
        itemList.appendChild(li);
        return;
      }

      filtered.forEach(node => {
        const li = document.createElement('li');
        li.textContent = node.id;
        
        // Use our helper to add Tailwind classes
        addTailwindClasses(li, 'py-1.5 px-2 border-b border-gray-700 cursor-pointer transition-colors hover:bg-gray-700 truncate');
        
        li.addEventListener('click', (event) => {
            const nodeId = node.id;
            if (selectedNodeIds.has(nodeId)) {
                // Deselect
                selectedNodeIds.delete(nodeId);
                li.classList.remove('active');
                removeTailwindClasses(li, 'bg-primary text-white');
                addTailwindClasses(li, 'hover:bg-gray-700');
                // Clear details if this was the last one selected
                if (selectedNodeIds.size === 0) {
                    clearDetails();
                }
            } else {
                // Select
                selectedNodeIds.add(nodeId);
                li.classList.add('active');
                addTailwindClasses(li, 'bg-primary text-white');
                removeTailwindClasses(li, 'hover:bg-gray-700');
                // Always show details of the currently clicked item
                showDetails(node);
            }
        });
        itemList.appendChild(li);
      });
    }

    function showDetails(node) {
      // Improve details display formatting
      itemDetails.innerHTML = `
        <div class="space-y-2">
          <p class="mb-1.5"><span class="font-semibold text-gray-300">ID:</span> ${node.id}</p>
          <p class="mb-1.5"><span class="font-semibold text-gray-300">Package:</span> ${node.package || 'N/A'}</p>
          <p class="mb-1.5"><span class="font-semibold text-gray-300">Type:</span> ${node.type}</p>
          ${node.module ? `<p class="mb-1.5"><span class="font-semibold text-gray-300">Module:</span> ${node.module}</p>` : ''}
          ${node.version ? `<p class="mb-1.5"><span class="font-semibold text-gray-300">Version:</span> ${node.version}</p>` : ''}
          ${node.linesOfCode ? `<p class="mb-1.5"><span class="font-semibold text-gray-300">Lines of Code:</span> ${node.linesOfCode}</p>` : ''}
          ${node.attributes?.length ? `
            <div class="mb-1.5">
              <span class="font-semibold text-gray-300">Attributes:</span>
              <ul class="list-disc pl-5 mt-1 space-y-0.5">
                ${node.attributes.map(a => `<li class="text-sm">${a}</li>`).join('')}
              </ul>
            </div>` : ''}
          ${node.methods?.length ? `
            <div class="mb-1.5">
              <span class="font-semibold text-gray-300">Methods:</span>
              <ul class="list-disc pl-5 mt-1 space-y-0.5">
                ${node.methods.map(m => `<li class="text-sm">${m}</li>`).join('')}
              </ul>
            </div>` : ''}
        </div>
      `;
    }

    function clearDetails() {
        itemDetails.innerHTML = '<div class="text-gray-400 italic">Select an item to view details.</div>';
    }

    // Bind event listener to the new <select> element
    newCategorySelect.addEventListener('change', () => {
      updateItemList(newCategorySelect.value);
    });

    // Trigger initial list population
    updateItemList(newCategorySelect.value);
}

export function getSelectedNodeIds() {
    return Array.from(selectedNodeIds);
}

export function clearSelection() {
    const itemList = document.getElementById('itemList');
    const itemDetails = document.getElementById('itemDetails');

    // Clear the set
    selectedNodeIds.clear();

    // Remove all classes from list items
    const activeItems = itemList.querySelectorAll('li.active');
    activeItems.forEach(item => {
        item.classList.remove('active');
        removeTailwindClasses(item, 'bg-primary text-white');
        addTailwindClasses(item, 'hover:bg-gray-700');
    });

    // Clear the details panel
    if (itemDetails) {
        itemDetails.innerHTML = '<div class="text-gray-400 italic">Select an item to view details.</div>';
    }
}
