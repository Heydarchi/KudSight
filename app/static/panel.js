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

      // --- Start Change: Directly clear state needed for list update ---
      selectedNodeIds.clear(); // Clear the selection set
      clearDetails(); // Clear the details panel display
      // --- End Change ---

      const filtered = graphData.nodes.filter(node => node.type === category);

      filtered.forEach(node => {
        const li = document.createElement('li');
        li.textContent = node.id;
        li.addEventListener('click', (event) => {
            const nodeId = node.id;
            if (selectedNodeIds.has(nodeId)) {
                // Deselect
                selectedNodeIds.delete(nodeId);
                li.classList.remove('active');
                // Clear details if this was the last one selected (optional, can be removed if confusing)
                if (selectedNodeIds.size === 0) {
                    clearDetails();
                }
            } else {
                // Select
                selectedNodeIds.add(nodeId);
                li.classList.add('active');
                // Always show details of the currently clicked item
                showDetails(node);
            }
        });
        itemList.appendChild(li);
      });
    }

    function showDetails(node) {
      itemDetails.innerHTML = `
        <b>ID:</b> ${node.id}<br/>
        <b>Package:</b> ${node.package}<br/>
        <b>Type:</b> ${node.type}<br/>
        ${node.module ? `<b>Module:</b> ${node.module}<br/>` : ''}
        ${node.version ? `<b>Version:</b> ${node.version}<br/>` : ''}
        ${node.attributes?.length ? `<b>Attributes:</b><ul>${node.attributes.map(a => `<li>${a}</li>`).join('')}</ul>` : ''}
        ${node.methods?.length ? `<b>Methods:</b><ul>${node.methods.map(m => `<li>${m}</li>`).join('')}</ul>` : ''}
      `;
    }

    function clearDetails() {
        itemDetails.innerHTML = 'Select an item to view details.';
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

    // Remove 'active' class from all list items
    const activeItems = itemList.querySelectorAll('li.active');
    activeItems.forEach(item => item.classList.remove('active'));

    // Clear the details panel
    if (itemDetails) {
        clearDetails(); // Use the reverted clearDetails function
    }
    console.log("Selection cleared.");
}
