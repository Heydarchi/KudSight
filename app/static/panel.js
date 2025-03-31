export function setupPanel(graphData) {
    const oldCategorySelect = document.getElementById('categorySelect');
    const itemList = document.getElementById('itemList');
    const itemDetails = document.getElementById('itemDetails');
  
    // ⚠️ Prevent duplicate event listeners by replacing the old select element
    const newCategorySelect = oldCategorySelect.cloneNode(true);
    oldCategorySelect.parentNode.replaceChild(newCategorySelect, oldCategorySelect);
  
    function updateItemList(category) {
      itemList.innerHTML = '';
      itemDetails.innerHTML = 'Select an item to view details.';
  
      const filtered = graphData.nodes.filter(node => node.type === category);
  
      filtered.forEach(node => {
        const li = document.createElement('li');
        li.textContent = node.id;
        li.addEventListener('click', () => showDetails(node));
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
  
    // ✅ Bind event listener to the new <select> element
    newCategorySelect.addEventListener('change', () => {
      updateItemList(newCategorySelect.value);
    });
  
    // ✅ Trigger initial list population
    updateItemList(newCategorySelect.value);
  }
  