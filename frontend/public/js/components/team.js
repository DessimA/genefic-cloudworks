import { TEAM_MEMBERS } from '../team-data.js';

export function renderTeam() {
    const teamGrid = document.querySelector('#team-grid');
    if (!teamGrid) return;

    teamGrid.innerHTML = TEAM_MEMBERS.map(member => {
        const initialsPhoto = `https://ui-avatars.com/api/?name=${encodeURIComponent(member.name)}&background=0052CC&color=fff`;
        
        let profilePhoto = member.image;

        // Fallback para foto do GitHub
        if (!profilePhoto && member.github && member.github !== "#") {
            try {
                const url = new URL(member.github);
                if (url.hostname === "github.com") {
                    const username = url.pathname.replace(/^\/|\/$/g, '');
                    if (username) {
                        profilePhoto = `https://github.com/${username}.png`;
                    }
                }
            } catch (e) {
                console.error("URL do GitHub inválida para:", member.name);
            }
        }

        const finalPhoto = profilePhoto || initialsPhoto;

        return `
            <div class="glass-panel team-card">
                <div class="avatar-wrapper">
                    <img src="${finalPhoto}" 
                         alt="${member.name}" 
                         class="avatar-img"
                         loading="lazy"
                         decoding="async"
                         onerror="this.src='${initialsPhoto}'">
                </div>
                <div class="team-name">${member.name}</div>
                <div class="team-role">${member.role}</div>
                <div class="team-socials">
                    <a href="${member.linkedin}" target="_blank" title="LinkedIn"><i class="fa-brands fa-linkedin-in"></i></a>
                    <a href="${member.github}" target="_blank" title="GitHub"><i class="fa-brands fa-github"></i></a>
                </div>
            </div>
        `;
    }).join('');
}