export function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggle-sidebar');
    const toggleIcon = document.getElementById('toggle-icon');
    
    if (!sidebar || !toggleBtn) return;

    // Recupera estado anterior do localStorage
    const isCollapsed = localStorage.getItem('genefic-sidebar-collapsed') === 'true';
    if (isCollapsed) {
        sidebar.classList.add('desktop-sidebar--compact');
        toggleIcon.className = 'fa-solid fa-chevron-right';
    }

    const updateLayout = (collapsed) => {
        const appLayout = document.querySelector('.app-layout');
        const isDesktop = window.innerWidth >= 1024;

        if (appLayout) {
            if (isDesktop) {
                appLayout.style.gridTemplateColumns = collapsed ? '80px 1fr' : '240px 1fr';
            } else {
                // No mobile, removemos o estilo inline para deixar o CSS original assumir
                appLayout.style.gridTemplateColumns = '';
            }
        }
        
        if (toggleIcon) {
            toggleIcon.className = collapsed ? 'fa-solid fa-chevron-right' : 'fa-solid fa-chevron-left';
        }
    };

    // Aplica estado inicial e adiciona listener de redimensionamento
    updateLayout(isCollapsed);
    window.addEventListener('resize', () => updateLayout(sidebar.classList.contains('desktop-sidebar--compact')));

    toggleBtn.addEventListener('click', () => {
        const collapsed = sidebar.classList.toggle('desktop-sidebar--compact');
        localStorage.setItem('genefic-sidebar-collapsed', collapsed);
        updateLayout(collapsed);
    });
}
