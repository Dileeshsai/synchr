/**
 * Dropdown Z-Index Fix
 * Ensures all dropdown menus appear above other content
 */
document.addEventListener('DOMContentLoaded', function() {
    // Fix for Alpine.js dropdowns
    document.addEventListener('alpine:init', () => {
        // Ensure dropdowns have proper z-index when shown
        Alpine.directive('dropdown-fix', (el, { expression }, { effect, evaluateLater }) => {
            effect(() => {
                const isOpen = evaluateLater(expression)();
                if (isOpen) {
                    // Find the dropdown menu and ensure it has high z-index
                    const dropdownMenu = el.querySelector('.oh-dropdown__menu');
                    if (dropdownMenu) {
                        dropdownMenu.style.zIndex = '9999';
                        dropdownMenu.style.position = 'absolute';
                    }
                }
            });
        });
    });

    // Additional fix for all dropdown menus
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                const target = mutation.target;
                if (target.classList.contains('oh-dropdown__menu')) {
                    // Ensure z-index is always 9999
                    if (target.style.zIndex !== '9999') {
                        target.style.zIndex = '9999';
                    }
                }
            }
        });
    });

    // Observe all dropdown menus
    document.querySelectorAll('.oh-dropdown__menu').forEach(menu => {
        observer.observe(menu, { attributes: true, attributeFilter: ['style'] });
    });

    // Fix for dynamically created dropdowns
    const dropdownObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    const dropdownMenus = node.querySelectorAll ? node.querySelectorAll('.oh-dropdown__menu') : [];
                    dropdownMenus.forEach(menu => {
                        menu.style.zIndex = '9999';
                        menu.style.position = 'absolute';
                        observer.observe(menu, { attributes: true, attributeFilter: ['style'] });
                    });
                }
            });
        });
    });

    // Observe the document body for new dropdown menus
    dropdownObserver.observe(document.body, { childList: true, subtree: true });
});

// Additional fix for navbar dropdowns specifically
document.addEventListener('click', function(e) {
    // Check if clicked element is a dropdown trigger
    if (e.target.closest('.oh-dropdown')) {
        const dropdown = e.target.closest('.oh-dropdown');
        const menu = dropdown.querySelector('.oh-dropdown__menu');
        if (menu) {
            menu.style.zIndex = '9999';
            menu.style.position = 'absolute';
        }
    }
});
